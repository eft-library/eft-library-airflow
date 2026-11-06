"""Maintain KORD BREACH modifiers after the one-time canonical ID migration."""
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from custom_module.kord_breach import sync_kord_breach_modifiers

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
    synchronize = PythonOperator(
        task_id='sync_kord_breach_modifiers',
        python_callable=sync_kord_breach_modifiers,
        op_kwargs={'postgres_conn_id': 'platform_db'},
        execution_timeout=timedelta(minutes=5),
        do_xcom_push=False,
    )

add_failure_watcher(dag)
