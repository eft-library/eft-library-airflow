from custom_module.queries import item as sql_queries

import json
import pendulum
import os

from airflow import DAG
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import get_current_context
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from psycopg2.extras import execute_values
from airflow.task.trigger_rule import TriggerRule

from custom_module.tarkov_json_api import get_items
from custom_module.item_task_func import (
    v3_item_row_process,
    assign_unique_normalized_names,
    v3_item_penalties_row,
    v3_weapon_items_row,
    v3_weapon_allowed_ammo_rows,
    v3_ammo_items_row,
    v3_melee_items_row,
    v3_throwable_items_row,
    v3_storage_items_and_grids,
    v3_protection_items_row,
    v3_consumable_items_and_effects,
    v3_usage_items_row,
    get_efficiency,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_item_en_list.json"

with DAG(
    on_failure_callback=send_dag_failure_email,
    dag_id="v3_dags_item",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="11 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_item():
        item_list_en = get_items("en")

        with open(en_path, "w") as f:
            json.dump(item_list_en, f)

        return {"en": en_path}

    def upsert_item(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}

        item_ids = set(item_en_dict)

        # ammo_efficiency
        ammo_efficiency_rows = []
        for iid in item_ids:
            item = item_en_dict[iid]
            props = item.get("properties")
            if not isinstance(props, dict):
                continue
            # ammo_items에 들어가는 아이템만 처리
            if not ("damage" in props or "penetrationPower" in props):
                continue
            eff = get_efficiency(item.get("name"))
            if eff and len(eff) == 6:
                ammo_efficiency_rows.append((iid, *eff))
        # items
        item_rows = [
            v3_item_row_process(item_en_dict[iid], None, None)
            for iid in item_ids
        ]

        # item_penalties
        def has_any_penalty(row):
            return any(x is not None for x in row[1:])

        penalties_rows = [
            r
            for iid in item_ids
            if has_any_penalty(r := v3_item_penalties_row(item_en_dict[iid]))
        ]

        # weapon_items
        weapon_rows = [
            v3_weapon_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_weapon_items_row(item_en_dict[iid])
        ]

        # weapon_allowed_ammo
        allowed_ammo_rows = []
        for iid in item_ids:
            allowed_ammo_rows.extend(v3_weapon_allowed_ammo_rows(item_en_dict[iid]))

        # ammo_items
        ammo_rows = [
            v3_ammo_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_ammo_items_row(item_en_dict[iid])
        ]

        # melee_items
        melee_rows = [
            v3_melee_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_melee_items_row(item_en_dict[iid])
        ]

        # throwable_items
        throwable_rows = [
            v3_throwable_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_throwable_items_row(item_en_dict[iid])
        ]

        # storage_items, storage_grids
        storage_rows, grid_rows = [], []
        for iid in item_ids:
            srow, grows = (
                v3_storage_items_and_grids(item_en_dict[iid])
                if v3_storage_items_and_grids(item_en_dict[iid])
                else (None, [])
            )
            if srow:
                storage_rows.append(srow)
            grid_rows.extend(grows)

        # protection_items
        protection_rows = [
            v3_protection_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_protection_items_row(item_en_dict[iid])
        ]

        # consumable_items, consumable_cures, consumable_stim_effects
        consumable_rows, cure_rows, stim_rows = [], [], []
        for iid in item_ids:
            irow, crows, srows = v3_consumable_items_and_effects(item_en_dict[iid])
            if irow:
                consumable_rows.append(irow)
            cure_rows.extend(crows)
            stim_rows.extend(srows)

        # usage_items
        usage_rows = [
            v3_usage_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_usage_items_row(item_en_dict[iid])
        ]

        hook = PostgresHook(postgres_conn_id)
        with closing(hook.get_conn()) as conn, conn.cursor() as cur:
            cur.execute(sql_queries.SELECT_ITEMS)
            existing_normalized_names_by_id = dict(cur.fetchall())
            item_rows = assign_unique_normalized_names(
                item_rows, existing_normalized_names_by_id
            )

            # 하위 테이블 전체 비우기 (items 제외)
            cur.execute(sql_queries.TRUNCATE_ITEM_PENALTIES)
            # items
            execute_values(
                cur,
                sql_queries.INSERT_ITEMS,
                item_rows,
            )

            # ammo_efficiency
            if ammo_efficiency_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_AMMO_EFFICIENCY,
                    ammo_efficiency_rows,
                )

            # item_penalties
            if penalties_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_ITEM_PENALTIES,
                    penalties_rows,
                )

            # weapon_items
            if weapon_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_WEAPON_ITEMS,
                    weapon_rows,
                )

            # weapon_allowed_ammo
            if allowed_ammo_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_WEAPON_ALLOWED_AMMO,
                    allowed_ammo_rows,
                )

            # ammo_items
            if ammo_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_AMMO_ITEMS,
                    ammo_rows,
                )

            # melee_items
            if melee_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_MELEE_ITEMS,
                    melee_rows,
                )

            # throwable_items
            if throwable_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_THROWABLE_ITEMS,
                    throwable_rows,
                )

            # storage_items
            if storage_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_STORAGE_ITEMS,
                    storage_rows,
                )

            # storage_grids
            if grid_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_STORAGE_GRIDS,
                    grid_rows,
                )

            # protection_items
            if protection_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_PROTECTION_ITEMS,
                    protection_rows,
                )

            # consumable_items
            if consumable_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_CONSUMABLE_ITEMS,
                    consumable_rows,
                )

            # consumable_cures
            if cure_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_CONSUMABLE_CURES,
                    cure_rows,
                )

            # consumable_stim_effects
            if stim_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_CONSUMABLE_STIM_EFFECTS,
                    stim_rows,
                )

            # usage_items
            if usage_rows:
                execute_values(
                    cur,
                    sql_queries.INSERT_USAGE_ITEMS,
                    usage_rows,
                )

            conn.commit()

    def remove_json_files():
        files = [en_path]

        for path in files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted: {path}")
                else:
                    print(f"File not found: {path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")

    fetch_item_task = PythonOperator(
        task_id="fetch_item",
        python_callable=fetch_item,
    )

    upsert_item_task = PythonOperator(
        task_id="upsert_item",
        python_callable=upsert_item,
        op_args=["platform_db"],
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    fetch_item_task >> upsert_item_task >> remove_json_files_task

add_failure_watcher(dag)
