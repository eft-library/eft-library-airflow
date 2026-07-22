import json
import pendulum
import os

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import get_current_context
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from psycopg2.extras import execute_values
from airflow.task.trigger_rule import TriggerRule

from custom_module.tarkov_json_api import get_bosses, get_boss_spawn_maps
from custom_module.v3.boss_task_func import (
    v3_boss_process,
    v3_boss_item_process,
    v3_boss_spawn_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_initial_boss_en_list.json"
ko_path = "/opt/airflow/tmp/v3_initial_boss_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_initial_boss_ja_list.json"
spawn_path = "/opt/airflow/tmp/v3_initial_boss_spawn_list.json"

with DAG(
    dag_id="v3_initial_dags_boss",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule=None,
    tags=["postgresql", "tarkov-dev-api", "initial-load", "manual-only"],
    catchup=False,
) as dag:

    def fetch_boss():
        item_list_en = get_bosses("en")
        item_list_ko = get_bosses("ko")
        item_list_ja = get_bosses("ja")

        with open(en_path, "w") as f:
            json.dump(item_list_en, f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko, f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja, f)

        return {"en": en_path, "ko": ko_path, "ja": ja_path}

    def fetch_spawn():
        spawn_data = get_boss_spawn_maps()

        with open(spawn_path, "w") as f:
            json.dump(spawn_data, f)

        return {"spawn": spawn_path}

    def upsert_boss(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_boss")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}
        item_ko_dict = {item["id"]: item for item in item_ko_list}
        item_ja_dict = {item["id"]: item for item in item_ja_list}

        item_ids = sorted(set(item_en_dict) & set(item_ko_dict) & set(item_ja_dict))

        boss_rows = []
        boss_item_rows = []

        for item_id in item_ids:
            item_en = item_en_dict[item_id]
            item_ko = item_ko_dict[item_id]
            item_ja = item_ja_dict[item_id]

            boss_rows.append(v3_boss_process(item_en, item_ko, item_ja))

            boss_item_rows.extend(v3_boss_item_process(item_en))

        if not boss_rows:
            return

        boss_sql = """
            insert into bosses (
                id, name_en, name_ko, name_ja, image, normalized_name,
                health_total, head_hp, thorax_hp, stomach_hp,
                left_arm_hp, right_arm_hp, left_leg_hp, right_leg_hp
            )
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja,
                image = EXCLUDED.image,
                normalized_name = EXCLUDED.normalized_name,
                health_total = EXCLUDED.health_total,
                head_hp = EXCLUDED.head_hp,
                thorax_hp = EXCLUDED.thorax_hp,
                stomach_hp = EXCLUDED.stomach_hp,
                left_arm_hp = EXCLUDED.left_arm_hp,
                right_arm_hp = EXCLUDED.right_arm_hp,
                left_leg_hp = EXCLUDED.left_leg_hp,
                right_leg_hp = EXCLUDED.right_leg_hp,
                update_time = now()
        """

        boss_item_sql = """
            insert into boss_item (boss_id, item_id, quantity)
            values %s
            ON CONFLICT (boss_id, item_id) DO UPDATE
            SET quantity = EXCLUDED.quantity
        """

        postgres_hook = PostgresHook(postgres_conn_id)
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    truncate table
                        boss_item
                    restart identity cascade;
                """
                )

                execute_values(
                    cursor,
                    boss_sql,
                    boss_rows,
                    page_size=500,
                )

                if boss_item_rows:
                    execute_values(
                        cursor,
                        boss_item_sql,
                        boss_item_rows,
                        page_size=500,
                    )

            conn.commit()

    def upsert_boss_spawn(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_spawn")

        with open(item_paths["spawn"], "r") as f:
            map_list = json.load(f)

        boss_spawn_rows = []

        for map_item in map_list:
            boss_spawn_rows.extend(v3_boss_spawn_process(map_item))

        if not boss_spawn_rows:
            return

        # 전체 한 번 더 dedupe
        dedup_map = {}
        for boss_id, map_id, spawn_chance in boss_spawn_rows:
            key = (boss_id, map_id)
            if key not in dedup_map:
                dedup_map[key] = spawn_chance
            else:
                dedup_map[key] = max(dedup_map[key], spawn_chance)

        boss_spawn_rows = [
            (boss_id, map_id, spawn_chance)
            for (boss_id, map_id), spawn_chance in dedup_map.items()
        ]

        sql = """
            insert into boss_spawn (boss_id, map_id, spawn_chance)
            values %s
            ON CONFLICT (boss_id, map_id) DO UPDATE
            SET spawn_chance = EXCLUDED.spawn_chance
        """

        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                execute_values(
                    cursor,
                    sql,
                    boss_spawn_rows,
                    page_size=500,
                )
            conn.commit()

    def remove_json_files():
        files = [en_path, ko_path, ja_path, spawn_path]

        for path in files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted: {path}")
                else:
                    print(f"File not found: {path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")

    fetch_boss_task = PythonOperator(
        task_id="fetch_boss",
        python_callable=fetch_boss,
    )

    upsert_boss_task = PythonOperator(
        task_id="upsert_boss",
        python_callable=upsert_boss,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    fetch_spawn_task = PythonOperator(
        task_id="fetch_spawn",
        python_callable=fetch_spawn,
    )

    upsert_boss_spawn_task = PythonOperator(
        task_id="upsert_boss_spawn",
        python_callable=upsert_boss_spawn,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    (
        fetch_boss_task
        >> upsert_boss_task
        >> fetch_spawn_task
        >> upsert_boss_spawn_task
        >> remove_json_files_task
    )
