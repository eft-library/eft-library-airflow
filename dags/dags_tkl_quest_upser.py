from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_function import read_sql
from custom_module.graphql_function import get_graphql
from custom_module.tkl_quest_function import quest_graphql, process_quest

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_tkl_quest_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="10 0 * * *",
    catchup=False,
) as dag:

    def fetch_quest_list(**kwargs):
        quest_list = get_graphql(quest_graphql)
        return quest_list

    def upsert_quest(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        quest_list = ti.xcom_pull(task_ids="fetch_quest_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_new_quest.sql")
        data_list = quest_list["data"]["tasks"]

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for quest in data_list:
                    cursor.execute(sql, process_quest(quest))
            conn.commit()

    fetch_data = PythonOperator(
        task_id="fetch_quest_list", python_callable=fetch_quest_list
    )

    upsert_quest_task = PythonOperator(
        task_id="upsert_quest",
        python_callable=upsert_quest,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    fetch_data >> [upsert_quest_task]
