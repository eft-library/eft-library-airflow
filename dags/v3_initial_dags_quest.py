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

from custom_module.tarkov_json_api import get_tasks
from custom_module.v3.quest_task_func import (
    v3_quest_process,
    v3_quest_objectives_process,
    v3_quest_objective_items_process,
    v3_quest_objective_maps_process,
    v3_quest_relations_process,
    v3_quest_finish_rewards_process,
    v3_quest_finish_reward_items_process,
    v3_quest_finish_reward_craft_unlocks_process,
    v3_quest_objective_required_keys_process,
    v3_quest_reward_customizations_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_initial_quest_en_list.json"
ko_path = "/opt/airflow/tmp/v3_initial_quest_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_initial_quest_ja_list.json"
raw_path = "/opt/airflow/tmp/v3_initial_quest_raw_list.json"


with DAG(
    dag_id="v3_initial_dags_quest",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule=None,
    tags=["postgresql", "tarkov-dev-api", "initial-load", "manual-only"],
    catchup=False,
) as dag:

    def fetch_quest():
        item_list_raw = get_tasks(None)
        item_list_en = get_tasks("en")
        item_list_ko = get_tasks("ko")
        item_list_ja = get_tasks("ja")

        with open(raw_path, "w") as f:
            json.dump(item_list_raw, f)

        with open(en_path, "w") as f:
            json.dump(item_list_en, f)

        with open(ko_path, "w") as f:
            json.dump(item_list_ko, f)

        with open(ja_path, "w") as f:
            json.dump(item_list_ja, f)

        return {"raw": raw_path, "en": en_path, "ko": ko_path, "ja": ja_path}

    def upsert_quest(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_quest")

        with open(item_paths["raw"], "r") as f:
            item_raw_list = json.load(f)
        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_raw_dict = {item["id"]: item for item in item_raw_list}
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
        objective_required_key_rows = []
        objective_map_rows = []
        relation_rows = []
        skill_reward_rows = []
        standing_reward_rows = []
        offer_reward_rows = []
        finish_reward_item_rows = []
        finish_reward_craft_unlock_rows = []
        customization_rows = []
        customization_item_rows = []
        quest_reward_customization_rows = []

        for item_id in item_ids:
            item_en = item_en_dict[item_id]
            item_raw = item_raw_dict.get(item_id, item_en)
            item_ko = item_ko_dict[item_id]
            item_ja = item_ja_dict[item_id]

            quest_rows.append(v3_quest_process(item_en, item_ko, item_ja))
            objective_rows.extend(
                v3_quest_objectives_process(item_en, item_ko, item_ja)
            )
            objective_item_rows.extend(v3_quest_objective_items_process(item_en))
            objective_required_key_rows.extend(
                v3_quest_objective_required_keys_process(item_en)
            )
            objective_map_rows.extend(v3_quest_objective_maps_process(item_en))
            relation_rows.extend(v3_quest_relations_process(item_en))
            skill, standing, offer = v3_quest_finish_rewards_process(
                item_en, item_ko, item_ja
            )
            skill_reward_rows.extend(skill)
            standing_reward_rows.extend(standing)
            offer_reward_rows.extend(offer)
            finish_reward_item_rows.extend(
                v3_quest_finish_reward_items_process(item_en)
            )
            finish_reward_craft_unlock_rows.extend(
                v3_quest_finish_reward_craft_unlocks_process(item_en)
            )
            customizations, customization_items, reward_customizations = (
                v3_quest_reward_customizations_process(
                    item_raw, item_en, item_ko, item_ja
                )
            )
            customization_rows.extend(customizations)
            customization_item_rows.extend(customization_items)
            quest_reward_customization_rows.extend(reward_customizations)

        customization_rows = list({row[0]: row for row in customization_rows}.values())
        customization_item_rows = list(
            {(row[0], row[1]): row for row in customization_item_rows}.values()
        )
        quest_reward_customization_rows = list(
            {
                (row[0], row[1], row[2]): row
                for row in quest_reward_customization_rows
            }.values()
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
                wiki_url,
                is_use
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
                type,
                description_en,
                description_ko,
                description_ja,
                count,
                found_in_raid,
                optional,
                sort_order,
                is_use
            )
            VALUES %s
            ON CONFLICT (objective_id, quest_id) DO UPDATE
            SET
                type = EXCLUDED.type,
                description_en = EXCLUDED.description_en,
                description_ko = EXCLUDED.description_ko,
                description_ja = EXCLUDED.description_ja,
                count = EXCLUDED.count,
                found_in_raid = EXCLUDED.found_in_raid,
                optional = EXCLUDED.optional,
                sort_order = EXCLUDED.sort_order,
                update_time = now()
        """

        objective_item_sql = """
            INSERT INTO quest_objective_items (
                objective_id,
                item_id,
                item_type
            )
            VALUES %s
            ON CONFLICT (objective_id, item_id, item_type) DO NOTHING
        """

        objective_required_key_sql = """
            INSERT INTO quest_objective_required_keys (
                objective_id,
                key_id
            )
            VALUES %s
            ON CONFLICT (objective_id, key_id) DO NOTHING
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

        skill_reward_sql = """
            INSERT INTO quest_finish_reward_skills (
                quest_id,
                name_en,
                name_ko,
                name_ja,
                skill_level
            )
            VALUES %s
        """

        standing_reward_sql = """
            INSERT INTO quest_finish_reward_trader_standing (
                quest_id,
                trader_id,
                standing
            )
            VALUES %s
        """

        offer_reward_sql = """
            INSERT INTO quest_finish_reward_offer_unlock (
                quest_id,
                offer_id,
                trader_id,
                item_id,
                level
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

        customization_sql = """
            INSERT INTO customizations (
                id, name_key, name_en, name_ko, name_ja, image_link,
                customization_type, customization_type_name_key,
                customization_type_name_en, customization_type_name_ko,
                customization_type_name_ja
            ) VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                name_key = EXCLUDED.name_key,
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja,
                image_link = EXCLUDED.image_link,
                customization_type = EXCLUDED.customization_type,
                customization_type_name_key = EXCLUDED.customization_type_name_key,
                customization_type_name_en = EXCLUDED.customization_type_name_en,
                customization_type_name_ko = EXCLUDED.customization_type_name_ko,
                customization_type_name_ja = EXCLUDED.customization_type_name_ja,
                update_time = now()
        """

        customization_item_sql = """
            INSERT INTO customization_items (
                customization_id, item_id, sort_order
            ) VALUES %s
            ON CONFLICT (customization_id, item_id) DO UPDATE SET
                sort_order = EXCLUDED.sort_order
        """

        quest_reward_customization_sql = """
            INSERT INTO quest_reward_customizations (
                quest_id, customization_id, reward_type, sort_order
            ) VALUES %s
            ON CONFLICT (quest_id, customization_id, reward_type) DO UPDATE SET
                sort_order = EXCLUDED.sort_order,
                update_time = now()
        """

        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:

                cursor.execute(
                    """
                    truncate table
                        quest_objective_items,
                        quest_objective_required_keys,
                        quest_objective_maps,
                        quest_relations,
                        quest_finish_reward_skills,
                        quest_finish_reward_trader_standing,
                        quest_finish_reward_offer_unlock,
                        quest_finish_reward_items,
                        quest_finish_reward_craft_unlocks
                    restart identity cascade;
                """
                )

                # quests upsert
                execute_values(cursor, quest_sql, quest_rows, page_size=500)

                if customization_rows:
                    execute_values(
                        cursor, customization_sql, customization_rows, page_size=500
                    )

                if customization_item_rows:
                    execute_values(
                        cursor,
                        customization_item_sql,
                        customization_item_rows,
                        page_size=500,
                    )

                if quest_reward_customization_rows:
                    execute_values(
                        cursor,
                        quest_reward_customization_sql,
                        quest_reward_customization_rows,
                        page_size=500,
                    )

                # child insert
                if objective_rows:
                    execute_values(
                        cursor,
                        objective_sql,
                        [(*row, False) for row in objective_rows],
                        page_size=500,
                    )

                if objective_item_rows:
                    execute_values(
                        cursor, objective_item_sql, objective_item_rows, page_size=500
                    )

                if objective_required_key_rows:
                    execute_values(
                        cursor,
                        objective_required_key_sql,
                        objective_required_key_rows,
                        page_size=500,
                    )

                if objective_map_rows:
                    execute_values(
                        cursor, objective_map_sql, objective_map_rows, page_size=500
                    )

                if relation_rows:
                    execute_values(cursor, relation_sql, relation_rows, page_size=500)

                if skill_reward_rows:
                    execute_values(
                        cursor, skill_reward_sql, skill_reward_rows, page_size=500
                    )

                if standing_reward_rows:
                    execute_values(
                        cursor, standing_reward_sql, standing_reward_rows, page_size=500
                    )

                if offer_reward_rows:
                    execute_values(
                        cursor, offer_reward_sql, offer_reward_rows, page_size=500
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
        files = [raw_path, en_path, ko_path, ja_path]

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
