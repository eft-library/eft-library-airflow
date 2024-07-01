from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_function import read_sql
from custom_module.graphql_function import get_graphql
from custom_module.tkl_hideout_function import hideout_graphql
from custom_module.hideout.master_function import process_master

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_tkl_hideout_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="10 0 * * *",
    tags=['postgresql', "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_hideout_list(**kwargs):
        hideout_list = get_graphql(hideout_graphql)
        return hideout_list

    def upsert_hideout_master(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        hideout_list = ti.xcom_pull(task_ids="fetch_hideout_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_hideout_master.sql")
        data_list = hideout_list["data"]["hideoutStations"]

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for hideout in data_list:
                    cursor.execute(sql, process_master(hideout))
            conn.commit()

    fetch_data = PythonOperator(
        task_id="fetch_hideout_list", python_callable=fetch_hideout_list
    )

    upsert_hideout_master_task = PythonOperator(
        task_id="upsert_hideout_master",
        python_callable=upsert_hideout_master,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    fetch_data >> [upsert_hideout_master_task]