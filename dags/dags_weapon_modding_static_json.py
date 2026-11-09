"""Build firearm modding JSON through the API, then retain three generations."""
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from custom_module.weapon_modding_static_json import publish_weapon_modding_static_json
from custom_module.weapon_modding_snapshot_cleanup import cleanup_weapon_modding_snapshots

with DAG(
    dag_id='dags_weapon_modding_static_json',
    schedule=None,  # Triggered only after successful dags_item ingestion (or manually).
    start_date=pendulum.datetime(2026, 11, 10, tz='Asia/Seoul'),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=3),
    default_args={'owner': 'airflow', 'retries': 1, 'retry_delay': timedelta(minutes=5)},
    on_failure_callback=send_dag_failure_email,
    tags=['weapon', 'modding', 'static-json', 'next-public'],
) as dag:
    generate = PythonOperator(
        task_id='generate_weapon_modding_static_json',
        python_callable=publish_weapon_modding_static_json,
        op_kwargs={'postgres_conn_id': 'platform_db'},
        execution_timeout=timedelta(hours=2),
        do_xcom_push=False,
    )
    cleanup = PythonOperator(
        task_id='cleanup_weapon_modding_snapshots',
        python_callable=cleanup_weapon_modding_snapshots,
        do_xcom_push=False,
    )
    generate >> cleanup

add_failure_watcher(dag)
