from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator

with DAG(
        dag_id='dags_tkw_weapon_update',
        start_date=pendulum.datetime(2024, 5, 1, tz='Asia/Seoul'),
        schedule='5 0 * * *',
        catchup=False
) as dag:
    def update_weapon(postgres_conn_id, **kwargs):
        from airflow.providers.postgres.hooks.postgres import PostgresHook
        from contextlib import closing
        from custom_module.tkw_function import get_weapon, weapon_data_check, read_sql

        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                weapon_data_list = get_weapon()
                sql = read_sql('update_tkw_weapon.sql')
                print(sql)
                for item in weapon_data_list:
                    cursor.execute(sql, weapon_data_check(item))
                conn.commit()


    update_tkw_weapon = PythonOperator(
        task_id='update_tkw_weapon',
        python_callable=update_weapon,
        op_kwargs={'postgres_conn_id': 'tkw_db'}
    )
    update_tkw_weapon
