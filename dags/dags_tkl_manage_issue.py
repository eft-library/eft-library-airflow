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
    dag_id="dags_tkl_manage_issue",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="0 * * * *",
    tags=['postgresql', "tarkov-dev-api"],
    catchup=False,
) as dag:

    def delete_issue(postgres_conn_id, **kwargs):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("delete_issue.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
            conn.commit()

    def delete_not_exist_issue(postgres_conn_id, **kwargs):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("delete_not_exist_issue.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
            conn.commit()

    def upsert_issue(postgres_conn_id, **kwargs):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_issue.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
            conn.commit()

    delete_issue_task = PythonOperator(
        task_id="delete_issue",
        python_callable=delete_issue,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    delete_not_exist_issue_task = PythonOperator(
        task_id="delete_not_exist_issue",
        python_callable=delete_not_exist_issue,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_issue_task = PythonOperator(
        task_id="upsert_issue",
        python_callable=upsert_issue,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    delete_issue_task >> delete_not_exist_issue_task >> upsert_issue_task
