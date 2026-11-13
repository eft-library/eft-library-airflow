"""Manual publication after curated reward SQL is committed. No reward collection."""
from datetime import timedelta
import pendulum
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from custom_module.kord_breach_reward_static_json import generate_kord_breach_reward_static_json
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email

with DAG(
    dag_id='dags_kord_breach_reward_static_json', schedule=None,
    start_date=pendulum.datetime(2026,11,13,tz='Asia/Seoul'), catchup=False,
    max_active_runs=1, dagrun_timeout=timedelta(minutes=5),
    default_args={'owner':'airflow', 'retries':1, 'retry_delay':timedelta(minutes=1)},
    on_failure_callback=send_dag_failure_email,
    tags=['kord-breach','static-json','next-public'],
) as dag:
    PythonOperator(task_id='generate_kord_breach_reward_static_json',
        python_callable=generate_kord_breach_reward_static_json,
        execution_timeout=timedelta(minutes=3), do_xcom_push=False)

add_failure_watcher(dag)
