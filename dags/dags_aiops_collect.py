"""Collect AIOps logs every five minutes without submitting analysis jobs."""

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.timetables.interval import CronDataIntervalTimetable
from airflow.providers.standard.operators.python import PythonOperator
from custom_module.aiops_api import collect
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email

with DAG(
    dag_id="dags_aiops_collect",
    schedule=CronDataIntervalTimetable("*/5 * * * *", timezone="Asia/Seoul"),
    start_date=pendulum.datetime(2026, 10, 29, tz="Asia/Seoul"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=4),
    default_args={"owner": "airflow", "retries": 1, "retry_delay": timedelta(seconds=30)},
    on_failure_callback=send_dag_failure_email,
    tags=["aiops", "collect"],
) as dag:
    collection = PythonOperator(
        task_id="collect", python_callable=collect,
        execution_timeout=timedelta(minutes=3), do_xcom_push=False,
    )

add_failure_watcher(dag)
