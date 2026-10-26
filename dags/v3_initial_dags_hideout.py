from custom_module.queries import hideout as sql_queries

import json
import pendulum
import os

from airflow import DAG
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import get_current_context
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from psycopg2.extras import execute_values
from airflow.task.trigger_rule import TriggerRule

from custom_module.tarkov_json_api import get_hideout
from custom_module.hideout_task_func import (
    v3_hideout_master_process,
    v3_hideout_level_process,
    v3_hideout_skill_require_process,
    v3_hideout_trader_require_process,
    v3_hideout_station_require_process,
    v3_hideout_item_require_process,
    v3_hideout_item_require_process,
    v3_hideout_craft_process,
    v3_hideout_bonus_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_initial_hideout_en_list.json"
ko_path = "/opt/airflow/tmp/v3_initial_hideout_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_initial_hideout_ja_list.json"

with DAG(
    on_failure_callback=send_dag_failure_email,
    dag_id="v3_initial_dags_hideout",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule=None,
    tags=["postgresql", "tarkov-dev-api", "initial-load", "manual-only"],
    catchup=False,
) as dag:

    def fetch_hideout():
        item_list_en = get_hideout("en")
        item_list_ko = get_hideout("ko")
        item_list_ja = get_hideout("ja")

        with open(en_path, "w") as f:
            json.dump(item_list_en, f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko, f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja, f)

        return {"en": en_path, "ko": ko_path, "ja": ja_path}

    def upsert_hideout(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_hideout")

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
            item_ko = item_ko_dict[item_id]
            item_ja = item_ja_dict[item_id]

            master_rows.append(v3_hideout_master_process(item_en, item_ko, item_ja))
            level_rows.extend(v3_hideout_level_process(item_en))
            skill_require_rows.extend(
                v3_hideout_skill_require_process(
                    item_en,
                    item_ko,
                    item_ja,
                )
            )
            trader_require_rows.extend(v3_hideout_trader_require_process(item_en))
            station_require_rows.extend(v3_hideout_station_require_process(item_en))
            item_require_rows.extend(v3_hideout_item_require_process(item_en))

            c_rows, r_rows = v3_hideout_craft_process(item_en)
            craft_rows.extend(c_rows)
            require_rows.extend(r_rows)
            bonus_rows.extend(v3_hideout_bonus_process(item_en, item_ko, item_ja))

        if not master_rows:
            return

        master_sql = sql_queries.INITIAL_MASTER_SQL

        level_sql = sql_queries.LEVEL_SQL

        skill_require_sql = sql_queries.INITIAL_SKILL_REQUIRE_SQL

        trader_require_sql = sql_queries.TRADER_REQUIRE_SQL

        station_require_sql = sql_queries.STATION_REQUIRE_SQL

        item_require_sql = sql_queries.ITEM_REQUIRE_SQL

        craft_sql = sql_queries.CRAFT_SQL

        craft_require_item_sql = sql_queries.CRAFT_REQUIRE_ITEM_SQL

        bonus_sql = sql_queries.INITIAL_BONUS_SQL

        postgres_hook = PostgresHook(postgres_conn_id)
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    sql_queries.TRUNCATE_HIDEOUT_LEVELS
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

    fetch_hideout_task = PythonOperator(
        task_id="fetch_hideout",
        python_callable=fetch_hideout,
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

    fetch_hideout_task >> upsert_hideout_task >> remove_json_files_task

add_failure_watcher(dag)
