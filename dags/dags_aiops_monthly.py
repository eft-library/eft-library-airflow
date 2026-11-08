"""Aggregate completed daily AIOps reports after the closing day's daily investigation."""

from datetime import timedelta
from functools import partial

import pendulum
from airflow import DAG
from airflow.timetables.interval import CronDataIntervalTimetable
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.sensors.external_task import ExternalTaskSensor
from airflow.providers.standard.sensors.python import PythonSensor
from custom_module.aiops_api import (
    check_status, daily_dependency_date, weekly_dependency_date, submit_report, run_until_completed,
)
from custom_module.aiops_sensors import MonthlyWeeklyReportSensor
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email

with DAG(
    dag_id="dags_aiops_monthly",
    schedule=CronDataIntervalTimetable("0 3 1 * *", timezone="Asia/Seoul"),
    start_date=pendulum.datetime(2026, 10, 28, tz="Asia/Seoul"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=24),
    default_args={"owner": "airflow", "retries": 2, "retry_delay": timedelta(minutes=2)},
    on_failure_callback=send_dag_failure_email,
    tags=["aiops", "monthly"],
) as dag:
    daily_completed = ExternalTaskSensor(
        task_id="wait_for_daily",
        external_dag_id="dags_aiops_daily",
        external_task_id="run_investigation_until_completed",
        execution_date_fn=partial(daily_dependency_date, report_type="monthly"),
        allowed_states=["success"],
        failed_states=["failed", "upstream_failed", "skipped"],
        check_existence=True,
        mode="reschedule",
        poke_interval=60,
        timeout=8 * 60 * 60,
        retries=0,
    )
    weekly_completed = MonthlyWeeklyReportSensor(
        task_id="wait_for_weekly",
        external_dag_id="dags_aiops_weekly",
        external_task_id="run_until_completed",
        execution_date_fn=weekly_dependency_date,
        allowed_states=["success"],
        failed_states=["failed", "upstream_failed", "skipped"],
        check_existence=True,
        mode="reschedule",
        poke_interval=60,
        timeout=12 * 60 * 60,
        retries=0,
    )
    status = PythonOperator(task_id="check_status", python_callable=check_status)
    report = PythonOperator(
        task_id="submit_report", python_callable=submit_report,
        pool="aiops_ingestion", pool_slots=1,
        op_kwargs={"report_type": "monthly"},
    )
    completed = PythonSensor(
        task_id="run_until_completed", python_callable=run_until_completed,
        mode="reschedule", poke_interval=60, timeout=3 * 60 * 60,
        execution_timeout=timedelta(minutes=20), retries=0,
    )
    daily_completed >> weekly_completed >> status >> report >> completed

add_failure_watcher(dag)
