import os

from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_func import read_sql
from custom_module.graphql_func import get_graphql
from custom_module.boss_func import (
    v2_boss_process,
    generate_boss_graphql,
    generate_boss_spawn_graphql,
    spawn_list_process,
    make_boss_spawn_dict,
)
import json

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/boss_en_list.json"
ko_path = "/opt/airflow/tmp/boss_ko_list.json"
ja_path = "/opt/airflow/tmp/boss_ja_list.json"

spawn_en_path = "/opt/airflow/tmp/boss_spawn_en_list.json"
spawn_ko_path = "/opt/airflow/tmp/boss_spawn_ko_list.json"
spawn_ja_path = "/opt/airflow/tmp/boss_spawn_ja_list.json"

with DAG(
    dag_id="dags_boss_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="15 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_boss_list(**kwargs):
        item_list_en = get_graphql(generate_boss_graphql("en"))
        item_list_ko = get_graphql(generate_boss_graphql("ko"))
        item_list_ja = get_graphql(generate_boss_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["bosses"], f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"]["bosses"], f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"]["bosses"], f)

        return {
            "en": en_path,
            "ko": ko_path,
            "ja": ja_path,
        }

    def upsert_boss(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_boss_list")

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
        sql = read_sql("upsert_boss.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_boss_process(item_en, item_ko, item_ja))
            conn.commit()

    def fetch_boss_spawn_list(**kwargs):
        item_list_en = get_graphql(generate_boss_spawn_graphql("en"))
        item_list_ko = get_graphql(generate_boss_spawn_graphql("ko"))
        item_list_ja = get_graphql(generate_boss_spawn_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["maps"], f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"]["maps"], f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"]["maps"], f)

        return {
            "en": en_path,
            "ko": ko_path,
            "ja": ja_path,
        }

    def upsert_boss_spawn(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_boss_spawn_list")

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
        sql = read_sql("upsert_boss_spawn.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                process_spawn_list = []
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]
                    process_spawn_list.append(
                        spawn_list_process(item_en, item_ko, item_ja)
                    )
                boss_spawn_dict = make_boss_spawn_dict(process_spawn_list)

                for boss_name, spawn_info in boss_spawn_dict.items():
                    cursor.execute(sql, (boss_name, json.dumps(spawn_info)))

            conn.commit()

    def remove_json_files(**kwargs):
        files = [en_path, ko_path, ja_path, spawn_en_path, spawn_ja_path, spawn_ko_path]

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
        task_id="fetch_boss_list", python_callable=fetch_boss_list
    )

    upsert_boss_task = PythonOperator(
        task_id="upsert_boss",
        python_callable=upsert_boss,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    fetch_spawn_data = PythonOperator(
        task_id="fetch_boss_spawn_list", python_callable=fetch_boss_spawn_list
    )

    upsert_boss_spawn_task = PythonOperator(
        task_id="upsert_boss_spawn",
        python_callable=upsert_boss_spawn,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        provide_context=True,
    )

    (
        fetch_data
        >> upsert_boss_task
        >> fetch_spawn_data
        >> upsert_boss_spawn_task
        >> remove_json_files_task
    )
