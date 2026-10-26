from custom_module.queries import autocomplete as sql_queries

from contextlib import closing

import pendulum
from airflow import DAG
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.standard.operators.python import PythonOperator


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}


AUTOCOMPLETE_SQL = sql_queries.AUTOCOMPLETE_SQL


with DAG(
    on_failure_callback=send_dag_failure_email,
    dag_id="v3_dags_autocomplete",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="17 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def update_autocomplete(postgres_conn_id):
        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(AUTOCOMPLETE_SQL)
            conn.commit()

    update_autocomplete_task = PythonOperator(
        task_id="update_autocomplete",
        python_callable=update_autocomplete,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    update_autocomplete_task

add_failure_watcher(dag)
