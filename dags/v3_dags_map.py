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
from custom_module.v3.map_task_func import generate_map_graphql, v3_map_process

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_map_en_list.json"
ko_path = "/opt/airflow/tmp/v3_map_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_map_ja_list.json"

with DAG(
    dag_id="v3_dags_map",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="1 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_map():
        item_list_en = get_graphql(generate_map_graphql("en"))
        item_list_ko = get_graphql(generate_map_graphql("ko"))
        item_list_ja = get_graphql(generate_map_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["maps"], f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"]["maps"], f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"]["maps"], f)

        return {"en": en_path, "ko": ko_path, "ja": ja_path}

    def upsert_map(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_map")

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

        rows = [
            v3_map_process(
                item_en_dict[item_id],
                item_ko_dict[item_id],
                item_ja_dict[item_id],
            )
            for item_id in item_ids
        ]

        if not rows:
            return

        sql = """
            INSERT INTO maps (
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
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja
        """

        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                execute_values(
                    cursor,
                    sql,
                    rows,
                    page_size=500,
                )
            conn.commit()

    def remove_json_files():
        files = [
            en_path,
            ko_path,
            ja_path,
        ]

        for path in files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted: {path}")
                else:
                    print(f"File not found: {path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")

    fetch_map_task = PythonOperator(
        task_id="fetch_map",
        python_callable=fetch_map,
    )

    upsert_map_task = PythonOperator(
        task_id="upsert_map",
        python_callable=upsert_map,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
    )

    fetch_map_task >> upsert_map_task >> remove_json_files_task
