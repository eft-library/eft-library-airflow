from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_function import read_sql

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_tkl_search_update",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="15 0 * * *",
    tags=['postgresql', "tarkov-dev-api"],
    catchup=False,
) as dag:

    def truncate_search(postgres_conn_id, **kwargs):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("truncate_tkl_search.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
            conn.commit()

    def insert_search(postgres_conn_id, **kwargs):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("update_tkl_search.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
            conn.commit()

    truncate_search_task = PythonOperator(
        task_id="truncate_search",
        python_callable=truncate_search,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    insert_search_task = PythonOperator(
        task_id="insert_search",
        python_callable=insert_search,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    truncate_search_task >> insert_search_task
