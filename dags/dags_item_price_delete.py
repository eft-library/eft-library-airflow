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
    dag_id="dags_item_price_delete",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule="20 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def delete_price(postgres_conn_id):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("delete_item_price.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
            conn.commit()

    delete_price_task = PythonOperator(
        task_id="delete_price",
        python_callable=delete_price,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    delete_price_task
