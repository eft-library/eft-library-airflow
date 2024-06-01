from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator

with DAG(
    dag_id="dags_tkw_item_upsert",
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule="5 0 * * *",
    catchup=False,
) as dag:

    def upsert_item(postgres_conn_id, **kwargs):
        from airflow.providers.postgres.hooks.postgres import PostgresHook
        from contextlib import closing
        from custom_module.psql_function import read_sql
        from custom_module.graphql_function import get_graphql
        from custom_module.tkw_item_function import (
            check_category,
            process_gun,
            process_knife,
            process_throwable,
            weapon_graphql,
            gun_image_change,
        )

        postgres_hook = PostgresHook(postgres_conn_id)

        try:
            weapon_data = get_graphql(weapon_graphql)

            with closing(postgres_hook.get_conn()) as conn:
                with closing(conn.cursor()) as cursor:
                    # gun
                    gun_sql = read_sql("upsert_tkw_weapon.sql")
                    gun_original_data = check_category(
                        weapon_data["data"]["items"], "Gun"
                    )
                    gun_image_data = check_category(
                        weapon_data["data"]["items"], "Gun image"
                    )
                    gun_process_data = gun_image_change(
                        gun_original_data, gun_image_data
                    )
                    print(gun_sql)
                    for item in gun_process_data:
                        cursor.execute(gun_sql, process_gun(item))

                    # knife
                    knife_sql = read_sql("upsert_tkw_knife.sql")
                    knife_data_list = check_category(
                        weapon_data["data"]["items"], "Knife"
                    )
                    print(knife_sql)
                    for item in knife_data_list:
                        cursor.execute(knife_sql, process_knife(item))

                    # throwable
                    throwable_sql = read_sql("upsert_tkw_throwable.sql")
                    throwable_data_list = check_category(
                        weapon_data["data"]["items"], "Throwable weapon"
                    )
                    print(throwable_sql)
                    for item in throwable_data_list:
                        cursor.execute(throwable_sql, process_throwable(item))

                    conn.commit()

        except Exception as e:
            conn.rollback()
            raise

        finally:
            if conn:
                conn.close()

    upsert_tkw_item = PythonOperator(
        task_id="update_tkw_item",
        python_callable=upsert_item,
        op_kwargs={"postgres_conn_id": "tkw_db"},
    )
    upsert_tkw_item
