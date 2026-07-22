import json
import pendulum
import os
from decimal import Decimal
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

from custom_module.tarkov_json_api import get_traders
from custom_module.v3.trader_task_func import (
    v3_trader_process,
    v3_trader_barter_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_trader_en_list.json"

MANUAL_TRADER_IDS = {"FLEA_MARKET"}

with DAG(
    dag_id="v3_dags_trader",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="7 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_trader():
        item_list_en = get_traders("en")

        with open(en_path, "w") as f:
            json.dump(item_list_en, f)

        return {"en": en_path}

    def compare_trader(postgres_conn_id):
        context = get_current_context()
        item_paths = context["ti"].xcom_pull(task_ids="fetch_trader")
        with open(item_paths["en"], "r") as f:
            api_trader_list = json.load(f)

        api_traders = {}
        api_sections = {
            "물물교환": {},
            "요구 아이템": {},
            "보상 아이템": {},
        }
        for trader in api_trader_list:
            trader_row = v3_trader_process(trader, None, None)
            trader_id = trader_row[0]
            api_traders[trader_id] = trader_row

            barter_rows, required_rows, reward_rows = v3_trader_barter_process(
                trader
            )
            barter_owner = {row[0]: row[1] for row in barter_rows}
            for row in barter_rows:
                api_sections["물물교환"][row[0]] = (row[1], tuple(row[1:]))
            for row in required_rows:
                owner_id = barter_owner.get(row[1])
                if owner_id:
                    api_sections["요구 아이템"][row[0]] = (
                        owner_id,
                        tuple(row[1:]),
                    )
            for row in reward_rows:
                owner_id = barter_owner.get(row[1])
                if owner_id:
                    api_sections["보상 아이템"][row[0]] = (
                        owner_id,
                        tuple(row[1:]),
                    )

        db_sections = {name: {} for name in api_sections}
        postgres_hook = PostgresHook(postgres_conn_id)
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    select id, name_en, name_ko, name_ja, image, normalized_name
                    from traders
                    """
                )
                db_traders = {
                    str(row[0]): (str(row[0]), *row[1:])
                    for row in cursor.fetchall()
                }

                cursor.execute(
                    "select id, trader_id, trader_level from trader_barters"
                )
                for row in cursor.fetchall():
                    db_sections["물물교환"][str(row[0])] = (
                        str(row[1]),
                        (str(row[1]), row[2]),
                    )

                item_queries = {
                    "요구 아이템": """
                        select r.id, b.trader_id, r.barter_id, r.item_id, r.quantity
                        from barter_required_items r
                        join trader_barters b on b.id = r.barter_id
                    """,
                    "보상 아이템": """
                        select r.id, b.trader_id, r.barter_id, r.item_id, r.quantity
                        from barter_reward_items r
                        join trader_barters b on b.id = r.barter_id
                    """,
                }
                for section, query in item_queries.items():
                    cursor.execute(query)
                    for row in cursor.fetchall():
                        db_sections[section][str(row[0])] = (
                            str(row[1]),
                            (str(row[2]), str(row[3]), row[4]),
                        )

                cursor.execute("select id, name_en from items")
                item_names = {str(row[0]): row[1] for row in cursor.fetchall()}

        api_ids = set(api_traders)
        db_ids = set(db_traders)
        changes_by_trader = {}

        def trader_name(trader_id):
            api_row = api_traders.get(trader_id)
            db_row = db_traders.get(trader_id)
            return (api_row and api_row[1]) or (db_row and db_row[1]) or trader_id

        def add_change(trader_id, message):
            changes_by_trader.setdefault(
                trader_id,
                {"id": trader_id, "name": trader_name(trader_id), "changes": []},
            )["changes"].append(message)

        for trader_id in sorted(api_ids - db_ids):
            add_change(trader_id, "상인 추가")
        for trader_id in sorted(db_ids - api_ids - MANUAL_TRADER_IDS):
            add_change(trader_id, "상인 삭제")

        field_labels = {
            1: "영문 이름",
            4: "이미지",
            5: "정규화 이름",
        }
        for trader_id in sorted(api_ids & db_ids):
            fields = [
                (
                    f"{label}: {db_traders[trader_id][index]}"
                    f" → {api_traders[trader_id][index]}"
                )
                for index, label in field_labels.items()
                if api_traders[trader_id][index] != db_traders[trader_id][index]
            ]
            if fields:
                add_change(trader_id, f"기본 정보 변경 ({', '.join(fields)})")

        def normalize(value):
            if isinstance(value, Decimal):
                return value.normalize()
            if isinstance(value, float):
                return Decimal(str(value)).normalize()
            if isinstance(value, (tuple, list)):
                return tuple(normalize(item) for item in value)
            return value

        common_ids = api_ids & db_ids
        section_fields = {
            "물물교환": ("상인 ID", "상인 레벨"),
            "보상 아이템": ("물물교환 ID", "아이템 ID", "수량"),
        }

        def format_values(section, values):
            return ", ".join(
                f"{name}={value}"
                for name, value in zip(section_fields[section], values)
            )

        def format_changed_values(section, db_value, api_value):
            return ", ".join(
                f"{name}: {old} → {new}"
                for name, old, new in zip(
                    section_fields[section], db_value, api_value
                )
                if normalize(old) != normalize(new)
            )

        def format_key(section, key, values):
            if section == "보상 아이템":
                item_id = values[1]
                item_name = item_names.get(str(item_id))
                if item_name:
                    return f"{item_name} ({item_id})"
            return str(key)

        for section, api_values in api_sections.items():
            db_values = db_sections[section]

            if section == "요구 아이템":
                api_counts = {}
                db_counts = {}
                for owner_id, _ in api_values.values():
                    if owner_id in common_ids:
                        api_counts[owner_id] = api_counts.get(owner_id, 0) + 1
                for owner_id, _ in db_values.values():
                    if owner_id in common_ids:
                        db_counts[owner_id] = db_counts.get(owner_id, 0) + 1

                for trader_id in sorted(common_ids):
                    api_count = api_counts.get(trader_id, 0)
                    db_count = db_counts.get(trader_id, 0)
                    if api_count != db_count:
                        add_change(
                            trader_id,
                            f"요구 아이템 개수 변경 (DB {db_count}건 → API {api_count}건)",
                        )
                continue

            api_keys = {
                key for key, value in api_values.items() if value[0] in common_ids
            }
            db_keys = {
                key for key, value in db_values.items() if value[0] in common_ids
            }
            counts = {}
            detail_by_trader = {}
            for key in sorted(api_keys - db_keys):
                owner_id = api_values[key][0]
                counts.setdefault(owner_id, [0, 0, 0])[0] += 1
                detail_by_trader.setdefault(owner_id, []).append(
                    f"추가: {format_key(section, key, api_values[key][1])} "
                    f"({format_values(section, api_values[key][1])})"
                )
            for key in sorted(db_keys - api_keys):
                owner_id = db_values[key][0]
                counts.setdefault(owner_id, [0, 0, 0])[1] += 1
                detail_by_trader.setdefault(owner_id, []).append(
                    f"삭제: {format_key(section, key, db_values[key][1])} "
                    f"({format_values(section, db_values[key][1])})"
                )
            for key in sorted(api_keys & db_keys):
                if normalize(api_values[key][1]) != normalize(db_values[key][1]):
                    owner_id = api_values[key][0]
                    counts.setdefault(owner_id, [0, 0, 0])[2] += 1
                    detail_by_trader.setdefault(owner_id, []).append(
                        f"변경: {format_key(section, key, api_values[key][1])} ("
                        f"{format_changed_values(section, db_values[key][1], api_values[key][1])})"
                    )

            for trader_id, (added, deleted, changed) in sorted(counts.items()):
                details = []
                if added:
                    details.append(f"추가 {added}건")
                if deleted:
                    details.append(f"삭제 {deleted}건")
                if changed:
                    details.append(f"변경 {changed}건")
                add_change(trader_id, f"{section} ({', '.join(details)})")
                detail_rows = detail_by_trader.get(trader_id, [])
                for detail in detail_rows[:20]:
                    add_change(trader_id, f"↳ {section} {detail}")
                if len(detail_rows) > 20:
                    add_change(
                        trader_id,
                        f"↳ {section} 외 {len(detail_rows) - 20}건",
                    )

        changes = [
            changes_by_trader[trader_id]
            for trader_id in sorted(changes_by_trader)
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
            "trader_count": len(changes),
            "changes": changes,
            "html_content": (
                f"<h2>Trader API 데이터 변경 내역 ({len(changes)}명)</h2>"
                f"<ul>{''.join(html_items)}</ul>"
            ),
        }

    def choose_email_branch():
        context = get_current_context()
        diff = context["ti"].xcom_pull(task_ids="compare_trader") or {}
        if diff.get("change_count", 0) > 0:
            return "send_change_email"
        return "no_trader_changes"

    def upsert_trader(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_trader")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}

        item_ids = set(item_en_dict)

        trader_rows = []
        barter_rows = []
        required_rows = []
        reward_rows = []

        for item_id in item_ids:
            item_en = item_en_dict[item_id]

            trader_rows.append(v3_trader_process(item_en, None, None))

            b_rows, req_rows, rew_rows = v3_trader_barter_process(item_en)
            barter_rows.extend(b_rows)
            required_rows.extend(req_rows)
            reward_rows.extend(rew_rows)

        if not trader_rows:
            return

        trader_sql = """
            insert into traders (id, name_en, name_ko, name_ja, image, normalized_name)
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                name_en = EXCLUDED.name_en,
                image = EXCLUDED.image,
                normalized_name = EXCLUDED.normalized_name,
                update_time = now()
        """

        barter_sql = """
            insert into trader_barters (
                id,
                trader_id,
                trader_level
            )
            values %s
            on conflict (id) do update
            set
                trader_id = excluded.trader_id,
                trader_level = excluded.trader_level
        """

        barter_required_sql = """
            insert into barter_required_items (
                id,
                barter_id,
                item_id,
                quantity
            )
            values %s
            on conflict (id) do update
            set
                barter_id = excluded.barter_id,
                item_id = excluded.item_id,
                quantity = excluded.quantity
        """

        barter_reward_sql = """
            insert into barter_reward_items (
                id,
                barter_id,
                item_id,
                quantity
            )
            values %s
            on conflict (id) do update
            set
                barter_id = excluded.barter_id,
                item_id = excluded.item_id,
                quantity = excluded.quantity
        """

        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                # 하위 테이블 전체 비우기 (traders 제외)
                cursor.execute("""
                    truncate table
                        trader_barters,
                        barter_required_items,
                        barter_reward_items
                    restart identity cascade;
                """)

                execute_values(
                    cursor,
                    trader_sql,
                    trader_rows,
                    page_size=500,
                )

                if barter_rows:
                    execute_values(cursor, barter_sql, barter_rows, page_size=500)

                if required_rows:
                    execute_values(
                        cursor, barter_required_sql, required_rows, page_size=500
                    )

                if reward_rows:
                    execute_values(
                        cursor, barter_reward_sql, reward_rows, page_size=500
                    )

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

    fetch_trader_task = PythonOperator(
        task_id="fetch_trader",
        python_callable=fetch_trader,
    )

    compare_trader_task = PythonOperator(
        task_id="compare_trader",
        python_callable=compare_trader,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    upsert_trader_task = PythonOperator(
        task_id="upsert_trader",
        python_callable=upsert_trader,
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
        to=["poeynus@gmail.com", "moonjipsa@gmail.com"],
        subject="[EFT Library] Trader API 데이터 변경 감지",
        html_content="{{ ti.xcom_pull(task_ids='compare_trader')['html_content'] }}",
        conn_id="smtp_gmail",
        from_email="poeynus@gmail.com",
    )

    no_trader_changes_task = EmptyOperator(task_id="no_trader_changes")

    fetch_trader_task >> compare_trader_task >> upsert_trader_task
    upsert_trader_task >> remove_json_files_task
    upsert_trader_task >> choose_email_branch_task
    choose_email_branch_task >> [send_change_email_task, no_trader_changes_task]
