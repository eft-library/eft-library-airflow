import json
import os

import pendulum
from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import get_current_context
from airflow.task.trigger_rule import TriggerRule
from contextlib import closing
from psycopg2.extras import execute_values

from custom_module.tarkov_json_api import get_live_map_tasks
from custom_module.v3.live_map_point_task_func import (
    build_live_map_point_rows,
    normalize_map_name,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_live_map_point_en_list.json"
ko_path = "/opt/airflow/tmp/v3_live_map_point_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_live_map_point_ja_list.json"

with DAG(
    dag_id="v3_dags_live_map_point",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 5, 25, tz="Asia/Seoul"),
    schedule=None,
    tags=["postgresql", "tarkov-dev-api", "live-map"],
    catchup=False,
) as dag:

    def fetch_live_map_point():
        tasks_en = get_live_map_tasks("en")
        tasks_ko = get_live_map_tasks("ko")
        tasks_ja = get_live_map_tasks("ja")

        with open(en_path, "w") as f:
            json.dump(tasks_en, f)
        with open(ko_path, "w") as f:
            json.dump(tasks_ko, f)
        with open(ja_path, "w") as f:
            json.dump(tasks_ja, f)

        return {"en": en_path, "ko": ko_path, "ja": ja_path}

    def upsert_live_map_point(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        paths = ti.xcom_pull(task_ids="fetch_live_map_point")

        with open(paths["en"], "r") as f:
            tasks_en = json.load(f)
        with open(paths["ko"], "r") as f:
            tasks_ko = json.load(f)
        with open(paths["ja"], "r") as f:
            tasks_ja = json.load(f)

        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    select id,
                           normalized_name,
                           name_en
                    from maps
                    where is_use is true;
                    """
                )
                local_maps = {}
                for row in cursor.fetchall():
                    map_info = {
                        "id": row[0],
                        "normalized_name": row[1],
                        "name_en": row[2],
                    }
                    local_maps[row[0]] = map_info
                    local_maps[row[1]] = map_info
                    local_maps[normalize_map_name(row[2])] = map_info

                cursor.execute(
                    """
                    select id,
                           map_id,
                           floor_no,
                           min_y,
                           max_y,
                           sort_order
                    from live_map_floors
                    order by map_id, sort_order, floor_no;
                    """
                )
                floors_by_map_id = {}
                for row in cursor.fetchall():
                    floors_by_map_id.setdefault(row[1], []).append(
                        {
                            "id": row[0],
                            "map_id": row[1],
                            "floor_no": row[2],
                            "min_y": row[3],
                            "max_y": row[4],
                            "sort_order": row[5],
                        }
                    )

                cursor.execute(
                    """
                    select id,
                           floor_id,
                           map_id,
                           area_x_min,
                           area_x_max,
                           area_z_min,
                           area_z_max,
                           override_min_y,
                           override_max_y,
                           sort_order
                    from live_map_floor_zones
                    order by map_id, sort_order nulls last, id;
                    """
                )
                floor_zones_by_map_id = {}
                for row in cursor.fetchall():
                    floor_zones_by_map_id.setdefault(row[2], []).append(
                        {
                            "id": row[0],
                            "floor_id": row[1],
                            "map_id": row[2],
                            "area_x_min": row[3],
                            "area_x_max": row[4],
                            "area_z_min": row[5],
                            "area_z_max": row[6],
                            "override_min_y": row[7],
                            "override_max_y": row[8],
                            "sort_order": row[9],
                        }
                    )

                point_rows, detail_rows = build_live_map_point_rows(
                    tasks_en,
                    tasks_ko,
                    tasks_ja,
                    local_maps,
                    floors_by_map_id,
                    floor_zones_by_map_id,
                )

                if point_rows:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO live_map_points (
                            id,
                            quest_id,
                            objective_id,
                            map_id,
                            floor_id,
                            x,
                            z
                        )
                        VALUES %s
                        ON CONFLICT (id) DO NOTHING
                        """,
                        point_rows,
                        page_size=500,
                    )

                if detail_rows:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO live_map_point_details (
                            id,
                            point_id,
                            description_en,
                            description_ko,
                            description_ja,
                            image,
                            sort_order
                        )
                        VALUES %s
                        ON CONFLICT (id) DO NOTHING
                        """,
                        detail_rows,
                        page_size=500,
                    )

            conn.commit()

    def remove_json_files():
        files = [
            en_path,
            ko_path,
            ja_path,
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

    fetch_live_map_point_task = PythonOperator(
        task_id="fetch_live_map_point",
        python_callable=fetch_live_map_point,
    )

    upsert_live_map_point_task = PythonOperator(
        task_id="upsert_live_map_point",
        python_callable=upsert_live_map_point,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    fetch_live_map_point_task >> upsert_live_map_point_task >> remove_json_files_task
