from custom_module.queries import item as sql_queries

import json
import pendulum
from hashlib import sha256
from pathlib import Path
from shutil import rmtree

from airflow import DAG
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sdk import get_current_context
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from psycopg2.extras import execute_values
from airflow.task.trigger_rule import TriggerRule

from custom_module.item_snapshot import get_item_snapshot
from custom_module.weapon_modding import build_modding_rows, sync_modding_rows
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

ITEM_TMP_ROOT = Path("/opt/airflow/tmp/dags_item")


def item_run_directory():
    run_id = get_current_context()["run_id"]
    return ITEM_TMP_ROOT / sha256(run_id.encode("utf-8")).hexdigest()


def write_json(path, value):
    with path.open("w") as f:
        json.dump(value, f)
    return str(path)


def read_json(path):
    with Path(path).open("r") as f:
        return json.load(f)


with DAG(
    on_failure_callback=send_dag_failure_email,
    dag_id="dags_item",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="11 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
    max_active_runs=1,
) as dag:

    def fetch_item():
        snapshot = get_item_snapshot("regular")
        directory = item_run_directory()
        directory.mkdir(parents=True, exist_ok=True)
        return {
            "en": write_json(directory / "items.json", snapshot["items"]),
            "names": write_json(directory / "names.json", snapshot["names"]),
            "snapshot": write_json(
                directory / "snapshot.json",
                {key: snapshot[key] for key in ("data", "translations", "game_mode")},
            ),
        }

    def fetched_items_by_id(item_paths):
        return {item["id"]: item for item in read_json(item_paths["en"])}

    def transform_item_core_rows():
        ti = get_current_context()["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item")
        item_en_dict = fetched_items_by_id(item_paths)
        item_ids = set(item_en_dict)
        localized_names = read_json(item_paths["names"])

        # items
        item_rows = [
            v3_item_row_process(
                item_en_dict[iid], localized_names["ko"].get(iid),
                localized_names["ja"].get(iid),
            )
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

        # usage_items
        usage_rows = [
            v3_usage_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_usage_items_row(item_en_dict[iid])
        ]

        return write_json(
            item_run_directory() / "item_core_rows.json",
            {
                "items": item_rows,
                "item_penalties": penalties_rows,
                "usage_items": usage_rows,
            },
        )

    def transform_equipment_rows():
        ti = get_current_context()["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item")
        item_en_dict = fetched_items_by_id(item_paths)
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

        # protection_items
        protection_rows = [
            v3_protection_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_protection_items_row(item_en_dict[iid])
        ]

        return write_json(
            item_run_directory() / "equipment_rows.json",
            {
                "ammo_efficiency": ammo_efficiency_rows,
                "weapon_items": weapon_rows,
                "weapon_allowed_ammo": allowed_ammo_rows,
                "ammo_items": ammo_rows,
                "melee_items": melee_rows,
                "throwable_items": throwable_rows,
                "protection_items": protection_rows,
            },
        )

    def transform_storage_and_consumable_rows():
        ti = get_current_context()["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item")
        item_en_dict = fetched_items_by_id(item_paths)
        item_ids = set(item_en_dict)

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

        # consumable_items, consumable_cures, consumable_stim_effects
        consumable_rows, cure_rows, stim_rows = [], [], []
        for iid in item_ids:
            irow, crows, srows = v3_consumable_items_and_effects(item_en_dict[iid])
            if irow:
                consumable_rows.append(irow)
            cure_rows.extend(crows)
            stim_rows.extend(srows)

        return write_json(
            item_run_directory() / "storage_and_consumable_rows.json",
            {
                "storage_items": storage_rows,
                "storage_grids": grid_rows,
                "consumable_items": consumable_rows,
                "consumable_cures": cure_rows,
                "consumable_stim_effects": stim_rows,
            },
        )

    def transform_modding_rows():
        ti = get_current_context()["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item")
        snapshot = read_json(item_paths["snapshot"])
        if snapshot["game_mode"] != "regular":
            raise ValueError("Item synchronization requires the regular snapshot")
        rows = build_modding_rows(snapshot["data"], snapshot["translations"])
        return write_json(item_run_directory() / "modding_rows.json", rows)

    def upsert_item(postgres_conn_id):
        ti = get_current_context()["ti"]
        rows = {}
        for task_id in (
            "transform_item_core_rows",
            "transform_equipment_rows",
            "transform_storage_and_consumable_rows",
        ):
            rows.update(read_json(ti.xcom_pull(task_ids=task_id)))
        modding_rows = read_json(ti.xcom_pull(task_ids="transform_modding_rows"))

        hook = PostgresHook(postgres_conn_id)
        with closing(hook.get_conn()) as conn, conn.cursor() as cur:
            # Serialize item synchronization writers using the same transaction lock.
            cur.execute("SELECT pg_advisory_xact_lock(724106110)")
            cur.execute(sql_queries.SELECT_ITEMS)
            existing_normalized_names_by_id = dict(cur.fetchall())
            item_rows = assign_unique_normalized_names(
                rows["items"], existing_normalized_names_by_id
            )

            # 하위 테이블 전체 비우기 (items 제외)
            cur.execute(sql_queries.TRUNCATE_ITEM_PENALTIES)
            execute_values(cur, sql_queries.INSERT_ITEMS, item_rows)
            for query, table in (
                (sql_queries.INSERT_AMMO_EFFICIENCY, "ammo_efficiency"),
                (sql_queries.INSERT_ITEM_PENALTIES, "item_penalties"),
                (sql_queries.INSERT_WEAPON_ITEMS, "weapon_items"),
                (sql_queries.INSERT_WEAPON_ALLOWED_AMMO, "weapon_allowed_ammo"),
                (sql_queries.INSERT_AMMO_ITEMS, "ammo_items"),
                (sql_queries.INSERT_MELEE_ITEMS, "melee_items"),
                (sql_queries.INSERT_THROWABLE_ITEMS, "throwable_items"),
                (sql_queries.INSERT_STORAGE_ITEMS, "storage_items"),
                (sql_queries.INSERT_STORAGE_GRIDS, "storage_grids"),
                (sql_queries.INSERT_PROTECTION_ITEMS, "protection_items"),
                (sql_queries.INSERT_CONSUMABLE_ITEMS, "consumable_items"),
                (sql_queries.INSERT_CONSUMABLE_CURES, "consumable_cures"),
                (sql_queries.INSERT_CONSUMABLE_STIM_EFFECTS, "consumable_stim_effects"),
                (sql_queries.INSERT_USAGE_ITEMS, "usage_items"),
            ):
                if rows[table]:
                    execute_values(cur, query, rows[table])

            sync_modding_rows(cur, modding_rows)
            print("[item-modding] synchronized rows:", {table: len(rows) for table, rows in modding_rows.items()})
            # Keep historical items for quest/trade references; remove obsolete weapon details only.
            cur.execute("DELETE FROM weapon_items WHERE NOT (item_id = ANY(%s::text[]))",
                        ([row[0] for row in rows["weapon_items"]],))
            conn.commit()

    def remove_json_files():
        try:
            rmtree(item_run_directory())
        except FileNotFoundError:
            pass

    fetch_item_task = PythonOperator(
        task_id="fetch_item",
        python_callable=fetch_item,
    )

    transform_item_core_rows_task = PythonOperator(
        task_id="transform_item_core_rows",
        python_callable=transform_item_core_rows,
    )

    transform_equipment_rows_task = PythonOperator(
        task_id="transform_equipment_rows",
        python_callable=transform_equipment_rows,
    )

    transform_storage_and_consumable_rows_task = PythonOperator(
        task_id="transform_storage_and_consumable_rows",
        python_callable=transform_storage_and_consumable_rows,
    )

    transform_modding_rows_task = PythonOperator(
        task_id="transform_modding_rows",
        python_callable=transform_modding_rows,
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


    publish_modding_task = TriggerDagRunOperator(
        task_id="publish_weapon_modding_static_json",
        trigger_dag_id="dags_weapon_modding_static_json",
        wait_for_completion=False,
    )

    transforms = [
        transform_item_core_rows_task,
        transform_equipment_rows_task,
        transform_storage_and_consumable_rows_task,
        transform_modding_rows_task,
    ]
    fetch_item_task >> transforms >> upsert_item_task
    transforms >> remove_json_files_task
    upsert_item_task >> remove_json_files_task
    upsert_item_task >> publish_modding_task

add_failure_watcher(dag)
