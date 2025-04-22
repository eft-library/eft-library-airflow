import json
import os

from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_func import read_sql
from custom_module.graphql_func import get_graphql
from custom_module.quest_item_func import (
    generate_quest_item_graphql,
    v2_quest_item_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/quest_item_en_list.json"
ko_path = "/opt/airflow/tmp/quest_item_ko_list.json"
ja_path = "/opt/airflow/tmp/quest_item_ja_list.json"

with DAG(
    dag_id="dags_quest_item_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="10 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_quest_item_list(**kwargs):
        item_list_en = get_graphql(generate_quest_item_graphql("en"))
        item_list_ko = get_graphql(generate_quest_item_graphql("ko"))
        item_list_ja = get_graphql(generate_quest_item_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["questItems"], f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"]["questItems"], f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"]["questItems"], f)

        return {
            "en": en_path,
            "ko": ko_path,
            "ja": ja_path,
        }

    def upsert_quest_item(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_quest_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}
        item_ko_dict = {item["id"]: item for item in item_ko_list}
        item_ja_dict = {item["id"]: item for item in item_ja_list}

        item_ids = (
            set(item_en_dict.keys())
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(
                        sql, v2_quest_item_process(item_en, item_ko, item_ja)
                    )
            conn.commit()

    def remove_json_files(**kwargs):
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

    fetch_data = PythonOperator(
        task_id="fetch_quest_item_list", python_callable=fetch_quest_item_list
    )

    upsert_quest_item_task = PythonOperator(
        task_id="upsert_quest_item",
        python_callable=upsert_quest_item,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        provide_context=True,
    )

    fetch_data >> upsert_quest_item_task >> remove_json_files_task
