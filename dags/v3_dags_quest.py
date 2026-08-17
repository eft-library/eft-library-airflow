import json
import os
import pendulum

from contextlib import closing
from decimal import Decimal
from html import escape
from uuid import UUID

from airflow import DAG
from airflow.providers.smtp.operators.smtp import EmailOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import BranchPythonOperator, PythonOperator
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
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_quest_en_list.json"
ko_path = "/opt/airflow/tmp/v3_quest_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_quest_ja_list.json"

MANUAL_QUEST_OBJECTIVE_REQUIRED_KEYS = {
    ("64f732240e186112c4455d84", "64ccc246ff54fb38131acf29"),
}


with DAG(
    dag_id="v3_dags_quest",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="9 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_quest():
        item_list_en = get_tasks("en")
        item_list_ko = get_tasks("ko")
        item_list_ja = get_tasks("ja")

        with open(en_path, "w") as f:
            json.dump(item_list_en, f)

        with open(ko_path, "w") as f:
            json.dump(item_list_ko, f)

        with open(ja_path, "w") as f:
            json.dump(item_list_ja, f)

        return {"en": en_path, "ko": ko_path, "ja": ja_path}

    def compare_quest(postgres_conn_id):
        context = get_current_context()
        item_paths = context["ti"].xcom_pull(task_ids="fetch_quest")
        with open(item_paths["en"], "r") as f:
            en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            ja_list = json.load(f)

        ko_by_id = {item["id"]: item for item in ko_list}
        ja_by_id = {item["id"]: item for item in ja_list}
        api_quests = {}
        section_names = [
            "목표",
            "목표 아이템",
            "목표 필요 열쇠",
            "목표 맵",
            "선행 퀘스트",
            "완료 보상 - 스킬",
            "완료 보상 - 상인 평판",
            "완료 보상 - 거래 잠금 해제",
            "완료 보상 - 아이템",
            "완료 보상 - 제작 잠금 해제",
        ]
        api_sections = {name: {} for name in section_names}

        def store(section, key, owner_id, values=()):
            api_sections[section][key] = (owner_id, tuple(values))

        for item in en_list:
            quest_id = item["id"]
            api_quests[quest_id] = v3_quest_process(
                item, ko_by_id.get(quest_id), ja_by_id.get(quest_id)
            )
            objective_rows = v3_quest_objectives_process(
                item, ko_by_id.get(quest_id), ja_by_id.get(quest_id)
            )
            objective_owner = {row[0]: row[1] for row in objective_rows}
            for row in objective_rows:
                store(
                    "목표",
                    (row[0], row[1]),
                    row[1],
                    (row[2], row[3], row[6], row[7], row[8], row[9]),
                )
            for row in v3_quest_objective_items_process(item):
                store("목표 아이템", tuple(row), objective_owner.get(row[0]), ())
            for row in v3_quest_objective_required_keys_process(item):
                store("목표 필요 열쇠", tuple(row), objective_owner.get(row[0]), ())
            for row in v3_quest_objective_maps_process(item):
                store("목표 맵", tuple(row), objective_owner.get(row[0]), ())
            for row in v3_quest_relations_process(item):
                store("선행 퀘스트", tuple(row), row[0], ())

            skill_rows, standing_rows, offer_rows = v3_quest_finish_rewards_process(
                item, None, None
            )
            for row in skill_rows:
                store("완료 보상 - 스킬", (row[0], row[1]), row[0], (row[4],))
            for row in standing_rows:
                store("완료 보상 - 상인 평판", (row[0], row[1]), row[0], (row[2],))
            for row in offer_rows:
                store(
                    "완료 보상 - 거래 잠금 해제",
                    (row[0], row[1], row[3]),
                    row[0],
                    (row[2], row[4]),
                )
            for row in v3_quest_finish_reward_items_process(item):
                store("완료 보상 - 아이템", (row[0], row[1]), row[0], (row[2],))
            for row in v3_quest_finish_reward_craft_unlocks_process(item):
                store(
                    "완료 보상 - 제작 잠금 해제",
                    (row[0], row[1]),
                    row[0],
                    (row[2],),
                )

        db_sections = {name: {} for name in section_names}
        postgres_hook = PostgresHook(postgres_conn_id)
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    select id, normalized_name, name_en, name_ko, name_ja,
                           trader_id, experience, delay_max, delay_min,
                           kappa_required, min_player_level, wiki_url
                    from quests
                    """
                )
                db_quests = {
                    str(row[0]): (str(row[0]), *row[1:])
                    for row in cursor.fetchall()
                }

                cursor.execute(
                    """
                    select objective_id, quest_id, type, description_en,
                           description_ko, description_ja,
                           count, found_in_raid, optional, sort_order
                    from quest_objectives
                    """
                )
                objective_owner = {}
                for row in cursor.fetchall():
                    objective_id = str(row[0])
                    quest_id = str(row[1])
                    objective_owner[objective_id] = quest_id
                    db_sections["목표"][(objective_id, quest_id)] = (
                        quest_id,
                        (row[2], row[3], row[6], row[7], row[8], row[9]),
                    )

                child_queries = {
                    "목표 아이템": "select objective_id, item_id, item_type from quest_objective_items",
                    "목표 필요 열쇠": "select objective_id, key_id from quest_objective_required_keys",
                    "목표 맵": "select objective_id, map_id from quest_objective_maps",
                }
                for section, query in child_queries.items():
                    cursor.execute(query)
                    for row in cursor.fetchall():
                        key = tuple(str(value) for value in row)
                        db_sections[section][key] = (
                            objective_owner.get(key[0]),
                            (),
                        )

                cursor.execute(
                    """
                    select quest_id, related_quest_id, relation_type
                    from quest_relations
                    where relation_type = 'require'
                    """
                )
                for row in cursor.fetchall():
                    key = tuple(str(value) for value in row)
                    db_sections["선행 퀘스트"][key] = (key[0], ())

                reward_queries = {
                    "완료 보상 - 스킬": """
                        select quest_id, name_en, skill_level
                        from quest_finish_reward_skills
                    """,
                    "완료 보상 - 상인 평판": """
                        select quest_id, trader_id, standing
                        from quest_finish_reward_trader_standing
                    """,
                    "완료 보상 - 거래 잠금 해제": """
                        select quest_id, offer_id, trader_id, item_id, level
                        from quest_finish_reward_offer_unlock
                    """,
                    "완료 보상 - 아이템": """
                        select quest_id, item_id, quantity
                        from quest_finish_reward_items
                    """,
                    "완료 보상 - 제작 잠금 해제": """
                        select quest_id, craft_id, station_level
                        from quest_finish_reward_craft_unlocks
                    """,
                }
                for section, query in reward_queries.items():
                    cursor.execute(query)
                    for row in cursor.fetchall():
                        quest_id = str(row[0])
                        child_id = str(row[1])
                        if section == "완료 보상 - 거래 잠금 해제":
                            item_id = str(row[3])
                            db_sections[section][
                                (quest_id, child_id, item_id)
                            ] = (quest_id, (row[2], row[4]))
                        else:
                            db_sections[section][(quest_id, child_id)] = (
                                quest_id,
                                tuple(row[2:]),
                            )

                cursor.execute("select id, name_en from items")
                item_names = {str(row[0]): row[1] for row in cursor.fetchall()}
                cursor.execute("select id, name_en from maps")
                map_names = {str(row[0]): row[1] for row in cursor.fetchall()}
                cursor.execute("select id, name_en from traders")
                trader_names = {str(row[0]): row[1] for row in cursor.fetchall()}

        api_ids = set(api_quests)
        db_ids = set(db_quests)
        changes_by_quest = {}

        def quest_name(quest_id):
            api_row = api_quests.get(quest_id)
            db_row = db_quests.get(quest_id)
            return (api_row and api_row[2]) or (db_row and db_row[2]) or quest_id

        def add_change(quest_id, message):
            if not quest_id:
                return
            changes_by_quest.setdefault(
                quest_id,
                {"id": quest_id, "name": quest_name(quest_id), "changes": []},
            )["changes"].append(message)

        for quest_id in sorted(api_ids - db_ids):
            add_change(quest_id, "퀘스트 추가")
        for quest_id in sorted(db_ids - api_ids):
            add_change(quest_id, "퀘스트 삭제")

        quest_fields = {
            1: "정규화 이름",
            2: "영문 이름",
            3: "한국어 이름",
            4: "일본어 이름",
            5: "상인",
            6: "경험치",
            7: "최대 지연 시간",
            8: "최소 지연 시간",
            9: "카파 필수 여부",
            10: "최소 플레이어 레벨",
            11: "Wiki URL",
        }

        def normalize(value):
            if isinstance(value, UUID):
                return str(value)
            if isinstance(value, Decimal):
                return value.normalize()
            if isinstance(value, float):
                return Decimal(str(value)).normalize()
            if isinstance(value, (tuple, list)):
                return tuple(normalize(item) for item in value)
            return value

        for quest_id in sorted(api_ids & db_ids):
            fields = [
                (
                    f"{label}: {db_quests[quest_id][index]}"
                    f" → {api_quests[quest_id][index]}"
                )
                for index, label in quest_fields.items()
                if normalize(api_quests[quest_id][index])
                != normalize(db_quests[quest_id][index])
            ]
            if fields:
                add_change(quest_id, f"기본 정보 변경 ({', '.join(fields)})")

        common_ids = api_ids & db_ids
        section_fields = {
            "목표": ("유형", "설명", "수량", "인레이드", "순서"),
            "목표 아이템": (),
            "목표 필요 열쇠": (),
            "목표 맵": (),
            "선행 퀘스트": (),
            "완료 보상 - 스킬": ("스킬 레벨",),
            "완료 보상 - 상인 평판": ("평판",),
            "완료 보상 - 거래 잠금 해제": (
                "상인 ID",
                "레벨",
            ),
            "완료 보상 - 아이템": ("수량",),
            "완료 보상 - 제작 잠금 해제": ("시설 레벨",),
        }

        def format_values(section, values):
            if not values:
                return ""
            return ", ".join(
                f"{name}={value}"
                for name, value in zip(section_fields[section], values)
            )

        def format_changed_values(section, db_value, api_value):
            return ", ".join(
                f"{name}: {old} → {new}"
                for name, old, new in zip(
                    section_fields[section], db_value, api_value
                )
                if normalize(old) != normalize(new)
            )

        def named_id(value, names):
            name = names.get(str(value))
            return f"{name} ({value})" if name else str(value)

        quest_names = {str(key): value[2] for key, value in db_quests.items()}
        quest_names.update(
            {str(key): value[2] for key, value in api_quests.items()}
        )

        def format_key(section, key):
            if section == "목표 아이템":
                return f"목표 {key[0]}, {named_id(key[1], item_names)}, {key[2]}"
            if section == "목표 필요 열쇠":
                return f"목표 {key[0]}, {named_id(key[1], item_names)}"
            if section == "목표 맵":
                return f"목표 {key[0]}, {named_id(key[1], map_names)}"
            if section == "선행 퀘스트":
                return f"선행 {named_id(key[1], quest_names)}"
            if section == "완료 보상 - 상인 평판":
                return named_id(key[1], trader_names)
            if section == "완료 보상 - 거래 잠금 해제":
                return f"오퍼 {key[1]}, {named_id(key[2], item_names)}"
            if section == "완료 보상 - 아이템":
                return named_id(key[1], item_names)
            return str(key)

        for section in section_names:
            api_values = api_sections[section]
            db_values = db_sections[section]
            api_keys = {
                key for key, value in api_values.items() if value[0] in common_ids
            }
            db_keys = {
                key for key, value in db_values.items() if value[0] in common_ids
            }
            counts = {}
            detail_by_quest = {}
            for key in sorted(api_keys - db_keys):
                owner_id = api_values[key][0]
                counts.setdefault(owner_id, [0, 0, 0])[0] += 1
                values = format_values(section, api_values[key][1])
                detail_by_quest.setdefault(owner_id, []).append(
                    f"추가: {format_key(section, key)}"
                    f"{f' ({values})' if values else ''}"
                )
            deleted_keys = db_keys - api_keys
            if section == "목표 필요 열쇠":
                deleted_keys -= MANUAL_QUEST_OBJECTIVE_REQUIRED_KEYS
            for key in sorted(deleted_keys):
                owner_id = db_values[key][0]
                counts.setdefault(owner_id, [0, 0, 0])[1] += 1
                values = format_values(section, db_values[key][1])
                detail_by_quest.setdefault(owner_id, []).append(
                    f"삭제: {format_key(section, key)}"
                    f"{f' ({values})' if values else ''}"
                )
            for key in sorted(api_keys & db_keys):
                if normalize(api_values[key][1]) != normalize(db_values[key][1]):
                    owner_id = api_values[key][0]
                    counts.setdefault(owner_id, [0, 0, 0])[2] += 1
                    detail_by_quest.setdefault(owner_id, []).append(
                        f"변경: {format_key(section, key)} ("
                        f"{format_changed_values(section, db_values[key][1], api_values[key][1])})"
                    )

            for quest_id, (added, deleted, changed) in sorted(counts.items()):
                details = []
                if added:
                    details.append(f"추가 {added}건")
                if deleted:
                    details.append(f"삭제 {deleted}건")
                if changed:
                    details.append(f"변경 {changed}건")
                add_change(quest_id, f"{section} ({', '.join(details)})")
                detail_rows = detail_by_quest.get(quest_id, [])
                for detail in detail_rows[:20]:
                    add_change(quest_id, f"↳ {section} {detail}")
                if len(detail_rows) > 20:
                    add_change(
                        quest_id,
                        f"↳ {section} 외 {len(detail_rows) - 20}건",
                    )

        changes = [changes_by_quest[key] for key in sorted(changes_by_quest)]
        html_items = []
        for change in changes:
            details = "".join(
                f"<li>{escape(message)}</li>" for message in change["changes"]
            )
            html_items.append(
                f'<li><strong>{escape(str(change["name"]))}</strong> '
                f'({escape(str(change["id"]))})<ul>{details}</ul></li>'
            )

        return {
            "change_count": sum(len(change["changes"]) for change in changes),
            "quest_count": len(changes),
            "changes": changes,
            "html_content": (
                f"<h2>Quest API 데이터 변경 내역 ({len(changes)}개 퀘스트)</h2>"
                f"<ul>{''.join(html_items)}</ul>"
            ),
        }

    def choose_email_branch():
        context = get_current_context()
        diff = context["ti"].xcom_pull(task_ids="compare_quest") or {}
        if diff.get("change_count", 0) > 0:
            return "send_change_email"
        return "no_quest_changes"

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
            item_ko = item_ko_dict.get(item_id)
            item_ja = item_ja_dict.get(item_id)

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
                wiki_url,
                is_use
            )
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                normalized_name = EXCLUDED.normalized_name,
                name_en = EXCLUDED.name_en,
                name_ko = COALESCE(EXCLUDED.name_ko, quests.name_ko),
                name_ja = COALESCE(EXCLUDED.name_ja, quests.name_ja),
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

                # quest_objectives는 수동 데이터를 보존하기 위해 upsert로만 관리한다.
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

    def sync_roadmap_node(postgres_conn_id):
        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    insert into roadmap_node (
                        id,
                        total_x_coordinate,
                        total_y_coordinate,
                        single_x_coordinate,
                        single_y_coordinate,
                        total_kappa_x_coordinate,
                        total_kappa_y_coordinate,
                        single_kappa_x_coordinate,
                        single_kappa_y_coordinate
                    )
                    select
                        q.id,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    from quests q
                    where q.is_use is true
                    on conflict (id) do nothing
                    """
                )

            conn.commit()

    fetch_quest_task = PythonOperator(
        task_id="fetch_quest",
        python_callable=fetch_quest,
    )

    compare_quest_task = PythonOperator(
        task_id="compare_quest",
        python_callable=compare_quest,
        op_kwargs={"postgres_conn_id": "platform_db"},
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

    sync_roadmap_node_task = PythonOperator(
        task_id="sync_roadmap_node",
        python_callable=sync_roadmap_node,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    choose_email_branch_task = BranchPythonOperator(
        task_id="choose_email_branch",
        python_callable=choose_email_branch,
    )

    send_change_email_task = EmailOperator(
        task_id="send_change_email",
        to=["poeynus@gmail.com", "moonjipsa@gmail.com"],
        subject="[EFT Library] Quest API 데이터 변경 감지",
        html_content="{{ ti.xcom_pull(task_ids='compare_quest')['html_content'] }}",
        conn_id="smtp_gmail",
        from_email="poeynus@gmail.com",
    )

    no_quest_changes_task = EmptyOperator(task_id="no_quest_changes")

    (
        fetch_quest_task
        >> compare_quest_task
        >> upsert_quest_task
        >> build_next_relations_task
        >> sync_roadmap_node_task
    )
    sync_roadmap_node_task >> remove_json_files_task
    sync_roadmap_node_task >> choose_email_branch_task
    choose_email_branch_task >> [send_change_email_task, no_quest_changes_task]
