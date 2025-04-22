import os

from airflow import DAG
import pendulum
import json
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_func import read_sql
from custom_module.graphql_func import get_graphql
from custom_module.item_price_func import (
    generate_pvp_item_price_graphql,
    generate_pve_item_price_graphql,
)
from custom_module.item_price.price_func import (
    merge_item_price_data,
    v2_item_price_process,
    price_list_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

pvp_en_path = "/opt/airflow/tmp/pvp_item_price_en_list.json"
pvp_ko_path = "/opt/airflow/tmp/pvp_item_price_ko_list.json"
pvp_ja_path = "/opt/airflow/tmp/pvp_item_price_ja_list.json"

pve_en_path = "/opt/airflow/tmp/pve_item_price_en_list.json"
pve_ko_path = "/opt/airflow/tmp/pve_item_price_ko_list.json"
pve_ja_path = "/opt/airflow/tmp/pve_item_price_ja_list.json"

with DAG(
    dag_id="dags_item_price_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="0 * * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_price_list(**kwargs):
        pvp_list_en = get_graphql(generate_pvp_item_price_graphql("en"))
        print(generate_pvp_item_price_graphql("en"))
        pvp_list_ko = get_graphql(generate_pvp_item_price_graphql("ko"))
        pvp_list_ja = get_graphql(generate_pvp_item_price_graphql("ja"))

        pve_list_en = get_graphql(generate_pve_item_price_graphql("en"))
        pve_list_ko = get_graphql(generate_pve_item_price_graphql("ko"))
        pve_list_ja = get_graphql(generate_pve_item_price_graphql("ja"))

        with open(pvp_en_path, "w") as f:
            json.dump(pvp_list_en["data"]["items"], f)
        with open(pvp_ko_path, "w") as f:
            json.dump(pvp_list_ko["data"]["items"], f)
        with open(pvp_ja_path, "w") as f:
            json.dump(pvp_list_ja["data"]["items"], f)

        with open(pve_en_path, "w") as f:
            json.dump(pve_list_en["data"]["items"], f)
        with open(pve_ko_path, "w") as f:
            json.dump(pve_list_ko["data"]["items"], f)
        with open(pve_ja_path, "w") as f:
            json.dump(pve_list_ja["data"]["items"], f)

        return {
            "pvp_en": pvp_en_path,
            "pvp_ko": pvp_ko_path,
            "pvp_ja": pvp_ja_path,
            "pve_en": pve_en_path,
            "pve_ko": pve_ko_path,
            "pve_ja": pve_ja_path,
        }

    def upsert_price(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_price_list")

        with open(item_paths["pvp_en"], "r") as f:
            pvp_en_list = json.load(f)
        with open(item_paths["pvp_ko"], "r") as f:
            pvp_ko_list = json.load(f)
        with open(item_paths["pvp_ja"], "r") as f:
            pvp_ja_list = json.load(f)

        with open(item_paths["pve_en"], "r") as f:
            pve_en_list = json.load(f)
        with open(item_paths["pve_ko"], "r") as f:
            pve_ko_list = json.load(f)
        with open(item_paths["pve_ja"], "r") as f:
            pve_ja_list = json.load(f)

        pvp_en_dict = {item["id"]: item for item in pvp_en_list}
        pvp_ko_dict = {item["id"]: item for item in pvp_ko_list}
        pvp_ja_dict = {item["id"]: item for item in pvp_ja_list}

        pve_en_dict = {item["id"]: item for item in pve_en_list}
        pve_ko_dict = {item["id"]: item for item in pve_ko_list}
        pve_ja_dict = {item["id"]: item for item in pve_ja_list}

        pvp_item_ids = (
            set(pvp_en_dict.keys()) & set(pvp_ko_dict.keys()) & set(pvp_ja_dict.keys())
        )
        pve_item_ids = (
            set(pve_en_dict.keys()) & set(pve_ko_dict.keys()) & set(pve_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item_price.sql")

        data_list = ti.xcom_pull(task_ids="fetch_price_list")
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                pvp_item_list = []
                pve_item_list = []

                for item_id in pvp_item_ids:
                    item_en = pvp_en_dict[item_id]
                    item_ko = pvp_ko_dict[item_id]
                    item_ja = pvp_ja_dict[item_id]
                    pvp_item_list.append(price_list_process(item_en, item_ko, item_ja))

                for item_id in pve_item_ids:
                    item_en = pve_en_dict[item_id]
                    item_ko = pve_ko_dict[item_id]
                    item_ja = pve_ja_dict[item_id]
                    pve_item_list.append(price_list_process(item_en, item_ko, item_ja))

                merged_item_price_list = merge_item_price_data(
                    pvp_item_list, pve_item_list
                )

                for item in data_list:
                    insert_data = v2_item_price_process(item)
                    trader_data = json.loads(insert_data[3])
                    if trader_data.get("pve_trader") is None:
                        continue
                    cursor.execute(sql, insert_data)
            conn.commit()

    # def upsert_price_history(postgres_conn_id, **kwargs):
    #     ti = kwargs["ti"]
    #     data_list = ti.xcom_pull(task_ids="fetch_price_list")
    #     postgres_hook = PostgresHook(postgres_conn_id)
    #     sql = read_sql("upsert_tkl_price_history.sql")
    #
    #     with closing(postgres_hook.get_conn()) as conn:
    #         with closing(conn.cursor()) as cursor:
    #             batch_data = []  # executemany에 사용할 리스트
    #
    #             for item in data_list:
    #                 item_id = item.get("id")
    #                 if not item_id:
    #                     continue  # ID가 없는 데이터는 무시
    #
    #                 for pvp_price in item.get("pvpHistoricalPrices", []):
    #                     batch_data.append(process_price_history(item_id, pvp_price, "PVP"))
    #
    #                 for pve_price in item.get("pveHistoricalPrices", []):
    #                     batch_data.append(process_price_history(item_id, pve_price, "PVE"))
    #
    #             # Batch Insert (executemany 사용)
    #             if batch_data:
    #                 cursor.executemany(sql, batch_data)
    #
    #             conn.commit()  # 한 번에 커밋

    def remove_json_files(**kwargs):
        files = [
            pvp_en_path,
            pvp_ko_path,
            pvp_ja_path,
            pve_en_path,
            pve_ko_path,
            pve_ja_path,
        ]

        for path in files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted: {path}")
                else:
                    print(f"File not found: {path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")

    fetch_data = PythonOperator(
        task_id="fetch_price_list", python_callable=fetch_price_list
    )

    upsert_price_task = PythonOperator(
        task_id="upsert_price",
        python_callable=upsert_price,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )
    #
    # upsert_price_history_task = PythonOperator(
    #     task_id="upsert_price_history",
    #     python_callable=upsert_price_history,
    #     op_kwargs={"postgres_conn_id": "tkl_db"},
    #     provide_context=True,
    # )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        provide_context=True,
    )

    fetch_data >> upsert_price_task >> remove_json_files_task
