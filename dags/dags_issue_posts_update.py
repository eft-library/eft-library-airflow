from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_func import read_sql

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_issue_posts_update",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule="0 * * * *",
    tags=["postgresql"],
    catchup=False,
) as dag:

    def delete_issue_posts(postgres_conn_id):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("delete_issue_posts.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
            conn.commit()

    def update_issue_posts(postgres_conn_id):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("update_issue_posts.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
            conn.commit()

    update_issue_posts_task = PythonOperator(
        task_id="update_issue_posts",
        python_callable=update_issue_posts,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    delete_issue_posts_task = PythonOperator(
        task_id="delete_issue_posts",
        python_callable=delete_issue_posts,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    delete_issue_posts_task >> update_issue_posts_task
