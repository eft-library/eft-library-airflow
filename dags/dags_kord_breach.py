"""Fetch season JSON, then transform/upsert source modifiers and clean up."""
import json
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow import DAG
from airflow.sdk import get_current_context
from airflow.task.trigger_rule import TriggerRule
from airflow.providers.standard.operators.python import PythonOperator
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from custom_module.kord_breach import get_season_snapshot, upsert_kord_breach_modifiers

SEASON_PATH = '/opt/airflow/tmp/kord_breach_season.json'

with DAG(
    dag_id='dags_kord_breach',
    schedule='45 2 * * *',
    start_date=pendulum.datetime(2026, 11, 6, tz='Asia/Seoul'),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=15),
    default_args={'owner': 'airflow', 'retries': 2, 'retry_delay': timedelta(minutes=2)},
    on_failure_callback=send_dag_failure_email,
    tags=['kord-breach', 'postgresql', 'tarkov-dev-api'],
) as dag:
    def fetch_kord_breach():
        snapshot = get_season_snapshot()
        path = Path(SEASON_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf-8') as stream:
            json.dump(snapshot, stream, ensure_ascii=False)
        return {'season': str(path)}

    def upsert_kord_breach(postgres_conn_id):
        paths = get_current_context()['ti'].xcom_pull(task_ids='fetch_kord_breach')
        with open(paths['season'], encoding='utf-8') as stream:
            snapshot = json.load(stream)
        upsert_kord_breach_modifiers(snapshot, postgres_conn_id)

    def remove_json_files():
        Path(SEASON_PATH).unlink(missing_ok=True)

    fetch_task = PythonOperator(
        task_id='fetch_kord_breach',
        python_callable=fetch_kord_breach,
        execution_timeout=timedelta(minutes=5),
    )
    upsert_task = PythonOperator(
        task_id='upsert_kord_breach',
        python_callable=upsert_kord_breach,
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
