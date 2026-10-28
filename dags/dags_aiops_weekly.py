"""Aggregate completed daily AIOps reports after the closing day's daily run."""

from datetime import timedelta
from functools import partial

import pendulum
from airflow import DAG
from airflow.timetables.interval import CronDataIntervalTimetable
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.sensors.external_task import ExternalTaskSensor
from airflow.providers.standard.sensors.python import PythonSensor
from custom_module.aiops_api import (
    check_status, daily_dependency_date, submit_report, run_until_completed,
)
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email

with DAG(
    dag_id="dags_aiops_weekly",
    schedule=CronDataIntervalTimetable("0 1 * * 1", timezone="Asia/Seoul"),
    start_date=pendulum.datetime(2026, 10, 28, tz="Asia/Seoul"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=8),
    default_args={"owner": "airflow", "retries": 2, "retry_delay": timedelta(minutes=2)},
    on_failure_callback=send_dag_failure_email,
    tags=["aiops", "weekly"],
) as dag:
    daily_completed = ExternalTaskSensor(
        task_id="wait_for_daily",
        external_dag_id="dags_aiops_daily",
        external_task_id="run_until_completed",
        execution_date_fn=partial(daily_dependency_date, report_type="weekly"),
        allowed_states=["success"],
        failed_states=["failed", "upstream_failed", "skipped"],
        check_existence=True,
        mode="reschedule",
        poke_interval=60,
        timeout=4 * 60 * 60,
        retries=0,
    )
    status = PythonOperator(task_id="check_status", python_callable=check_status)
    report = PythonOperator(
        task_id="submit_report", python_callable=submit_report,
        op_kwargs={"report_type": "weekly"},
    )
    completed = PythonSensor(
        task_id="run_until_completed", python_callable=run_until_completed,
        mode="reschedule", poke_interval=60, timeout=3 * 60 * 60,
        execution_timeout=timedelta(minutes=20), retries=0,
    )
    daily_completed >> status >> report >> completed

add_failure_watcher(dag)
