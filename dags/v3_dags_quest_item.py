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
from custom_module.v3.quest_item_task_func import (
    generate_quest_item_graphql,
    v3_quest_item_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_quest_item_en_list.json"
ko_path = "/opt/airflow/tmp/v3_quest_item_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_quest_item_ja_list.json"

with DAG(
    dag_id="v3_quest_item_map",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="13 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_quest_item():
        item_list_en = get_graphql(generate_quest_item_graphql("en"))
        item_list_ko = get_graphql(generate_quest_item_graphql("ko"))
        item_list_ja = get_graphql(generate_quest_item_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["maps"], f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"]["maps"], f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"]["maps"], f)

        return {"en": en_path, "ko": ko_path, "ja": ja_path}

    def upsert_quest_item(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_quest_item")

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
            v3_quest_item_process(
                item_en_dict[item_id],
                item_ko_dict[item_id],
                item_ja_dict[item_id],
            )
            for item_id in item_ids
        ]

        if not rows:
            return

        sql = """
                insert into items (
                    id, parent_category, category, name_en, name_ko, name_ja, normalized_name, weight, width, height, image
                ) values %s
                on conflict (id) do update set
                    parent_category=excluded.parent_category,
                    category=excluded.category,
                    name_en=excluded.name_en,
                    name_ko=excluded.name_ko,
                    name_ja=excluded.name_ja,
                    normalized_name=excluded.normalized_name,
                    weight=excluded.weight,
                    width=excluded.width,
                    height=excluded.height,
                    image=excluded.image,
                    update_time=now()
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

    fetch_quest_item_task = PythonOperator(
        task_id="fetch_quest_item",
        python_callable=fetch_quest_item,
    )

    upsert_quest_item_task = PythonOperator(
        task_id="upsert_quest_item",
        python_callable=upsert_quest_item,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    fetch_quest_item_task >> upsert_quest_item_task >> remove_json_files_task
