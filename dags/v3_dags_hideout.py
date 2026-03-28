import json
import pendulum
import os

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import get_current_context
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from psycopg2.extras import execute_values

from custom_module.graphql_func import get_graphql
from custom_module.v3.hideout_task_func import (
    generate_hideout_graphql,
    v3_hideout_master_process,
    v3_hideout_level_process,
    v3_hideout_skill_require_process,
    v3_hideout_trader_require_process,
    v3_hideout_station_require_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_hideout_en_list.json"
ko_path = "/opt/airflow/tmp/v3_hideout_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_hideout_ja_list.json"

with DAG(
    dag_id="v3_dags_hideout",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="10 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_hideout():
        item_list_en = get_graphql(generate_hideout_graphql("en"))
        item_list_ko = get_graphql(generate_hideout_graphql("ko"))
        item_list_ja = get_graphql(generate_hideout_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["hideoutStations"], f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"]["hideoutStations"], f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"]["hideoutStations"], f)

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

        if not master_rows:
            return

        master_sql = """
            insert into hideout_master (id, name_en, name_ko, name_ja)
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja
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
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja
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

        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
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

    fetch_hideout = PythonOperator(
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
    )

    fetch_hideout >> upsert_hideout_task >> remove_json_files_task
