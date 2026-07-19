import json
import pendulum
import os
from decimal import Decimal
from html import escape
from uuid import UUID

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
from custom_module.v3.hideout_task_func import (
    generate_hideout_graphql,
    v3_hideout_master_process,
    v3_hideout_level_process,
    v3_hideout_skill_require_process,
    v3_hideout_trader_require_process,
    v3_hideout_station_require_process,
    v3_hideout_item_require_process,
    v3_hideout_craft_process,
    v3_hideout_bonus_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_hideout_en_list.json"

with DAG(
    dag_id="v3_dags_hideout",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="5 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_hideout():
        item_list_en = get_graphql(generate_hideout_graphql("en"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["hideoutStations"], f)

        return {"en": en_path}

    def compare_hideout(postgres_conn_id):
        context = get_current_context()
        item_paths = context["ti"].xcom_pull(task_ids="fetch_hideout")
        with open(item_paths["en"], "r") as f:
            api_stations = json.load(f)

        api_master = {}
        api_sections = {
            "레벨": {},
            "스킬 요구조건": {},
            "상인 요구조건": {},
            "선행 시설": {},
            "필요 아이템": {},
            "제작": {},
            "제작 재료": {},
            "보너스": {},
        }

        def put_rows(target, rows, owner_by_parent=None, parent_index=1, values=None):
            for row in rows:
                owner_id = (
                    owner_by_parent.get(row[parent_index])
                    if owner_by_parent is not None
                    else row[1]
                )
                if owner_id:
                    target[row[0]] = (
                        owner_id,
                        tuple(row[index] for index in (values or range(1, len(row)))),
                    )

        for station in api_stations:
            master_row = v3_hideout_master_process(station, None, None)
            api_master[master_row[0]] = master_row

            level_rows = v3_hideout_level_process(station)
            level_owner = {row[0]: row[1] for row in level_rows}
            put_rows(api_sections["레벨"], level_rows)
            put_rows(
                api_sections["스킬 요구조건"],
                v3_hideout_skill_require_process(station, None, None),
                level_owner,
                values=(1, 2, 3),
            )
            put_rows(
                api_sections["상인 요구조건"],
                v3_hideout_trader_require_process(station),
                level_owner,
            )
            put_rows(
                api_sections["선행 시설"],
                v3_hideout_station_require_process(station),
                level_owner,
            )
            put_rows(
                api_sections["필요 아이템"],
                v3_hideout_item_require_process(station),
                level_owner,
            )
            craft_rows, require_rows = v3_hideout_craft_process(station)
            put_rows(api_sections["제작"], craft_rows, level_owner)
            craft_owner = {
                row[0]: level_owner.get(row[1]) for row in craft_rows
            }
            put_rows(api_sections["제작 재료"], require_rows, craft_owner)
            put_rows(
                api_sections["보너스"],
                v3_hideout_bonus_process(station, None, None),
                level_owner,
                values=(1, 2, 3, 6, 9),
            )

        db_sections = {name: {} for name in api_sections}
        postgres_hook = PostgresHook(postgres_conn_id)
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    "select id, normalized_name, name_en, name_ko, name_ja from hideout_master"
                )
                db_master = {
                    str(row[0]): (str(row[0]), *row[1:])
                    for row in cursor.fetchall()
                }

                section_queries = {
                    "레벨": """
                        select hl.id, hl.master_id,
                               hl.master_id, hl.hideout_level, hl.construction_time
                        from hideout_levels hl
                    """,
                    "스킬 요구조건": """
                        select r.id, hl.master_id,
                               r.hideout_level_id, r.require_level, r.name_en
                        from hideout_skill_require r
                        join hideout_levels hl on hl.id = r.hideout_level_id
                    """,
                    "상인 요구조건": """
                        select r.id, hl.master_id,
                               r.hideout_level_id, r.trader_id, r.trader_level
                        from hideout_trader_require r
                        join hideout_levels hl on hl.id = r.hideout_level_id
                    """,
                    "선행 시설": """
                        select r.id, hl.master_id,
                               r.hideout_level_id, r.require_master_id, r.station_level
                        from hideout_station_require r
                        join hideout_levels hl on hl.id = r.hideout_level_id
                    """,
                    "필요 아이템": """
                        select r.id, hl.master_id,
                               r.hideout_level_id, r.item_id, r.quantity, r.in_raid
                        from hideout_item_require r
                        join hideout_levels hl on hl.id = r.hideout_level_id
                    """,
                    "제작": """
                        select c.id, hl.master_id,
                               c.hideout_level_id, c.reward_item_id, c.duration, c.reward_quantity
                        from hideout_crafts c
                        join hideout_levels hl on hl.id = c.hideout_level_id
                    """,
                    "제작 재료": """
                        select r.id, hl.master_id,
                               r.craft_id, r.item_id, r.quantity
                        from hideout_craft_require_items r
                        join hideout_crafts c on c.id = r.craft_id
                        join hideout_levels hl on hl.id = c.hideout_level_id
                    """,
                    "보너스": """
                        select b.id, hl.master_id,
                               b.hideout_level_id, b.bonus_type, b.name_en,
                               b.skill_name_en, b.bonus_value
                        from hideout_bonus b
                        join hideout_levels hl on hl.id = b.hideout_level_id
                    """,
                }
                for section, query in section_queries.items():
                    cursor.execute(query)
                    db_sections[section] = {
                        str(row[0]): (str(row[1]), tuple(row[2:]))
                        for row in cursor.fetchall()
                    }

        api_ids = set(api_master)
        db_ids = set(db_master)
        changes_by_station = {}

        def station_name(station_id):
            api_row = api_master.get(station_id)
            db_row = db_master.get(station_id)
            return (api_row and api_row[2]) or (db_row and db_row[2]) or station_id

        def add_change(station_id, message):
            changes_by_station.setdefault(
                station_id,
                {"id": station_id, "name": station_name(station_id), "changes": []},
            )["changes"].append(message)

        for station_id in sorted(api_ids - db_ids):
            add_change(station_id, "은신처 시설 추가")
        for station_id in sorted(db_ids - api_ids):
            add_change(station_id, "은신처 시설 삭제")

        master_fields = {1: "정규화 이름", 2: "영문 이름"}
        for station_id in sorted(api_ids & db_ids):
            fields = [
                label
                for index, label in master_fields.items()
                if api_master[station_id][index] != db_master[station_id][index]
            ]
            if fields:
                add_change(station_id, f"기본 정보 변경 ({', '.join(fields)})")

        def normalize(value):
            if isinstance(value, UUID):
                return str(value)
            if isinstance(value, Decimal):
                return value.normalize()
            if isinstance(value, float):
                return Decimal(str(value)).normalize()
            if isinstance(value, (tuple, list)):
                return tuple(normalize(item) for item in value)
            return value

        common_ids = api_ids & db_ids
        for section, api_values in api_sections.items():
            db_values = db_sections[section]
            api_keys = {
                key for key, value in api_values.items() if value[0] in common_ids
            }
            db_keys = {
                key for key, value in db_values.items() if value[0] in common_ids
            }
            counts = {}
            for key in api_keys - db_keys:
                owner_id = api_values[key][0]
                counts.setdefault(owner_id, [0, 0, 0])[0] += 1
            for key in db_keys - api_keys:
                owner_id = db_values[key][0]
                counts.setdefault(owner_id, [0, 0, 0])[1] += 1
            for key in api_keys & db_keys:
                if normalize(api_values[key][1]) != normalize(db_values[key][1]):
                    owner_id = api_values[key][0]
                    counts.setdefault(owner_id, [0, 0, 0])[2] += 1

            for station_id, (added, deleted, changed) in sorted(counts.items()):
                details = []
                if added:
                    details.append(f"추가 {added}건")
                if deleted:
                    details.append(f"삭제 {deleted}건")
                if changed:
                    details.append(f"변경 {changed}건")
                add_change(station_id, f"{section} ({', '.join(details)})")

        changes = [
            changes_by_station[station_id]
            for station_id in sorted(changes_by_station)
        ]
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
            "station_count": len(changes),
            "changes": changes,
            "html_content": (
                f"<h2>Hideout API 데이터 변경 내역 ({len(changes)}개 시설)</h2>"
                f"<ul>{''.join(html_items)}</ul>"
            ),
        }

    def choose_email_branch():
        context = get_current_context()
        diff = context["ti"].xcom_pull(task_ids="compare_hideout") or {}
        if diff.get("change_count", 0) > 0:
            return "send_change_email"
        return "no_hideout_changes"

    def upsert_hideout(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_hideout")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}

        item_ids = set(item_en_dict)

        master_rows = []
        level_rows = []
        skill_require_rows = []
        trader_require_rows = []
        station_require_rows = []
        item_require_rows = []
        craft_rows = []
        require_rows = []
        bonus_rows = []

        for item_id in item_ids:
            item_en = item_en_dict[item_id]

            master_rows.append(v3_hideout_master_process(item_en, None, None))
            level_rows.extend(v3_hideout_level_process(item_en))
            skill_require_rows.extend(
                v3_hideout_skill_require_process(
                    item_en,
                    None,
                    None,
                )
            )
            trader_require_rows.extend(v3_hideout_trader_require_process(item_en))
            station_require_rows.extend(v3_hideout_station_require_process(item_en))
            item_require_rows.extend(v3_hideout_item_require_process(item_en))

            c_rows, r_rows = v3_hideout_craft_process(item_en)
            craft_rows.extend(c_rows)
            require_rows.extend(r_rows)
            bonus_rows.extend(v3_hideout_bonus_process(item_en, None, None))

        if not master_rows:
            return

        master_sql = """
            insert into hideout_master (
                id,
                normalized_name,
                name_en,
                name_ko,
                name_ja
            )
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                normalized_name = EXCLUDED.normalized_name,
                name_en = EXCLUDED.name_en
        """

        level_sql = """
            insert into hideout_levels (id, master_id, hideout_level, construction_time)
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                master_id = EXCLUDED.master_id,
                hideout_level = EXCLUDED.hideout_level,
                construction_time = EXCLUDED.construction_time
        """

        skill_require_sql = """
            insert into hideout_skill_require (
                id,
                hideout_level_id,
                require_level,
                name_en,
                name_ko,
                name_ja
            )
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                hideout_level_id = EXCLUDED.hideout_level_id,
                require_level = EXCLUDED.require_level,
                name_en = EXCLUDED.name_en
        """

        trader_require_sql = """
            insert into hideout_trader_require (id, hideout_level_id, trader_id, trader_level)
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                hideout_level_id = EXCLUDED.hideout_level_id,
                trader_id = EXCLUDED.trader_id,
                trader_level = EXCLUDED.trader_level
        """

        station_require_sql = """
            insert into hideout_station_require (id, hideout_level_id, require_master_id, station_level)
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                hideout_level_id = EXCLUDED.hideout_level_id,
                require_master_id = EXCLUDED.require_master_id,
                station_level = EXCLUDED.station_level
        """

        item_require_sql = """
            insert into hideout_item_require (id, hideout_level_id, item_id, quantity, in_raid)
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                hideout_level_id = EXCLUDED.hideout_level_id,
                item_id = EXCLUDED.item_id,
                quantity = EXCLUDED.quantity,
                in_raid = EXCLUDED.in_raid
        """

        craft_sql = """
            insert into hideout_crafts (
                id,
                hideout_level_id,
                reward_item_id,
                duration,
                reward_quantity
            )
            values %s
            on conflict (id) do update
            set
                hideout_level_id = excluded.hideout_level_id,
                reward_item_id = excluded.reward_item_id,
                duration = excluded.duration,
                reward_quantity = excluded.reward_quantity
        """

        craft_require_item_sql = """
            insert into hideout_craft_require_items (
                id,
                craft_id,
                item_id,
                quantity
            )
            values %s
            on conflict (id) do update
            set
                craft_id = excluded.craft_id,
                item_id = excluded.item_id,
                quantity = excluded.quantity
        """

        bonus_sql = """
            insert into hideout_bonus (
                id,
                hideout_level_id,
                bonus_type,
                name_en,
                name_ko,
                name_ja,
                skill_name_en,
                skill_name_ko,
                skill_name_ja,
                bonus_value
            )
            values %s
            on conflict (id) do update
            set
                hideout_level_id = excluded.hideout_level_id,
                bonus_type = excluded.bonus_type,
                name_en = excluded.name_en,
                skill_name_en = excluded.skill_name_en,
                bonus_value = excluded.bonus_value
        """

        postgres_hook = PostgresHook(postgres_conn_id)
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    select id, name_ko, name_ja
                    from hideout_skill_require
                    """
                )
                existing_skill_names = {
                    row_id: (name_ko, name_ja)
                    for row_id, name_ko, name_ja in cursor.fetchall()
                }
                skill_require_rows = [
                    (
                        row_id,
                        hideout_level_id,
                        require_level,
                        name_en,
                        existing_skill_names.get(row_id, (name_ko, name_ja))[0],
                        existing_skill_names.get(row_id, (name_ko, name_ja))[1],
                    )
                    for row_id, hideout_level_id, require_level, name_en, name_ko, name_ja in skill_require_rows
                ]

                cursor.execute(
                    """
                    select id, name_ko, name_ja, skill_name_ko, skill_name_ja
                    from hideout_bonus
                    """
                )
                existing_bonus_names = {
                    row_id: (name_ko, name_ja, skill_name_ko, skill_name_ja)
                    for row_id, name_ko, name_ja, skill_name_ko, skill_name_ja in cursor.fetchall()
                }
                bonus_rows = [
                    (
                        row_id,
                        hideout_level_id,
                        bonus_type,
                        name_en,
                        existing_bonus_names.get(
                            row_id,
                            (name_ko, name_ja, skill_name_ko, skill_name_ja),
                        )[0],
                        existing_bonus_names.get(
                            row_id,
                            (name_ko, name_ja, skill_name_ko, skill_name_ja),
                        )[1],
                        skill_name_en,
                        existing_bonus_names.get(
                            row_id,
                            (name_ko, name_ja, skill_name_ko, skill_name_ja),
                        )[2],
                        existing_bonus_names.get(
                            row_id,
                            (name_ko, name_ja, skill_name_ko, skill_name_ja),
                        )[3],
                        bonus_value,
                    )
                    for (
                        row_id,
                        hideout_level_id,
                        bonus_type,
                        name_en,
                        name_ko,
                        name_ja,
                        skill_name_en,
                        skill_name_ko,
                        skill_name_ja,
                        bonus_value,
                    ) in bonus_rows
                ]

                cursor.execute(
                    """
                    truncate table
                        hideout_levels,
                        hideout_skill_require,
                        hideout_trader_require,
                        hideout_station_require,
                        hideout_item_require,
                        hideout_crafts,
                        hideout_craft_require_items,
                        hideout_bonus
                    restart identity cascade;
                """
                )

                execute_values(
                    cursor,
                    master_sql,
                    master_rows,
                    page_size=500,
                )

                if level_rows:
                    execute_values(
                        cursor,
                        level_sql,
                        level_rows,
                        page_size=500,
                    )

                if skill_require_rows:
                    execute_values(
                        cursor,
                        skill_require_sql,
                        skill_require_rows,
                        page_size=500,
                    )

                if trader_require_rows:
                    execute_values(
                        cursor,
                        trader_require_sql,
                        trader_require_rows,
                        page_size=500,
                    )

                if station_require_rows:
                    execute_values(
                        cursor,
                        station_require_sql,
                        station_require_rows,
                        page_size=500,
                    )

                if item_require_rows:
                    execute_values(
                        cursor,
                        item_require_sql,
                        item_require_rows,
                        page_size=500,
                    )

                if craft_rows:
                    execute_values(cursor, craft_sql, craft_rows, page_size=500)

                if require_rows:
                    execute_values(
                        cursor, craft_require_item_sql, require_rows, page_size=500
                    )
                if bonus_rows:
                    execute_values(cursor, bonus_sql, bonus_rows, page_size=500)

            conn.commit()

    def remove_json_files():
        files = [en_path]

        for path in files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted: {path}")
                else:
                    print(f"File not found: {path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")

    fetch_hideout_task = PythonOperator(
        task_id="fetch_hideout",
        python_callable=fetch_hideout,
    )

    compare_hideout_task = PythonOperator(
        task_id="compare_hideout",
        python_callable=compare_hideout,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    upsert_hideout_task = PythonOperator(
        task_id="upsert_hideout",
        python_callable=upsert_hideout,
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
        subject="[EFT Library] Hideout API 데이터 변경 감지",
        html_content="{{ ti.xcom_pull(task_ids='compare_hideout')['html_content'] }}",
        conn_id="smtp_gmail",
        from_email="poeynus@gmail.com",
    )

    no_hideout_changes_task = EmptyOperator(task_id="no_hideout_changes")

    fetch_hideout_task >> compare_hideout_task >> upsert_hideout_task
    upsert_hideout_task >> remove_json_files_task
    upsert_hideout_task >> choose_email_branch_task
    choose_email_branch_task >> [send_change_email_task, no_hideout_changes_task]
