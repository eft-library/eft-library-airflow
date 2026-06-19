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

from custom_module.graphql_func import get_graphql
from custom_module.v3.live_map_point_task_func import (
    build_live_map_point_rows,
    generate_live_map_point_graphql,
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
        tasks_en = get_graphql(generate_live_map_point_graphql("en"))
        tasks_ko = get_graphql(generate_live_map_point_graphql("ko"))
        tasks_ja = get_graphql(generate_live_map_point_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(tasks_en["data"]["tasks"], f)
        with open(ko_path, "w") as f:
            json.dump(tasks_ko["data"]["tasks"], f)
        with open(ja_path, "w") as f:
            json.dump(tasks_ja["data"]["tasks"], f)

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

                point_rows, detail_rows = build_live_map_point_rows(
                    tasks_en,
                    tasks_ko,
                    tasks_ja,
                    local_maps,
                    floors_by_map_id,
                )

                quest_ids = [(task.get("id"),) for task in tasks_en if task.get("id")]
                cursor.execute(
                    """
                    create temporary table incoming_live_map_quests (
                        quest_id text
                    ) on commit drop
                    """
                )
                if quest_ids:
                    execute_values(
                        cursor,
                        """
                        insert into incoming_live_map_quests (
                            quest_id
                        ) values %s
                        """,
                        quest_ids,
                        page_size=500,
                    )

                cursor.execute(
                    """
                    create temporary table incoming_live_map_points (
                        point_id text
                    ) on commit drop
                    """
                )
                if point_rows:
                    execute_values(
                        cursor,
                        """
                        insert into incoming_live_map_points (
                            point_id
                        ) values %s
                        """,
                        [(row[0],) for row in point_rows],
                        page_size=500,
                    )

                cursor.execute(
                    """
                    delete from live_map_point_details lmpd
                    using live_map_points lmp
                    where lmpd.point_id = lmp.id
                      and lmp.quest_id in (
                          select quest_id
                          from incoming_live_map_quests
                      )
                      and not exists (
                          select 1
                          from incoming_live_map_points incoming
                          where incoming.point_id = lmp.id
                      );
                    """
                )

                cursor.execute(
                    """
                    delete from live_map_points lmp
                    where lmp.quest_id in (
                        select quest_id
                        from incoming_live_map_quests
                    )
                    and not exists (
                        select 1
                        from incoming_live_map_points incoming
                        where incoming.point_id = lmp.id
                    );
                    """
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
                            floor_no,
                            x,
                            z,
                            y,
                            sort_order
                        )
                        VALUES %s
                        ON CONFLICT (id) DO UPDATE
                        SET
                            quest_id = EXCLUDED.quest_id,
                            objective_id = EXCLUDED.objective_id,
                            map_id = EXCLUDED.map_id,
                            floor_id = EXCLUDED.floor_id,
                            floor_no = EXCLUDED.floor_no,
                            x = EXCLUDED.x,
                            z = EXCLUDED.z,
                            y = EXCLUDED.y,
                            sort_order = EXCLUDED.sort_order,
                            update_time = now()
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
                        ON CONFLICT (id) DO UPDATE
                        SET
                            point_id = EXCLUDED.point_id,
                            description_en = EXCLUDED.description_en,
                            description_ko = EXCLUDED.description_ko,
                            description_ja = EXCLUDED.description_ja,
                            image = COALESCE(EXCLUDED.image, live_map_point_details.image),
                            sort_order = EXCLUDED.sort_order,
                            update_time = now()
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
