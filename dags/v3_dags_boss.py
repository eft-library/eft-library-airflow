import json
import pendulum
import os
from decimal import Decimal, InvalidOperation
from html import escape

from airflow import DAG
from airflow.providers.smtp.operators.smtp import EmailOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import BranchPythonOperator, PythonOperator
from airflow.sdk import get_current_context
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from psycopg2.extras import execute_values
from airflow.task.trigger_rule import TriggerRule

from custom_module.graphql_func import get_graphql
from custom_module.v3.boss_task_func import (
    generate_boss_graphql,
    generate_boss_spawn_graphql,
    v3_boss_process,
    v3_boss_item_process,
    v3_boss_spawn_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_boss_en_list.json"
spawn_path = "/opt/airflow/tmp/v3_boss_spawn_list.json"

with DAG(
    dag_id="v3_dags_boss",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="3 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_boss():
        item_list_en = get_graphql(generate_boss_graphql("en"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["bosses"], f)

        return {"en": en_path}

    def fetch_spawn():
        spawn_data = get_graphql(generate_boss_spawn_graphql())

        with open(spawn_path, "w") as f:
            json.dump(spawn_data["data"]["maps"], f)

        return {"spawn": spawn_path}

    def compare_boss(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        boss_paths = ti.xcom_pull(task_ids="fetch_boss")
        spawn_paths = ti.xcom_pull(task_ids="fetch_spawn")

        with open(boss_paths["en"], "r") as f:
            api_bosses = json.load(f)
        with open(spawn_paths["spawn"], "r") as f:
            api_maps = json.load(f)

        api_boss_by_id = {}
        api_items = {}
        for boss in api_bosses:
            boss_row = v3_boss_process(boss, None, None)
            api_boss_by_id[boss_row[0]] = boss_row
            for boss_id, item_id, quantity in v3_boss_item_process(boss):
                api_items[(boss_id, item_id)] = quantity

        api_spawns = {}
        for map_item in api_maps:
            for boss_id, map_id, spawn_chance in v3_boss_spawn_process(map_item):
                key = (boss_id, map_id)
                api_spawns[key] = max(api_spawns.get(key, spawn_chance), spawn_chance)

        postgres_hook = PostgresHook(postgres_conn_id)
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    select id, name_en, name_ko, name_ja, image, normalized_name,
                           health_total, head_hp, thorax_hp, stomach_hp,
                           left_arm_hp, right_arm_hp, left_leg_hp, right_leg_hp
                    from bosses
                    """
                )
                db_boss_by_id = {
                    str(row[0]): (str(row[0]), *row[1:])
                    for row in cursor.fetchall()
                }

                cursor.execute("select boss_id, item_id, quantity from boss_item")
                db_items = {
                    (str(row[0]), str(row[1])): row[2]
                    for row in cursor.fetchall()
                }

                cursor.execute(
                    "select boss_id, map_id, spawn_chance from boss_spawn"
                )
                db_spawns = {
                    (str(row[0]), str(row[1])): row[2]
                    for row in cursor.fetchall()
                }

        api_ids = set(api_boss_by_id)
        db_ids = set(db_boss_by_id)
        changes_by_boss = {}

        def boss_name(boss_id):
            api_row = api_boss_by_id.get(boss_id)
            db_row = db_boss_by_id.get(boss_id)
            return (api_row and api_row[1]) or (db_row and db_row[1]) or boss_id

        def add_change(boss_id, message):
            changes_by_boss.setdefault(
                boss_id,
                {"id": boss_id, "name": boss_name(boss_id), "changes": []},
            )["changes"].append(message)

        for boss_id in sorted(api_ids - db_ids):
            add_change(boss_id, "보스 추가")
        for boss_id in sorted(db_ids - api_ids):
            add_change(boss_id, "보스 삭제")

        field_labels = {
            1: "영문 이름",
            4: "이미지",
            5: "정규화 이름",
            6: "전체 체력",
            7: "머리 체력",
            8: "흉부 체력",
            9: "복부 체력",
            10: "왼팔 체력",
            11: "오른팔 체력",
            12: "왼쪽 다리 체력",
            13: "오른쪽 다리 체력",
        }
        for boss_id in sorted(api_ids & db_ids):
            fields = [
                label
                for index, label in field_labels.items()
                if api_boss_by_id[boss_id][index] != db_boss_by_id[boss_id][index]
            ]
            if fields:
                add_change(boss_id, f"기본 정보 변경 ({', '.join(fields)})")

        def add_section_changes(section_name, api_values, db_values):
            common_boss_ids = api_ids & db_ids
            api_keys = {key for key in api_values if key[0] in common_boss_ids}
            db_keys = {key for key in db_values if key[0] in common_boss_ids}

            counts = {}
            for boss_id, _ in api_keys - db_keys:
                counts.setdefault(boss_id, [0, 0, 0])[0] += 1
            for boss_id, _ in db_keys - api_keys:
                counts.setdefault(boss_id, [0, 0, 0])[1] += 1
            for key in api_keys & db_keys:
                try:
                    values_changed = Decimal(str(api_values[key])) != Decimal(
                        str(db_values[key])
                    )
                except (InvalidOperation, TypeError, ValueError):
                    values_changed = api_values[key] != db_values[key]
                if values_changed:
                    counts.setdefault(key[0], [0, 0, 0])[2] += 1

            for boss_id, (added, deleted, changed) in sorted(counts.items()):
                details = []
                if added:
                    details.append(f"추가 {added}건")
                if deleted:
                    details.append(f"삭제 {deleted}건")
                if changed:
                    details.append(f"변경 {changed}건")
                add_change(boss_id, f"{section_name} ({', '.join(details)})")

        add_section_changes("소지 아이템", api_items, db_items)
        add_section_changes("출현 정보", api_spawns, db_spawns)

        changes = [changes_by_boss[boss_id] for boss_id in sorted(changes_by_boss)]
        html_items = []
        for change in changes:
            details = "".join(
                f"<li>{escape(message)}</li>" for message in change["changes"]
            )
            html_items.append(
                f'<li><strong>{escape(str(change["name"]))}</strong> '
                f'({escape(str(change["id"]))})<ul>{details}</ul></li>'
            )

        return {
            "change_count": sum(len(change["changes"]) for change in changes),
            "boss_count": len(changes),
            "changes": changes,
            "html_content": (
                f"<h2>Boss API 데이터 변경 내역 ({len(changes)}명)</h2>"
                f"<ul>{''.join(html_items)}</ul>"
            ),
        }

    def choose_email_branch():
        context = get_current_context()
        diff = context["ti"].xcom_pull(task_ids="compare_boss") or {}
        if diff.get("change_count", 0) > 0:
            return "send_change_email"
        return "no_boss_changes"

    def upsert_boss(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_boss")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}

        item_ids = sorted(set(item_en_dict))

        boss_rows = []
        boss_item_rows = []

        for item_id in item_ids:
            item_en = item_en_dict[item_id]

            boss_rows.append(v3_boss_process(item_en, None, None))

            boss_item_rows.extend(v3_boss_item_process(item_en))

        if not boss_rows:
            return

        boss_sql = """
            insert into bosses (
                id, name_en, name_ko, name_ja, image, normalized_name,
                health_total, head_hp, thorax_hp, stomach_hp,
                left_arm_hp, right_arm_hp, left_leg_hp, right_leg_hp
            )
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                name_en = EXCLUDED.name_en,
                image = EXCLUDED.image,
                normalized_name = EXCLUDED.normalized_name,
                health_total = EXCLUDED.health_total,
                head_hp = EXCLUDED.head_hp,
                thorax_hp = EXCLUDED.thorax_hp,
                stomach_hp = EXCLUDED.stomach_hp,
                left_arm_hp = EXCLUDED.left_arm_hp,
                right_arm_hp = EXCLUDED.right_arm_hp,
                left_leg_hp = EXCLUDED.left_leg_hp,
                right_leg_hp = EXCLUDED.right_leg_hp,
                update_time = now()
        """

        boss_item_sql = """
            insert into boss_item (boss_id, item_id, quantity)
            values %s
            ON CONFLICT (boss_id, item_id) DO UPDATE
            SET quantity = EXCLUDED.quantity
        """

        postgres_hook = PostgresHook(postgres_conn_id)
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    truncate table
                        boss_item
                    restart identity cascade;
                """
                )

                execute_values(
                    cursor,
                    boss_sql,
                    boss_rows,
                    page_size=500,
                )

                if boss_item_rows:
                    execute_values(
                        cursor,
                        boss_item_sql,
                        boss_item_rows,
                        page_size=500,
                    )

            conn.commit()

    def upsert_boss_spawn(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_spawn")

        with open(item_paths["spawn"], "r") as f:
            map_list = json.load(f)

        boss_spawn_rows = []

        for map_item in map_list:
            boss_spawn_rows.extend(v3_boss_spawn_process(map_item))

        if not boss_spawn_rows:
            return

        # 전체 한 번 더 dedupe
        dedup_map = {}
        for boss_id, map_id, spawn_chance in boss_spawn_rows:
            key = (boss_id, map_id)
            if key not in dedup_map:
                dedup_map[key] = spawn_chance
            else:
                dedup_map[key] = max(dedup_map[key], spawn_chance)

        boss_spawn_rows = [
            (boss_id, map_id, spawn_chance)
            for (boss_id, map_id), spawn_chance in dedup_map.items()
        ]

        sql = """
            insert into boss_spawn (boss_id, map_id, spawn_chance)
            values %s
            ON CONFLICT (boss_id, map_id) DO UPDATE
            SET spawn_chance = EXCLUDED.spawn_chance
        """

        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    truncate table
                        boss_spawn
                    restart identity cascade;
                    """
                )

                execute_values(
                    cursor,
                    sql,
                    boss_spawn_rows,
                    page_size=500,
                )
            conn.commit()

    def remove_json_files():
        files = [en_path, spawn_path]

        for path in files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted: {path}")
                else:
                    print(f"File not found: {path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")

    fetch_boss_task = PythonOperator(
        task_id="fetch_boss",
        python_callable=fetch_boss,
    )

    compare_boss_task = PythonOperator(
        task_id="compare_boss",
        python_callable=compare_boss,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    upsert_boss_task = PythonOperator(
        task_id="upsert_boss",
        python_callable=upsert_boss,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    fetch_spawn_task = PythonOperator(
        task_id="fetch_spawn",
        python_callable=fetch_spawn,
    )

    upsert_boss_spawn_task = PythonOperator(
        task_id="upsert_boss_spawn",
        python_callable=upsert_boss_spawn,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    choose_email_branch_task = BranchPythonOperator(
        task_id="choose_email_branch",
        python_callable=choose_email_branch,
    )

    send_change_email_task = EmailOperator(
        task_id="send_change_email",
        to=["poeynus@gmail.com"],
        subject="[EFT Library] Boss API 데이터 변경 감지",
        html_content="{{ ti.xcom_pull(task_ids='compare_boss')['html_content'] }}",
        conn_id="smtp_gmail",
        from_email="poeynus@gmail.com",
    )

    no_boss_changes_task = EmptyOperator(task_id="no_boss_changes")

    (
        fetch_boss_task
        >> fetch_spawn_task
        >> compare_boss_task
        >> upsert_boss_task
        >> upsert_boss_spawn_task
    )
    upsert_boss_spawn_task >> remove_json_files_task
    upsert_boss_spawn_task >> choose_email_branch_task
    choose_email_branch_task >> [send_change_email_task, no_boss_changes_task]
