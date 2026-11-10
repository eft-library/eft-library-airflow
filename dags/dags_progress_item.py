"""Fetch checklist source JSON, transform/upsert it, then request static JSON."""
import json
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow import DAG
from airflow.sdk import get_current_context
from airflow.task.trigger_rule import TriggerRule
from airflow.providers.standard.operators.python import PythonOperator
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from custom_module.tarkov_json_api import get_json_data
from custom_module.progress_items import upsert_progress_items

TASKS_PATH = '/opt/airflow/tmp/progress_item_tasks.json'

with DAG(
    dag_id='dags_progress_item',
    schedule='55 2 * * *',
    start_date=pendulum.datetime(2026, 11, 6, tz='Asia/Seoul'),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=15),
    default_args={'owner': 'airflow', 'retries': 2, 'retry_delay': timedelta(minutes=2)},
    on_failure_callback=send_dag_failure_email,
    tags=['progress', 'postgresql', 'tarkov-dev-api'],
) as dag:
    def fetch_progress_item():
        data = get_json_data('tasks', None, 'regular')
        path = Path(TASKS_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False)
        return {'tasks': str(path)}

    def upsert_progress_item(postgres_conn_id):
        paths = get_current_context()['ti'].xcom_pull(task_ids='fetch_progress_item')
        with open(paths['tasks'], encoding='utf-8') as stream:
            data = json.load(stream)
        upsert_progress_items(data, postgres_conn_id)

    def remove_json_files():
        Path(TASKS_PATH).unlink(missing_ok=True)

    fetch_task = PythonOperator(
        task_id='fetch_progress_item',
        python_callable=fetch_progress_item,
        execution_timeout=timedelta(minutes=5),
    )
    upsert_task = PythonOperator(
        task_id='upsert_progress_item',
        python_callable=upsert_progress_item,
        op_kwargs={'postgres_conn_id': 'platform_db'},
        execution_timeout=timedelta(minutes=5),
        do_xcom_push=False,
    )
    cleanup_task = PythonOperator(
        task_id='remove_json_files',
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )
    fetch_task >> upsert_task >> cleanup_task

add_failure_watcher(dag)
