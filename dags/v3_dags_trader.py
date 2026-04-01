import json
import pendulum
import os

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import get_current_context
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from psycopg2.extras import execute_values
from airflow.task.trigger_rule import TriggerRule

from custom_module.graphql_func import get_graphql
from custom_module.v3.trader_task_func import (
    generate_trader_graphql,
    v3_trader_process,
    v3_trader_barter_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_trader_en_list.json"
ko_path = "/opt/airflow/tmp/v3_trader_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_trader_ja_list.json"

with DAG(
    dag_id="v3_dags_trader",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="7 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_trader():
        item_list_en = get_graphql(generate_trader_graphql("en"))
        item_list_ko = get_graphql(generate_trader_graphql("ko"))
        item_list_ja = get_graphql(generate_trader_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["traders"], f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"]["traders"], f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"]["traders"], f)

        return {"en": en_path, "ko": ko_path, "ja": ja_path}

    def upsert_trader(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_trader")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}
        item_ko_dict = {item["id"]: item for item in item_ko_list}
        item_ja_dict = {item["id"]: item for item in item_ja_list}

        item_ids = set(item_en_dict) & set(item_ko_dict) & set(item_ja_dict)

        trader_rows = []
        barter_rows = []
        required_rows = []
        reward_rows = []

        for item_id in item_ids:
            item_en = item_en_dict[item_id]
            item_ko = item_ko_dict[item_id]
            item_ja = item_ja_dict[item_id]

            trader_rows.append(v3_trader_process(item_en, item_ko, item_ja))

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
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja,
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
        files = [en_path, ko_path, ja_path]

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

    fetch_trader_task >> upsert_trader_task >> remove_json_files_task
