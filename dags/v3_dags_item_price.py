import json
import os
import pendulum

from contextlib import closing

from airflow import DAG
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import get_current_context
from airflow.task.trigger_rule import TriggerRule
from psycopg2.extras import execute_values


from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from custom_module.tarkov_json_api import get_item_prices, get_price_season
from custom_module.v3.item_price_task_func import (
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
season_path = "/opt/airflow/tmp/v3_item_price_season.json"
pve_en_path = "/opt/airflow/tmp/v3_item_price_pve_en_list.json"


with DAG(
    on_failure_callback=send_dag_failure_email,
    dag_id="v3_dags_item_price",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="15 * * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
    max_active_runs=1,
) as dag:

    def fetch_item_price():
        season = get_price_season()
        season_items = get_item_prices("pvp-season")
        if get_price_season()["id"] != season["id"]:
            raise ValueError("Season changed while fetching items")
        pvp_list_en = get_item_prices("regular")
        pve_list_en = get_item_prices("pve")

        with open(pvp_en_path, "w") as f:
            json.dump(pvp_list_en, f)

        with open(pve_en_path, "w") as f:
            json.dump(pve_list_en, f)

        with open(season_path, "w") as f:
            json.dump({"season": season, "items": season_items}, f)

        return {"pvp_en": pvp_en_path, "pve_en": pve_en_path, "season": season_path}

    def _load_item_lists():
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_price")

        with open(item_paths["pvp_en"], "r") as f:
            pvp_en_list = json.load(f)

        with open(item_paths["pve_en"], "r") as f:
            pve_en_list = json.load(f)

        with open(item_paths["season"], "r") as f:
            seasonal = json.load(f)

        return pvp_en_list, pve_en_list, seasonal

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
        pvp_en_list, pve_en_list, seasonal = _load_item_lists()

        item_price_rows = []
        trader_price_rows = []
        history_rows = []

        postgres_hook = PostgresHook(postgres_conn_id)

        item_price_sql = """
            insert into item_prices (
                item_id,
                game_mode,
                season_id,
                highest_trader_price,
                highest_trader_id,
                flea_market_price,
                trader_count,
                has_flea
            )
            values %s
            on conflict (item_id, game_mode, season_key) do update
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
                season_id,
                trader_id,
                price
            )
            values %s
            on conflict (item_id, game_mode, season_key, trader_id) do update
            set
                item_id = excluded.item_id,
                game_mode = excluded.game_mode,
                trader_id = excluded.trader_id,
                price = excluded.price
        """

        history_sql = """
            insert into item_price_history (
                item_id,
                price,
                game_mode,
                season_id,
                price_time
            )
            values %s
            on conflict (item_id, game_mode, season_key, price_time) do update
            set
                price = excluded.price
        """

        with closing(postgres_hook.get_conn()) as conn:
            with conn, closing(conn.cursor()) as cursor:
                trader_name_map = _fetch_trader_name_map(cursor)

                if not trader_name_map:
                    raise ValueError(
                        "traders table is empty. Run v3_dags_trader first."
                    )

                for game_mode, season_id, item_list in (
                    ("pvp", None, pvp_en_list),
                    ("pve", None, pve_en_list),
                    ("pvp-season", seasonal["season"]["id"], seasonal["items"]),
                ):
                    for item_en in item_list:
                        history_rows.extend(v3_item_price_history_rows(item_en, game_mode, season_id))
                        item_price_row = v3_item_price_row(
                            item_en, game_mode, trader_name_map, season_id
                        )
                        if item_price_row:
                            item_price_rows.append(item_price_row)

                        trader_price_rows.extend(
                            v3_item_trader_price_rows(
                                item_en, game_mode, trader_name_map, season_id
                            )
                        )

                season = seasonal["season"]
                cursor.execute("LOCK TABLE price_seasons IN EXCLUSIVE MODE")
                cursor.execute("UPDATE price_seasons SET is_current = false WHERE is_current")
                cursor.execute(
                    """INSERT INTO price_seasons (id, name, starts_at, ends_at, is_current)
                       VALUES (%s, %s, %s, %s, true)
                       ON CONFLICT (id) DO UPDATE SET name = excluded.name,
                           starts_at = excluded.starts_at, ends_at = excluded.ends_at,
                           is_current = true, update_time = now()""",
                    (season["id"], season["name"], season["starts_at"], season["ends_at"]),
                )
                for table in ("item_trader_prices", "item_prices"):
                    cursor.execute(
                        f"DELETE FROM {table} WHERE "
                        "(game_mode IN ('pvp', 'pve') AND season_id IS NULL) OR "
                        "(game_mode = 'pvp-season' AND season_id = %s)",
                        (season["id"],),
                    )

                if item_price_rows:
                    execute_values(
                        cursor, item_price_sql, item_price_rows, page_size=500
                    )

                if trader_price_rows:
                    execute_values(
                        cursor, trader_price_sql, trader_price_rows, page_size=500
                    )

                if history_rows:
                    execute_values(cursor, history_sql, history_rows, page_size=1000)
                cursor.execute(
                    "DELETE FROM item_price_history WHERE game_mode IN ('pvp', 'pve') "
                    "AND season_id IS NULL AND price_time < now() - interval '14 days'"
                )

    def remove_json_files():
        files = [pvp_en_path, pve_en_path, season_path]

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

    generate_static_task = TriggerDagRunOperator(
        task_id="generate_price_static_json",
        trigger_dag_id="v3_dags_price_static_json",
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    (
        fetch_item_price_task
        >> upsert_item_price_task
        >> generate_static_task
        >> remove_json_files_task
    )

add_failure_watcher(dag)
