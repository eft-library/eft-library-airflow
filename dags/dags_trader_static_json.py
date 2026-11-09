"""Publish trader JSON after successful trader-offer ingestion."""
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from custom_module.trader_static_json import generate_trader_static_json
from custom_module.trader_snapshot_cleanup import cleanup_trader_snapshots

with DAG(
    dag_id='dags_trader_static_json',
    schedule=None,
    start_date=pendulum.datetime(2026, 11, 3, tz='Asia/Seoul'),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=30),
    default_args={'owner': 'airflow', 'retries': 1, 'retry_delay': timedelta(minutes=5)},
    on_failure_callback=send_dag_failure_email,
    tags=['trader', 'static-json', 'next-public'],
) as dag:
    generate = PythonOperator(
        task_id='generate_trader_static_json',
        python_callable=generate_trader_static_json,
        do_xcom_push=False,
    )
    cleanup = PythonOperator(
        task_id='cleanup_trader_snapshots',
        python_callable=cleanup_trader_snapshots,
        do_xcom_push=False,
    )
    generate >> cleanup

add_failure_watcher(dag)
