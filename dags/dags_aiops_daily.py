"""Collect host logs and finish the previous day's AIOps report over HTTP."""

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.sensors.python import PythonSensor
from custom_module.aiops_api import check_status, collect, submit_daily, run_until_completed
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email

with DAG(
    dag_id="dags_aiops_daily",
    schedule="0 1 * * *",
    start_date=pendulum.datetime(2026, 10, 28, tz="Asia/Seoul"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=4),
    default_args={"owner": "airflow", "retries": 2, "retry_delay": timedelta(minutes=2)},
    on_failure_callback=send_dag_failure_email,
    tags=["aiops", "daily"],
) as dag:
    status = PythonOperator(task_id="check_status", python_callable=check_status)
    collection = PythonOperator(task_id="collect", python_callable=collect)
    report = PythonOperator(task_id="submit_report", python_callable=submit_daily)
    completed = PythonSensor(
        task_id="run_until_completed",
        python_callable=run_until_completed,
        mode="reschedule",
        poke_interval=60,
        timeout=3 * 60 * 60,
        execution_timeout=timedelta(minutes=20),
        retries=0,
    )
    status >> collection >> report >> completed

add_failure_watcher(dag)
