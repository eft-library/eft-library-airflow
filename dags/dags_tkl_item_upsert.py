from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_function import read_sql
from custom_module.graphql_function import get_graphql
from custom_module.tkl_item_function import check_category, item_graphql
from custom_module.item.knife_function import process_knife
from custom_module.item.throwable_function import process_throwable
from custom_module.item.rig_function import process_rig
from custom_module.item.armor_vest_function import process_armor_vest
from custom_module.item.headwear_function import process_headwear
from custom_module.item.headset_function import process_headset
from custom_module.item.gun_function import process_gun, gun_image_change
from custom_module.item.backpack_function import process_backpack
from custom_module.item.container_function import process_container
from custom_module.item.key_function import process_key, process_key_map
from custom_module.item.provisions_function import process_provisions
from custom_module.item.medical_function import process_medical
from custom_module.item.ammo_function import process_ammo
from custom_module.item.loot_function import process_loot

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_tkl_item_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="5 0 * * *",
    tags=['postgresql', "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_item_list(**kwargs):
        item_list = get_graphql(item_graphql)
        return item_list

    def upsert_gun(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_weapon.sql")
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
        sql = read_sql("upsert_tkl_knife.sql")
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
        sql = read_sql("upsert_tkl_throwable.sql")
        data_list = check_category(item_list["data"]["items"], "Throwable weapon")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_throwable(item))
            conn.commit()

    def upsert_headset(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_headset.sql")
        data_list = check_category(item_list["data"]["items"], "Headphones")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_headset(item))
            conn.commit()

    def upsert_headwear(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_headwear.sql")
        data_list = check_category(item_list["data"]["items"], "Headwear")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_headwear(item))
            conn.commit()

    def upsert_armor_vest(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_armor_vest.sql")
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
        sql = read_sql("upsert_tkl_backpack.sql")
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
        sql = read_sql("upsert_tkl_container.sql")
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
        sql = read_sql("upsert_tkl_key.sql")
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
        sql = read_sql("upsert_tkl_rig.sql")
        data_list = check_category(item_list["data"]["items"], "Chest rig")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_rig(item))
            conn.commit()

    def upsert_provisions(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_provisions.sql")
        data_list = check_category(item_list["data"]["items"], "Provisions")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_provisions(item))
            conn.commit()

    def upsert_medical(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_medical.sql")
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
        sql = read_sql("upsert_tkl_ammo.sql")
        data_list = check_category(item_list["data"]["items"], "Ammo")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_ammo(item))
            conn.commit()

    def upsert_loot(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_list = ti.xcom_pull(task_ids="fetch_item_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_loot.sql")
        data_list = check_category(item_list["data"]["items"], "Loot")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_loot(item))
            conn.commit()

    fetch_data = PythonOperator(
        task_id="fetch_item_list", python_callable=fetch_item_list
    )

    upsert_gun_task = PythonOperator(
        task_id="upsert_gun",
        python_callable=upsert_gun,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_knife_task = PythonOperator(
        task_id="upsert_knife",
        python_callable=upsert_knife,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_throwable_task = PythonOperator(
        task_id="upsert_throwable",
        python_callable=upsert_throwable,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_headset_task = PythonOperator(
        task_id="upsert_headset",
        python_callable=upsert_headset,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_headwear_task = PythonOperator(
        task_id="upsert_headwear",
        python_callable=upsert_headwear,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_armor_vest_task = PythonOperator(
        task_id="upsert_armor_vest",
        python_callable=upsert_armor_vest,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_rig_task = PythonOperator(
        task_id="upsert_rig",
        python_callable=upsert_rig,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_backpack_task = PythonOperator(
        task_id="upsert_backpack",
        python_callable=upsert_backpack,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_container_task = PythonOperator(
        task_id="upsert_container",
        python_callable=upsert_container,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_key_task = PythonOperator(
        task_id="upsert_key",
        python_callable=upsert_key,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_provisions_task = PythonOperator(
        task_id="upsert_provisions",
        python_callable=upsert_provisions,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_medical_task = PythonOperator(
        task_id="upsert_medical",
        python_callable=upsert_medical,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_ammo_task = PythonOperator(
        task_id="upsert_ammo",
        python_callable=upsert_ammo,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_loot_task = PythonOperator(
        task_id="upsert_loot",
        python_callable=upsert_loot,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    fetch_data >> [
        upsert_gun_task,
        upsert_knife_task,
        upsert_throwable_task,
        upsert_headset_task,
        upsert_headwear_task,
        upsert_armor_vest_task,
        upsert_backpack_task,
        upsert_rig_task,
        upsert_container_task,
        upsert_key_task,
        upsert_provisions_task,
        upsert_medical_task,
        upsert_ammo_task,
        upsert_loot_task,
    ]
