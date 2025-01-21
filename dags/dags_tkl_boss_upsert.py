from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_function import read_sql
from custom_module.graphql_function import get_graphql
from custom_module.tkl_boss_function import process_boss_spawn, boss_graphql

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_tkl_boss_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="15 0 * * *",
    tags=['postgresql', "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_map_list(**kwargs):
        map_list = get_graphql(boss_graphql)
        return map_list

    def upsert_boss_spawn(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        map_list = ti.xcom_pull(task_ids="fetch_map_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_boss_spawn.sql")
        boss_spawn_data = process_boss_spawn(map_list)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for boss in boss_spawn_data:
                    cursor.execute(sql, (boss['location_spawn_chance_en'], boss['location_spawn_chance_kr'], boss['id']))
            conn.commit()

    fetch_data = PythonOperator(
        task_id="fetch_map_list", python_callable=fetch_map_list
    )

    upsert_boss_spawn_task = PythonOperator(
        task_id="upsert_boss_spawn",
        python_callable=upsert_boss_spawn,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    fetch_data >> [
        upsert_boss_spawn_task,
    ]