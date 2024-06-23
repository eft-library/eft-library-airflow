from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_function import read_sql
from custom_module.graphql_function import get_graphql
from custom_module.tkw_item_function import check_category, weapon_graphql
from custom_module.item.knife_function import process_knife
from custom_module.item.throwable_function import process_throwable
from custom_module.item.rig_function import process_rig
from custom_module.item.armor_vest_function import process_armor_vest
from custom_module.item.head_wear_function import process_head_wear
from custom_module.item.head_phone_function import process_head_phone
from custom_module.item.gun_function import process_gun, gun_image_change
from custom_module.item.backpack_function import process_backpack
from custom_module.item.container_function import process_container
from custom_module.item.key_function import process_key, process_key_map
from custom_module.item.food_drink_function import process_food_drink
from custom_module.item.medical_function import process_medical
from custom_module.item.ammo_function import process_ammo

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

    def fetch_item_list(**kwargs):
        item_list = get_graphql(weapon_graphql)
        return item_list

    def upsert_gun(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_weapon.sql")
        original_data = check_category(item_list["data"]["items"], "Gun")
        image_data = check_category(item_list["data"]["items"], "Gun image")
        data_list = gun_image_change(original_data, image_data)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_gun(item))
            conn.commit()

    def upsert_knife(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_knife.sql")
        data_list = check_category(item_list["data"]["items"], "Knife")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_knife(item))
            conn.commit()

    def upsert_throwable(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_throwable.sql")
        data_list = check_category(item_list["data"]["items"], "Throwable weapon")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_throwable(item))
            conn.commit()

    def upsert_head_phone(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_head_phone.sql")
        data_list = check_category(item_list["data"]["items"], "Headphones")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_head_phone(item))
            conn.commit()

    def upsert_head_wear(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_head_wear.sql")
        data_list = check_category(item_list["data"]["items"], "Headwear")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_head_wear(item))
            conn.commit()

    def upsert_armor_vest(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_armor_vest.sql")
        data_list = check_category(item_list["data"]["items"], "Armor")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_armor_vest(item))
            conn.commit()

    def upsert_backpack(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_backpack.sql")
        data_list = check_category(item_list["data"]["items"], "Backpack")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_backpack(item))
            conn.commit()

    def upsert_container(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_container.sql")
        data_list = check_category(item_list["data"]["items"], "Common container")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_container(item))
            conn.commit()

    def upsert_key(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_key.sql")
        data_list = check_category(item_list["data"]["items"], "Key")
        key_map = process_key_map(item_list["data"]["maps"])

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_key(item, key_map))
            conn.commit()

    def upsert_rig(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_rig.sql")
        data_list = check_category(item_list["data"]["items"], "Chest rig")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_rig(item))
            conn.commit()

    def upsert_food_drink(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_food_drink.sql")
        data_list = check_category(item_list["data"]["items"], "Food Drink")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_food_drink(item))
            conn.commit()

    def upsert_medical(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_medical.sql")
        data_list = check_category(item_list["data"]["items"], "Meds")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_medical(item))
            conn.commit()

    def upsert_ammo(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkw_ammo.sql")
        data_list = check_category(item_list["data"]["items"], "Ammo")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_ammo(item))
            conn.commit()

    fetch_data = PythonOperator(
        task_id="fetch_item_list", python_callable=fetch_item_list
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

    upsert_rig_task = PythonOperator(
        task_id="upsert_rig",
        python_callable=upsert_rig,
        op_kwargs={"postgres_conn_id": "tkw_db"},
        provide_context=True,
    )

    upsert_backpack_task = PythonOperator(
        task_id="upsert_backpack",
        python_callable=upsert_backpack,
        op_kwargs={"postgres_conn_id": "tkw_db"},
        provide_context=True,
    )

    upsert_container_task = PythonOperator(
        task_id="upsert_container",
        python_callable=upsert_container,
        op_kwargs={"postgres_conn_id": "tkw_db"},
        provide_context=True,
    )

    upsert_key_task = PythonOperator(
        task_id="upsert_key",
        python_callable=upsert_key,
        op_kwargs={"postgres_conn_id": "tkw_db"},
        provide_context=True,
    )

    upsert_food_drink_task = PythonOperator(
        task_id="upsert_food_drink",
        python_callable=upsert_food_drink,
        op_kwargs={"postgres_conn_id": "tkw_db"},
        provide_context=True,
    )

    upsert_medical_task = PythonOperator(
        task_id="upsert_medical",
        python_callable=upsert_medical,
        op_kwargs={"postgres_conn_id": "tkw_db"},
        provide_context=True,
    )

    upsert_ammo_task = PythonOperator(
        task_id="upsert_ammo",
        python_callable=upsert_ammo,
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
        upsert_backpack_task,
        upsert_rig_task,
        upsert_container_task,
        upsert_key_task,
        upsert_food_drink_task,
        upsert_medical_task,
        upsert_ammo_task,
    ]
