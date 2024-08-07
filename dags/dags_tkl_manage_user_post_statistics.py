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
    dag_id="dags_tkl_manage_user_post_statistics",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="0 10 * * *",
    tags=['postgresql', "tarkov-dev-api"],
    catchup=False,
) as dag:

    def upsert_user_post_statistics(postgres_conn_id, **kwargs):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_user_post_statistics.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
            conn.commit()

    upsert_user_post_statistics_task = PythonOperator(
        task_id="upsert_user_post_statistics",
        python_callable=upsert_user_post_statistics,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )


    upsert_user_post_statistics_task
