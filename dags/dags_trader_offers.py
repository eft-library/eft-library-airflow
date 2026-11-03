"""Collect complete purchase/barter snapshots and source restock times."""
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from custom_module.trader_offers import collect_trader_offers

with DAG(
    dag_id='dags_trader_offers',
    schedule='*/5 * * * *',
    start_date=pendulum.datetime(2026, 11, 3, tz='Asia/Seoul'),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=20),
    default_args={'owner': 'airflow', 'retries': 2, 'retry_delay': timedelta(minutes=5)},
    on_failure_callback=send_dag_failure_email,
    tags=['trader', 'postgresql', 'tarkov-dev-api'],
) as dag:
    collect = PythonOperator(
        task_id='collect_trader_offers',
        python_callable=collect_trader_offers,
        op_kwargs={'postgres_conn_id': 'platform_db'},
        do_xcom_push=False,
        execution_timeout=timedelta(minutes=10),
    )

    publish = TriggerDagRunOperator(
        task_id='generate_trader_static_json',
        trigger_dag_id='dags_trader_static_json',
    )
    collect >> publish

add_failure_watcher(dag)
