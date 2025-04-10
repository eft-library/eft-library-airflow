from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_function import read_sql
from custom_module.graphql_function import get_graphql
from custom_module.trader_function import trader_graphql, process_trader

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_tkl_trader_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="15 0 * * *",
    tags=['postgresql', "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_trader_list(**kwargs):
        trader_list = get_graphql(trader_graphql)
        return trader_list

    def upsert_trader(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        quest_list = ti.xcom_pull(task_ids="fetch_trader_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_trader.sql")
        data_list = quest_list["data"]["traders"]

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for trader in data_list:
                    cursor.execute(sql, process_trader(trader))
            conn.commit()

    fetch_data = PythonOperator(
        task_id="fetch_trader_list", python_callable=fetch_trader_list
    )

    upsert_trader_task = PythonOperator(
        task_id="upsert_trader",
        python_callable=upsert_trader,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    fetch_data >> [upsert_trader_task]