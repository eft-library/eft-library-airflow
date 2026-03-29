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
from custom_module.v3.item_task_func import generate_item_graphql

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_item_en_list.json"
ko_path = "/opt/airflow/tmp/v3_item_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_item_ja_list.json"

with DAG(
    dag_id="v3_dags_item",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="11 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_boss():
        item_list_en = get_graphql(generate_item_graphql("en"))
        item_list_ko = get_graphql(generate_item_graphql("ko"))
        item_list_ja = get_graphql(generate_item_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["bosses"], f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"]["bosses"], f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"]["bosses"], f)

        return {"en": en_path, "ko": ko_path, "ja": ja_path}
