from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_function import read_sql
from custom_module.graphql_function import get_graphql
from custom_module.item_price_function import pvp_item_price_graphql, pve_item_price_graphql
from custom_module.item_price.price_function import merge_item_price_data, process_price, process_price_history

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_tkl_item_price_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="0 * * * *",
    tags=['postgresql', "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_price_list(**kwargs):
        pvp_list = get_graphql(pvp_item_price_graphql)
        pve_list = get_graphql(pve_item_price_graphql)
        merged_data = merge_item_price_data(pvp_list['data']['items'], pve_list['data']['items'])
        return merged_data

    def upsert_price(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        data_list = ti.xcom_pull(task_ids="fetch_price_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_price.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item in data_list:
                    cursor.execute(sql, process_price(item))
            conn.commit()

    def upsert_price_history(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        data_list = ti.xcom_pull(task_ids="fetch_price_list")
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_tkl_price_history.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                batch_data = []  # executemany에 사용할 리스트

                for item in data_list:
                    item_id = item.get("id")
                    if not item_id:
                        continue  # ID가 없는 데이터는 무시

                    for pvp_price in item.get("pvpHistoricalPrices", []):
                        batch_data.append(process_price_history(item_id, pvp_price, "PVP"))

                    for pve_price in item.get("pveHistoricalPrices", []):
                        batch_data.append(process_price_history(item_id, pve_price, "PVE"))

                # Batch Insert (executemany 사용)
                if batch_data:
                    cursor.executemany(sql, batch_data)

                conn.commit()  # 한 번에 커밋

    fetch_data = PythonOperator(
        task_id="fetch_price_list", python_callable=fetch_price_list
    )

    upsert_price_task = PythonOperator(
        task_id="upsert_price",
        python_callable=upsert_price,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_price_history_task = PythonOperator(
        task_id="upsert_price_history",
        python_callable=upsert_price_history,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    fetch_data >> upsert_price_task >> upsert_price_history_task
