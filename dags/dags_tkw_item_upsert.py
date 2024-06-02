from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_function import read_sql
from custom_module.graphql_function import get_graphql
from custom_module.tkw_item_function import (
    check_category,
    process_gun,
    process_knife,
    process_throwable,
    process_head_phone,
    weapon_graphql,
    gun_image_change,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_tkw_item_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="5 0 * * *",
    catchup=False,
) as dag:

    def fetch_weapon_data(**kwargs):
        weapon_data = get_graphql(weapon_graphql)
        return weapon_data

    def upsert_gun(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        weapon_data = ti.xcom_pull(task_ids="fetch_weapon_data")
        postgres_hook = PostgresHook(postgres_conn_id)
        gun_sql = read_sql("upsert_tkw_weapon.sql")
        gun_original_data = check_category(weapon_data["data"]["items"], "Gun")
        gun_image_data = check_category(weapon_data["data"]["items"], "Gun image")
        gun_process_data = gun_image_change(gun_original_data, gun_image_data)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in gun_process_data:
                    cursor.execute(gun_sql, process_gun(item))
            conn.commit()

    def upsert_knife(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        weapon_data = ti.xcom_pull(task_ids="fetch_weapon_data")
        postgres_hook = PostgresHook(postgres_conn_id)
        knife_sql = read_sql("upsert_tkw_knife.sql")
        knife_data_list = check_category(weapon_data["data"]["items"], "Knife")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in knife_data_list:
                    cursor.execute(knife_sql, process_knife(item))
            conn.commit()

    def upsert_throwable(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        weapon_data = ti.xcom_pull(task_ids="fetch_weapon_data")
        postgres_hook = PostgresHook(postgres_conn_id)
        throwable_sql = read_sql("upsert_tkw_throwable.sql")
        throwable_data_list = check_category(
            weapon_data["data"]["items"], "Throwable weapon"
        )

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in throwable_data_list:
                    cursor.execute(throwable_sql, process_throwable(item))
            conn.commit()

    def upsert_head_phone(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        weapon_data = ti.xcom_pull(task_ids="fetch_weapon_data")
        postgres_hook = PostgresHook(postgres_conn_id)
        head_phone_sql = read_sql("upsert_tkw_head_phone.sql")
        head_phone_data_list = check_category(
            weapon_data["data"]["items"], "Headphones"
        )

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in head_phone_data_list:
                    cursor.execute(head_phone_sql, process_head_phone(item))
            conn.commit()

    fetch_data = PythonOperator(
        task_id="fetch_weapon_data", python_callable=fetch_weapon_data
    )

    upsert_gun_task = PythonOperator(
        task_id="upsert_gun",
        python_callable=upsert_gun,
        op_kwargs={"postgres_conn_id": "tkw_db"},
        provide_context=True,
    )

    upsert_knife_task = PythonOperator(
        task_id="upsert_knife",
        python_callable=upsert_knife,
        op_kwargs={"postgres_conn_id": "tkw_db"},
        provide_context=True,
    )

    upsert_throwable_task = PythonOperator(
        task_id="upsert_throwable",
        python_callable=upsert_throwable,
        op_kwargs={"postgres_conn_id": "tkw_db"},
        provide_context=True,
    )

    upsert_head_phone_task = PythonOperator(
        task_id="upsert_head_phone",
        python_callable=upsert_head_phone,
        op_kwargs={"postgres_conn_id": "tkw_db"},
        provide_context=True,
    )

    fetch_data >> [
        upsert_gun_task,
        upsert_knife_task,
        upsert_throwable_task,
        upsert_head_phone_task,
    ]
