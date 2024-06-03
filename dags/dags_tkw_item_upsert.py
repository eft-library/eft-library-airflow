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
    process_head_wear,
    process_armor_vest,
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
        sql = read_sql("upsert_tkw_weapon.sql")
        original_data = check_category(weapon_data["data"]["items"], "Gun")
        image_data = check_category(weapon_data["data"]["items"], "Gun image")
        data_list = gun_image_change(original_data, image_data)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_gun(item))
            conn.commit()

    def upsert_knife(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        weapon_data = ti.xcom_pull(task_ids="fetch_weapon_data")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_knife.sql")
        data_list = check_category(weapon_data["data"]["items"], "Knife")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_knife(item))
            conn.commit()

    def upsert_throwable(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        weapon_data = ti.xcom_pull(task_ids="fetch_weapon_data")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_throwable.sql")
        data_list = check_category(weapon_data["data"]["items"], "Throwable weapon")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_throwable(item))
            conn.commit()

    def upsert_head_phone(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        weapon_data = ti.xcom_pull(task_ids="fetch_weapon_data")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_head_phone.sql")
        data_list = check_category(weapon_data["data"]["items"], "Headphones")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_head_phone(item))
            conn.commit()

    def upsert_head_wear(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        weapon_data = ti.xcom_pull(task_ids="fetch_weapon_data")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_head_wear.sql")
        data_list = check_category(weapon_data["data"]["items"], "Headwear")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_head_wear(item))
            conn.commit()

    def upsert_armor_vest(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        weapon_data = ti.xcom_pull(task_ids="fetch_weapon_data")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_armor_vest.sql")
        data_list = check_category(weapon_data["data"]["items"], "Armor")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_armor_vest(item))
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

    upsert_head_wear_task = PythonOperator(
        task_id="upsert_head_wear",
        python_callable=upsert_head_wear,
        op_kwargs={"postgres_conn_id": "tkw_db"},
        provide_context=True,
    )

    upsert_armor_vest_task = PythonOperator(
        task_id="upsert_armor_vest",
        python_callable=upsert_armor_vest,
        op_kwargs={"postgres_conn_id": "tkw_db"},
        provide_context=True,
    )

    fetch_data >> [
        upsert_gun_task,
        upsert_knife_task,
        upsert_throwable_task,
        upsert_head_phone_task,
        upsert_head_wear_task,
        upsert_armor_vest_task,
    ]
