"""Refresh Kappa/Rebirth item candidates, then request static JSON publication."""
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from custom_module.progress_items import sync_progress_items

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
    synchronize = PythonOperator(
        task_id='sync_progress_items',
        python_callable=sync_progress_items,
        op_kwargs={'postgres_conn_id': 'platform_db'},
        execution_timeout=timedelta(minutes=5),
        do_xcom_push=False,
    )
    publish = TriggerDagRunOperator(
        task_id='generate_progress_static_json',
        trigger_dag_id='dags_progress_static_json',
    )
    synchronize >> publish

add_failure_watcher(dag)
