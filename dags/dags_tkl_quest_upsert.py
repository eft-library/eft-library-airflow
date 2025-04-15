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
    tags=['postgresql', "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_quest_list(**kwargs):
        quest_list = get_graphql(quest_graphql)
        return quest_list

    def upsert_quest(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        quest_list = ti.xcom_pull(task_ids="fetch_quest_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_api_quest.sql")
        data_list = quest_list["data"]["tasks"]
        no_insert = ["5e381b0286f77420e3417a74", "6744a728352b4da8e003eda9", "6615141bfda04449120269a7", "6745cbee909d2013670a4a55", "66151401efb0539ae10875ae", "5e4d515e86f77438b2195244", "6391d9144b15ca31f76bc323", "6391d912f8e5dd32bf4e3ab2", "5e4d4ac186f774264f758336"]
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for quest in data_list:
                    if quest.get("id") not in no_insert:
                        cursor.execute(sql, process_quest(quest))
            conn.commit()

    def update_quest_url_mapping(postgres_conn_id, **kwargs):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("update_quest_url_mapping.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
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

    update_quest_url_mapping_task = PythonOperator(
        task_id="update_quest_url_mapping",
        python_callable=update_quest_url_mapping,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    fetch_data >> upsert_quest_task >> update_quest_url_mapping_task
