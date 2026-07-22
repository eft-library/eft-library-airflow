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

from custom_module.tarkov_json_api import get_quest_items
from custom_module.v3.quest_item_task_func import (
    v3_quest_item_process,
)
from custom_module.v3.item_task_func import assign_unique_normalized_names

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_quest_item_en_list.json"

with DAG(
    dag_id="v3_dags_quest_item",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="13 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_quest_item():
        item_list_en = get_quest_items("en")

        with open(en_path, "w") as f:
            json.dump(item_list_en, f)

        return {"en": en_path}

    def upsert_quest_item(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_quest_item")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}

        item_ids = set(item_en_dict)

        rows = [
            v3_quest_item_process(
                item_en_dict[item_id],
                None,
                None,
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
                cursor.execute(
                    "select id, normalized_name from items where normalized_name is not null"
                )
                existing_normalized_names_by_id = dict(cursor.fetchall())
                rows = assign_unique_normalized_names(
                    rows, existing_normalized_names_by_id
                )

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
