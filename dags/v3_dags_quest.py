import json
import os
import pendulum

from contextlib import closing

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import get_current_context
from airflow.utils.trigger_rule import TriggerRule
from psycopg2.extras import execute_values

from custom_module.graphql_func import get_graphql
from custom_module.v3.quest_task_func import (
    generate_quest_graphql,
    v3_quest_process,
    v3_quest_objectives_process,
    v3_quest_objective_items_process,
    v3_quest_objective_maps_process,
    v3_quest_relations_process,
    v3_quest_finish_rewards_process,
    v3_quest_finish_reward_items_process,
    v3_quest_finish_reward_craft_unlocks_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_quest_en_list.json"
ko_path = "/opt/airflow/tmp/v3_quest_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_quest_ja_list.json"


with DAG(
    dag_id="v3_dags_quest",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="9 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_quest():
        item_list_en = get_graphql(generate_quest_graphql("en"))
        item_list_ko = get_graphql(generate_quest_graphql("ko"))
        item_list_ja = get_graphql(generate_quest_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["tasks"], f)

        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"]["tasks"], f)

        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"]["tasks"], f)

        return {"en": en_path, "ko": ko_path, "ja": ja_path}

    def upsert_quest(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_quest")

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

        if not item_ids:
            print("No quest data to process.")
            return

        quest_rows = []
        objective_rows = []
        objective_item_rows = []
        objective_map_rows = []
        relation_rows = []
        finish_reward_rows = []
        finish_reward_item_rows = []
        finish_reward_craft_unlock_rows = []

        for item_id in item_ids:
            item_en = item_en_dict[item_id]
            item_ko = item_ko_dict[item_id]
            item_ja = item_ja_dict[item_id]

            quest_rows.append(v3_quest_process(item_en, item_ko, item_ja))
            objective_rows.extend(v3_quest_objectives_process(item_en))
            objective_item_rows.extend(v3_quest_objective_items_process(item_en))
            objective_map_rows.extend(v3_quest_objective_maps_process(item_en))
            relation_rows.extend(v3_quest_relations_process(item_en))
            finish_reward_rows.extend(v3_quest_finish_rewards_process(item_en))
            finish_reward_item_rows.extend(
                v3_quest_finish_reward_items_process(item_en)
            )
            finish_reward_craft_unlock_rows.extend(
                v3_quest_finish_reward_craft_unlocks_process(item_en)
            )

        quest_sql = """
            INSERT INTO quests (
                id,
                normalized_name,
                name_en,
                name_ko,
                name_ja,
                trader_id,
                experience,
                delay_max,
                delay_min,
                kappa_required,
                min_player_level,
                wiki_url
            )
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                normalized_name = EXCLUDED.normalized_name,
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja,
                trader_id = EXCLUDED.trader_id,
                experience = EXCLUDED.experience,
                delay_max = EXCLUDED.delay_max,
                delay_min = EXCLUDED.delay_min,
                kappa_required = EXCLUDED.kappa_required,
                min_player_level = EXCLUDED.min_player_level,
                wiki_url = EXCLUDED.wiki_url,
                update_time = now()
        """

        objective_sql = """
            INSERT INTO quest_objectives (
                objective_id,
                quest_id,
                objective_type,
                raw_data
            )
            VALUES %s
            ON CONFLICT (objective_id) DO UPDATE
            SET
                quest_id = EXCLUDED.quest_id,
                objective_type = EXCLUDED.objective_type,
                raw_data = EXCLUDED.raw_data,
                update_time = now()
        """

        objective_item_sql = """
            INSERT INTO quest_objective_items (
                objective_id,
                item_type,
                item_id
            )
            VALUES %s
            ON CONFLICT (objective_id, item_type, item_id) DO NOTHING
        """

        objective_map_sql = """
            INSERT INTO quest_objective_maps (
                objective_id,
                map_id
            )
            VALUES %s
            ON CONFLICT (objective_id, map_id) DO NOTHING
        """

        relation_sql = """
            INSERT INTO quest_relations (
                quest_id,
                related_quest_id,
                relation_type
            )
            VALUES %s
            ON CONFLICT (quest_id, related_quest_id, relation_type) DO NOTHING
        """

        finish_reward_sql = """
            INSERT INTO quest_finish_rewards (
                quest_id,
                reward_type,
                target_id,
                reward_value,
                raw_data
            )
            VALUES %s
        """

        finish_reward_item_sql = """
            INSERT INTO quest_finish_reward_items (
                quest_id,
                item_id,
                quantity
            )
            VALUES %s
        """

        finish_reward_craft_unlock_sql = """
            INSERT INTO quest_finish_reward_craft_unlocks (
                quest_id,
                craft_id,
                station_level
            )
            VALUES %s
        """

        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                # 1. quests upsert
                execute_values(cursor, quest_sql, quest_rows, page_size=500)

                # 2. 기존 child 삭제
                cursor.execute(
                    "DELETE FROM quest_objective_items WHERE objective_id IN (SELECT objective_id FROM quest_objectives WHERE quest_id = ANY(%s))",
                    (item_ids,),
                )
                cursor.execute(
                    "DELETE FROM quest_objective_maps WHERE objective_id IN (SELECT objective_id FROM quest_objectives WHERE quest_id = ANY(%s))",
                    (item_ids,),
                )
                cursor.execute(
                    "DELETE FROM quest_objectives WHERE quest_id = ANY(%s)",
                    (item_ids,),
                )
                cursor.execute(
                    "DELETE FROM quest_relations WHERE quest_id = ANY(%s)",
                    (item_ids,),
                )
                cursor.execute(
                    "DELETE FROM quest_finish_rewards WHERE quest_id = ANY(%s)",
                    (item_ids,),
                )
                cursor.execute(
                    "DELETE FROM quest_finish_reward_items WHERE quest_id = ANY(%s)",
                    (item_ids,),
                )
                cursor.execute(
                    "DELETE FROM quest_finish_reward_craft_unlocks WHERE quest_id = ANY(%s)",
                    (item_ids,),
                )

                # 3. child insert
                if objective_rows:
                    execute_values(cursor, objective_sql, objective_rows, page_size=500)

                if objective_item_rows:
                    execute_values(
                        cursor, objective_item_sql, objective_item_rows, page_size=500
                    )

                if objective_map_rows:
                    execute_values(
                        cursor, objective_map_sql, objective_map_rows, page_size=500
                    )

                if relation_rows:
                    execute_values(cursor, relation_sql, relation_rows, page_size=500)

                if finish_reward_rows:
                    execute_values(
                        cursor, finish_reward_sql, finish_reward_rows, page_size=500
                    )

                if finish_reward_item_rows:
                    execute_values(
                        cursor,
                        finish_reward_item_sql,
                        finish_reward_item_rows,
                        page_size=500,
                    )

                if finish_reward_craft_unlock_rows:
                    execute_values(
                        cursor,
                        finish_reward_craft_unlock_sql,
                        finish_reward_craft_unlock_rows,
                        page_size=500,
                    )

            conn.commit()

    def remove_json_files():
        files = [en_path, ko_path, ja_path]

        for path in files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted: {path}")
                else:
                    print(f"File not found: {path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")

    fetch_quest_task = PythonOperator(
        task_id="fetch_quest",
        python_callable=fetch_quest,
    )

    upsert_quest_task = PythonOperator(
        task_id="upsert_quest",
        python_callable=upsert_quest,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    fetch_quest_task >> upsert_quest_task >> remove_json_files_task
