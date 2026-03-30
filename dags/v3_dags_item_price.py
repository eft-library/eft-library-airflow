import json
import os
import pendulum

from contextlib import closing

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import get_current_context
from airflow.task.trigger_rule import TriggerRule
from psycopg2.extras import execute_values


from custom_module.graphql_func import get_graphql
from custom_module.v3.item_price_task_func import (
    generate_pvp_item_price_graphql,
    generate_pve_item_price_graphql,
    v3_item_price_row,
    v3_item_trader_price_rows,
    v3_item_price_history_rows,
)


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

pvp_en_path = "/opt/airflow/tmp/v3_item_price_pvp_en_list.json"
pve_en_path = "/opt/airflow/tmp/v3_item_price_pve_en_list.json"


with DAG(
    dag_id="v3_dags_item_price",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="15 * * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_item_price():
        pvp_list_en = get_graphql(generate_pvp_item_price_graphql("en"))
        pve_list_en = get_graphql(generate_pve_item_price_graphql("en"))

        with open(pvp_en_path, "w") as f:
            json.dump(pvp_list_en["data"]["items"], f)

        with open(pve_en_path, "w") as f:
            json.dump(pve_list_en["data"]["items"], f)

        return {"pvp_en": pvp_en_path, "pve_en": pve_en_path}

    def _load_item_lists():
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_price")

        with open(item_paths["pvp_en"], "r") as f:
            pvp_en_list = json.load(f)

        with open(item_paths["pve_en"], "r") as f:
            pve_en_list = json.load(f)

        return pvp_en_list, pve_en_list

    def _fetch_trader_name_map(cursor):
        cursor.execute("select id, name_en from traders")
        rows = cursor.fetchall()
        trader_name_map = {}

        for trader_id, name_en in rows:
            normalized_name = name_en
            if normalized_name:
                trader_name_map[normalized_name] = trader_id

        return trader_name_map

    def upsert_item_price(postgres_conn_id):
        pvp_en_list, pve_en_list = _load_item_lists()

        item_price_rows = []
        trader_price_rows = []

        postgres_hook = PostgresHook(postgres_conn_id)

        item_price_sql = """
            insert into item_prices (
                item_id,
                game_mode,
                highest_trader_price,
                highest_trader_id,
                flea_market_price,
                trader_count,
                has_flea
            )
            values %s
            on conflict (item_id, game_mode) do update
            set
                highest_trader_price = excluded.highest_trader_price,
                highest_trader_id = excluded.highest_trader_id,
                flea_market_price = excluded.flea_market_price,
                trader_count = excluded.trader_count,
                has_flea = excluded.has_flea,
                update_time = now()
        """

        trader_price_sql = """
            insert into item_trader_prices (
                id,
                item_id,
                game_mode,
                trader_id,
                price
            )
            values %s
            on conflict (id) do update
            set
                item_id = excluded.item_id,
                game_mode = excluded.game_mode,
                trader_id = excluded.trader_id,
                price = excluded.price
        """

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                trader_name_map = _fetch_trader_name_map(cursor)

                if not trader_name_map:
                    raise ValueError(
                        "traders table is empty. Run v3_dags_trader first."
                    )

                for game_mode, item_list in (
                    ("pvp", pvp_en_list),
                    ("pve", pve_en_list),
                ):
                    for item_en in item_list:
                        item_price_row = v3_item_price_row(
                            item_en, game_mode, trader_name_map
                        )
                        if item_price_row:
                            item_price_rows.append(item_price_row)

                        trader_price_rows.extend(
                            v3_item_trader_price_rows(
                                item_en, game_mode, trader_name_map
                            )
                        )

                cursor.execute(
                    "delete from item_trader_prices where game_mode in ('pvp', 'pve')"
                )
                cursor.execute(
                    "delete from item_prices where game_mode in ('pvp', 'pve')"
                )

                if item_price_rows:
                    execute_values(
                        cursor, item_price_sql, item_price_rows, page_size=500
                    )

                if trader_price_rows:
                    execute_values(
                        cursor, trader_price_sql, trader_price_rows, page_size=500
                    )

            conn.commit()

    def upsert_item_price_history(postgres_conn_id):
        pvp_en_list, pve_en_list = _load_item_lists()

        history_rows = []
        for game_mode, item_list in (("pvp", pvp_en_list), ("pve", pve_en_list)):
            for item_en in item_list:
                history_rows.extend(v3_item_price_history_rows(item_en, game_mode))

        postgres_hook = PostgresHook(postgres_conn_id)

        history_sql = """
            insert into item_price_history (
                item_id,
                price,
                game_mode,
                price_time
            )
            values %s
            on conflict (item_id, game_mode, price_time) do update
            set
                price = excluded.price
        """

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    "delete from item_price_history where price_time >= now() - interval '14 days'"
                )

                if history_rows:
                    execute_values(cursor, history_sql, history_rows, page_size=1000)

                cursor.execute(
                    "delete from item_price_history where price_time < now() - interval '14 days'"
                )

            conn.commit()

    def remove_json_files():
        files = [pvp_en_path, pve_en_path]

        for path in files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted: {path}")
                else:
                    print(f"File not found: {path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")

    fetch_item_price_task = PythonOperator(
        task_id="fetch_item_price",
        python_callable=fetch_item_price,
    )

    upsert_item_price_task = PythonOperator(
        task_id="upsert_item_price",
        python_callable=upsert_item_price,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    upsert_item_price_history_task = PythonOperator(
        task_id="upsert_item_price_history",
        python_callable=upsert_item_price_history,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    (
        fetch_item_price_task
        >> upsert_item_price_task
        >> upsert_item_price_history_task
        >> remove_json_files_task
    )
