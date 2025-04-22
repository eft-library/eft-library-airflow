import json
import os
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_func import read_sql
from custom_module.graphql_func import get_graphql
from custom_module.trader_func import generate_trader_graphql, v2_trader_process

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/mnt/ramdisk/trader_en_list.json"
ko_path = "/mnt/ramdisk/trader_ko_list.json"
ja_path = "/mnt/ramdisk/trader_ja_list.json"

with DAG(
    dag_id="dags_trader_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="15 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_trader_list(**kwargs):
        trader_en_list = get_graphql(generate_trader_graphql("en"))
        trader_ko_list = get_graphql(generate_trader_graphql("ko"))
        trader_ja_list = get_graphql(generate_trader_graphql("ja"))
        print("EN list sample:", trader_en_list[:1])
        print("Directory exists?", os.path.exists("/mnt/ramdisk/"))
        try:
            json.dumps(trader_en_list)
        except Exception as e:
            print("❌ json serialization error:", e)

        with open(en_path, "w") as f:
            json.dump(trader_en_list, f)
        with open(ko_path, "w") as f:
            json.dump(trader_ko_list, f)
        with open(ja_path, "w") as f:
            json.dump(trader_ja_list, f)

        return {
            "en": en_path,
            "ko": ko_path,
            "ja": ja_path,
        }

    def upsert_trader(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        trader_paths = ti.xcom_pull(task_ids="fetch_trader_list")

        with open(trader_paths["en"], "r") as f:
            trader_en_list = json.load(f)
        with open(trader_paths["ko"], "r") as f:
            trader_ko_list = json.load(f)
        with open(trader_paths["ja"], "r") as f:
            trader_ja_list = json.load(f)

        trader_en_data = trader_en_list["data"]["trader"]
        trader_ko_data = trader_ko_list["data"]["trader"]
        trader_ja_data = trader_ja_list["data"]["trader"]

        trader_en_dict = {item["id"]: item for item in trader_en_data}
        trader_ko_dict = {item["id"]: item for item in trader_ko_data}
        trader_ja_dict = {item["id"]: item for item in trader_ja_data}

        trader_ids = (
            set(trader_en_dict.keys())
            & set(trader_ko_dict.keys())
            & set(trader_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_trader.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for trader_id in trader_ids:
                    trader_en = trader_en_dict[trader_id]
                    trader_ko = trader_ko_dict[trader_id]
                    trader_ja = trader_ja_dict[trader_id]

                    cursor.execute(
                        sql, v2_trader_process(trader_en, trader_ko, trader_ja)
                    )
            conn.commit()

    def remove_trader_json_files(**kwargs):
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
        task_id="fetch_trader_list", python_callable=fetch_trader_list
    )

    upsert_trader_task = PythonOperator(
        task_id="upsert_trader",
        python_callable=upsert_trader,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    remove_trader_json_files_task = PythonOperator(
        task_id="remove_trader_json_files",
        python_callable=remove_trader_json_files,
        provide_context=True,
    )

    fetch_data >> upsert_trader_task >> remove_trader_json_files_task
