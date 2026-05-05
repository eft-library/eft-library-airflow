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
    v3_quest_objective_required_keys_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_quest_en_list.json"


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

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["tasks"], f)

        return {"en": en_path}

    def upsert_quest(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_quest")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}

        item_ids = sorted(set(item_en_dict))

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

        for item_id in item_ids:
            item_en = item_en_dict[item_id]

            quest_rows.append(v3_quest_process(item_en, None, None))
            objective_rows.extend(v3_quest_objectives_process(item_en))
            objective_item_rows.extend(v3_quest_objective_items_process(item_en))
            objective_required_key_rows.extend(
                v3_quest_objective_required_keys_process(item_en)
            )
            objective_map_rows.extend(v3_quest_objective_maps_process(item_en))
            relation_rows.extend(v3_quest_relations_process(item_en))
            skill, standing, offer = v3_quest_finish_rewards_process(
                item_en, None, None
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
                count,
                found_in_raid
            )
            VALUES %s
            ON CONFLICT (objective_id, quest_id) DO UPDATE
            SET
                type = EXCLUDED.type,
                description_en = EXCLUDED.description_en,
                count = EXCLUDED.count,
                found_in_raid = EXCLUDED.found_in_raid
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

        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    select quest_id, name_en, skill_level, name_ko, name_ja
                    from quest_finish_reward_skills
                    """
                )
                existing_skill_names = {
                    (quest_id, name_en, skill_level): (name_ko, name_ja)
                    for quest_id, name_en, skill_level, name_ko, name_ja in cursor.fetchall()
                }
                skill_reward_rows = [
                    (
                        quest_id,
                        name_en,
                        existing_skill_names.get(
                            (quest_id, name_en, skill_level), (name_ko, name_ja)
                        )[0],
                        existing_skill_names.get(
                            (quest_id, name_en, skill_level), (name_ko, name_ja)
                        )[1],
                        skill_level,
                    )
                    for quest_id, name_en, name_ko, name_ja, skill_level in skill_reward_rows
                ]

                cursor.execute(
                    """
                    create temporary table incoming_quests (
                        quest_id text
                    ) on commit drop
                    """
                )
                execute_values(
                    cursor,
                    """
                    insert into incoming_quests (
                        quest_id
                    ) values %s
                    """,
                    [(quest_id,) for quest_id, *_ in quest_rows],
                    page_size=500,
                )

                cursor.execute(
                    """
                    create temporary table incoming_quest_objectives (
                        objective_id text,
                        quest_id text
                    ) on commit drop
                    """
                )
                if objective_rows:
                    execute_values(
                        cursor,
                        """
                        insert into incoming_quest_objectives (
                            objective_id,
                            quest_id
                        ) values %s
                        """,
                        [
                            (objective_id, quest_id)
                            for objective_id, quest_id, *_ in objective_rows
                        ],
                        page_size=500,
                    )

                # 번역 컬럼이 없는 하위 테이블만 비운다. quest_objectives는 수동 번역 보존을 위해 upsert/delete로 관리한다.
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

                cursor.execute(
                    """
                    delete from quest_objectives qo
                    where qo.quest_id::text in (select quest_id from incoming_quests)
                    and not exists (
                        select 1
                        from incoming_quest_objectives incoming
                        where incoming.objective_id = qo.objective_id::text
                        and incoming.quest_id = qo.quest_id::text
                    )
                    """
                )

                # quests upsert
                execute_values(cursor, quest_sql, quest_rows, page_size=500)

                # child insert
                if objective_rows:
                    execute_values(cursor, objective_sql, objective_rows, page_size=500)

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

    def build_next_relations(postgres_conn_id):
        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    insert into quest_relations (
                        quest_id,
                        related_quest_id,
                        relation_type,
                        sort_order
                    )
                    select
                        related_quest_id as quest_id,
                        quest_id as related_quest_id,
                        'next' as relation_type,
                        sort_order
                    from quest_relations
                    where relation_type = 'require'
                    on conflict (quest_id, related_quest_id, relation_type) do nothing
                    """
                )

            conn.commit()

    fetch_quest_task = PythonOperator(
        task_id="fetch_quest",
        python_callable=fetch_quest,
    )

    upsert_quest_task = PythonOperator(
        task_id="upsert_quest",
        python_callable=upsert_quest,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    build_next_relations_task = PythonOperator(
        task_id="build_next_relations",
        python_callable=build_next_relations,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    fetch_quest_task >> upsert_quest_task >> build_next_relations_task >> remove_json_files_task
