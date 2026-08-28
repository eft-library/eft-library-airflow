from contextlib import closing

import pendulum
from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.standard.operators.python import PythonOperator
from psycopg2.extras import Json, execute_values

from custom_module.tarkov_json_api import get_prestige_data


POSTGRES_CONN_ID = "platform_db"

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}


def _localized_value(raw_value, localized_value):
    if localized_value in (None, "") or localized_value == raw_value:
        return None
    return localized_value


def _by_id(rows):
    return {row.get("id"): row for row in rows or [] if row.get("id")}


def _deduplicate(rows, key_indexes):
    deduplicated = {}
    for row in rows:
        key = tuple(row[index] for index in key_indexes)
        deduplicated[key] = row
    return list(deduplicated.values())


def sync_prestige(postgres_conn_id=POSTGRES_CONN_ID):
    payload = get_prestige_data()
    raw_levels = payload["raw"]
    if not raw_levels:
        raise ValueError("Empty prestige data from json.tarkov.dev/regular/tasks")

    localized_levels = {
        lang: _by_id(payload[lang]) for lang in ("en", "ko", "ja")
    }

    level_rows = []
    condition_rows = []
    condition_item_rows = []
    condition_status_rows = []
    condition_map_rows = []
    reward_item_rows = []
    reward_skill_rows = []
    customization_rows = []
    customization_item_rows = []
    transfer_setting_rows = []
    transfer_filter_rows = []

    for level_sort_order, raw_level in enumerate(raw_levels, start=1):
        prestige_id = raw_level["id"]
        localized_level = {
            lang: localized_levels[lang].get(prestige_id, {})
            for lang in ("en", "ko", "ja")
        }
        name_key = raw_level.get("name")
        level_rows.append(
            (
                prestige_id,
                raw_level.get("prestigeLevel"),
                name_key,
                _localized_value(name_key, localized_level["en"].get("name")),
                _localized_value(name_key, localized_level["ko"].get("name")),
                _localized_value(name_key, localized_level["ja"].get("name")),
                raw_level.get("iconLink"),
                raw_level.get("imageLink"),
                True,
                level_sort_order,
            )
        )

        localized_conditions = {
            lang: _by_id(localized_level[lang].get("conditions"))
            for lang in ("en", "ko", "ja")
        }
        for condition_sort_order, condition in enumerate(
            raw_level.get("conditions") or [], start=1
        ):
            condition_id = condition.get("id")
            if not condition_id:
                continue
            description_key = condition.get("description")
            condition_rows.append(
                (
                    condition_id,
                    prestige_id,
                    condition.get("type"),
                    description_key,
                    _localized_value(
                        description_key,
                        localized_conditions["en"]
                        .get(condition_id, {})
                        .get("description"),
                    ),
                    _localized_value(
                        description_key,
                        localized_conditions["ko"]
                        .get(condition_id, {})
                        .get("description"),
                    ),
                    _localized_value(
                        description_key,
                        localized_conditions["ja"]
                        .get(condition_id, {})
                        .get("description"),
                    ),
                    condition.get("count"),
                    condition.get("optional", False),
                    condition.get("playerLevel"),
                    condition.get("task"),
                    condition.get("station"),
                    condition.get("stationLevel"),
                    condition.get("skill"),
                    condition.get("level"),
                    condition.get("dogTagLevel"),
                    condition.get("maxDurability"),
                    condition.get("minDurability"),
                    condition.get("foundInRaid"),
                    condition_sort_order,
                )
            )
            for sort_order, item_id in enumerate(condition.get("items") or [], start=1):
                condition_item_rows.append((condition_id, item_id, sort_order))
            for sort_order, status in enumerate(condition.get("status") or [], start=1):
                condition_status_rows.append((condition_id, status, sort_order))
            for sort_order, map_id in enumerate(condition.get("maps") or [], start=1):
                condition_map_rows.append((condition_id, map_id, sort_order))

        rewards = raw_level.get("rewards") or {}
        for sort_order, reward in enumerate(rewards.get("items") or [], start=1):
            item_id = reward.get("item")
            if item_id:
                reward_item_rows.append(
                    (
                        prestige_id,
                        item_id,
                        reward.get("count"),
                        Json(reward.get("attributes") or {}),
                        sort_order,
                    )
                )

        for sort_order, reward in enumerate(
            rewards.get("skillLevelReward") or [], start=1
        ):
            skill_name = reward.get("skill")
            if skill_name:
                reward_skill_rows.append(
                    (prestige_id, skill_name, reward.get("level"), sort_order)
                )

        localized_customizations = {
            lang: _by_id(
                (localized_level[lang].get("rewards") or {}).get("customization")
            )
            for lang in ("en", "ko", "ja")
        }
        for sort_order, customization in enumerate(
            rewards.get("customization") or [], start=1
        ):
            customization_id = customization.get("id")
            if not customization_id:
                continue
            name_key = customization.get("name")
            type_name_key = customization.get("customizationTypeName")

            def customization_value(lang, field, raw_value):
                value = localized_customizations[lang].get(customization_id, {}).get(field)
                return _localized_value(raw_value, value)

            customization_rows.append(
                (
                    customization_id,
                    prestige_id,
                    name_key,
                    customization_value("en", "name", name_key),
                    customization_value("ko", "name", name_key),
                    customization_value("ja", "name", name_key),
                    customization.get("imageLink"),
                    customization.get("customizationType"),
                    type_name_key,
                    customization_value(
                        "en", "customizationTypeName", type_name_key
                    ),
                    customization_value(
                        "ko", "customizationTypeName", type_name_key
                    ),
                    customization_value(
                        "ja", "customizationTypeName", type_name_key
                    ),
                    sort_order,
                )
            )
            for item_sort_order, item_id in enumerate(
                customization.get("items") or [], start=1
            ):
                customization_item_rows.append(
                    (customization_id, item_id, item_sort_order)
                )

        localized_transfer_settings = {
            lang: localized_level[lang].get("transferSettings") or []
            for lang in ("en", "ko", "ja")
        }
        setting_type_counts = {}
        for sort_order, setting in enumerate(
            raw_level.get("transferSettings") or [], start=1
        ):
            setting_type = "item_grid" if "itemFilters" in setting else "skill"
            setting_type_counts[setting_type] = setting_type_counts.get(setting_type, 0) + 1
            if setting_type == "skill":
                setting_suffix = setting.get("skillType") or setting_type_counts[setting_type]
            else:
                setting_suffix = setting_type_counts[setting_type]
            setting_id = f"{prestige_id}:{setting_type}:{setting_suffix}"
            name_key = setting.get("name")

            def transfer_name(lang):
                localized_settings = localized_transfer_settings[lang]
                localized_setting = (
                    localized_settings[sort_order - 1]
                    if len(localized_settings) >= sort_order
                    else {}
                )
                return _localized_value(name_key, localized_setting.get("name"))

            transfer_setting_rows.append(
                (
                    setting_id,
                    prestige_id,
                    setting_type,
                    name_key,
                    transfer_name("en"),
                    transfer_name("ko"),
                    transfer_name("ja"),
                    setting.get("skillType"),
                    setting.get("transferRate"),
                    setting.get("gridWidth"),
                    setting.get("gridHeight"),
                    sort_order,
                )
            )
            filter_mappings = {
                "allowedCategories": "allowed_category",
                "allowedItems": "allowed_item",
                "excludedCategories": "excluded_category",
                "excludedItems": "excluded_item",
            }
            item_filters = setting.get("itemFilters") or {}
            for json_field, filter_type in filter_mappings.items():
                for filter_sort_order, value_id in enumerate(
                    item_filters.get(json_field) or [], start=1
                ):
                    transfer_filter_rows.append(
                        (setting_id, filter_type, value_id, filter_sort_order)
                    )

    row_groups = {
        "prestige_levels": _deduplicate(level_rows, (0,)),
        "prestige_conditions": _deduplicate(condition_rows, (0,)),
        "prestige_condition_items": _deduplicate(condition_item_rows, (0, 1)),
        "prestige_condition_statuses": _deduplicate(condition_status_rows, (0, 1)),
        "prestige_condition_maps": _deduplicate(condition_map_rows, (0, 1)),
        "prestige_reward_items": _deduplicate(reward_item_rows, (0, 1)),
        "prestige_reward_skills": _deduplicate(reward_skill_rows, (0, 1)),
        "prestige_reward_customizations": _deduplicate(customization_rows, (0,)),
        "prestige_reward_customization_items": _deduplicate(
            customization_item_rows, (0, 1)
        ),
        "prestige_transfer_settings": _deduplicate(transfer_setting_rows, (0,)),
        "prestige_transfer_filter_values": _deduplicate(
            transfer_filter_rows, (0, 1, 2)
        ),
    }

    sql_by_table = {
        "prestige_levels": """
            insert into prestige_levels (
                id, prestige_level, name_key, name_en, name_ko, name_ja,
                icon_link, image_link, is_use, sort_order
            ) values %s
            on conflict (id) do update set
                prestige_level = excluded.prestige_level,
                name_key = excluded.name_key,
                name_en = excluded.name_en,
                name_ko = excluded.name_ko,
                name_ja = excluded.name_ja,
                icon_link = excluded.icon_link,
                image_link = excluded.image_link,
                is_use = excluded.is_use,
                sort_order = excluded.sort_order,
                update_time = now()
        """,
        "prestige_conditions": """
            insert into prestige_conditions (
                id, prestige_id, condition_type, description_key,
                description_en, description_ko, description_ja, count,
                is_optional, player_level, task_id, station_id, station_level,
                skill_name, skill_level, dog_tag_level, max_durability,
                min_durability, found_in_raid, sort_order
            ) values %s
            on conflict (id) do update set
                prestige_id = excluded.prestige_id,
                condition_type = excluded.condition_type,
                description_key = excluded.description_key,
                description_en = excluded.description_en,
                description_ko = excluded.description_ko,
                description_ja = excluded.description_ja,
                count = excluded.count,
                is_optional = excluded.is_optional,
                player_level = excluded.player_level,
                task_id = excluded.task_id,
                station_id = excluded.station_id,
                station_level = excluded.station_level,
                skill_name = excluded.skill_name,
                skill_level = excluded.skill_level,
                dog_tag_level = excluded.dog_tag_level,
                max_durability = excluded.max_durability,
                min_durability = excluded.min_durability,
                found_in_raid = excluded.found_in_raid,
                sort_order = excluded.sort_order,
                update_time = now()
        """,
        "prestige_condition_items": """
            insert into prestige_condition_items (condition_id, item_id, sort_order)
            values %s on conflict (condition_id, item_id) do update set
                sort_order = excluded.sort_order
        """,
        "prestige_condition_statuses": """
            insert into prestige_condition_statuses (condition_id, status, sort_order)
            values %s on conflict (condition_id, status) do update set
                sort_order = excluded.sort_order
        """,
        "prestige_condition_maps": """
            insert into prestige_condition_maps (condition_id, map_id, sort_order)
            values %s on conflict (condition_id, map_id) do update set
                sort_order = excluded.sort_order
        """,
        "prestige_reward_items": """
            insert into prestige_reward_items (
                prestige_id, item_id, quantity, attributes, sort_order
            ) values %s on conflict (prestige_id, item_id) do update set
                quantity = excluded.quantity,
                attributes = excluded.attributes,
                sort_order = excluded.sort_order
        """,
        "prestige_reward_skills": """
            insert into prestige_reward_skills (
                prestige_id, skill_name, skill_level, sort_order
            ) values %s on conflict (prestige_id, skill_name) do update set
                skill_level = excluded.skill_level,
                sort_order = excluded.sort_order
        """,
        "prestige_reward_customizations": """
            insert into prestige_reward_customizations (
                customization_id, prestige_id, name_key, name_en, name_ko,
                name_ja, image_link, customization_type,
                customization_type_name_key, customization_type_name_en,
                customization_type_name_ko, customization_type_name_ja, sort_order
            ) values %s on conflict (customization_id) do update set
                prestige_id = excluded.prestige_id,
                name_key = excluded.name_key,
                name_en = excluded.name_en,
                name_ko = excluded.name_ko,
                name_ja = excluded.name_ja,
                image_link = excluded.image_link,
                customization_type = excluded.customization_type,
                customization_type_name_key = excluded.customization_type_name_key,
                customization_type_name_en = excluded.customization_type_name_en,
                customization_type_name_ko = excluded.customization_type_name_ko,
                customization_type_name_ja = excluded.customization_type_name_ja,
                sort_order = excluded.sort_order,
                update_time = now()
        """,
        "prestige_reward_customization_items": """
            insert into prestige_reward_customization_items (
                customization_id, item_id, sort_order
            ) values %s on conflict (customization_id, item_id) do update set
                sort_order = excluded.sort_order
        """,
        "prestige_transfer_settings": """
            insert into prestige_transfer_settings (
                id, prestige_id, setting_type, name_key, name_en, name_ko,
                name_ja, skill_type, transfer_rate, grid_width, grid_height,
                sort_order
            ) values %s on conflict (id) do update set
                prestige_id = excluded.prestige_id,
                setting_type = excluded.setting_type,
                name_key = excluded.name_key,
                name_en = excluded.name_en,
                name_ko = excluded.name_ko,
                name_ja = excluded.name_ja,
                skill_type = excluded.skill_type,
                transfer_rate = excluded.transfer_rate,
                grid_width = excluded.grid_width,
                grid_height = excluded.grid_height,
                sort_order = excluded.sort_order,
                update_time = now()
        """,
        "prestige_transfer_filter_values": """
            insert into prestige_transfer_filter_values (
                transfer_setting_id, filter_type, value_id, sort_order
            ) values %s
            on conflict (transfer_setting_id, filter_type, value_id) do update set
                sort_order = excluded.sort_order
        """,
    }

    postgres_hook = PostgresHook(postgres_conn_id)
    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:
            for table_name, rows in row_groups.items():
                if rows:
                    execute_values(
                        cursor,
                        sql_by_table[table_name],
                        rows,
                        page_size=500,
                    )
                    print(f"Upserted {len(rows)} rows into {table_name}")
        conn.commit()


with DAG(
    dag_id="v3_dags_prestige",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 8, 1, tz="Asia/Seoul"),
    schedule="10 0 * * *",
    tags=["postgresql", "tarkov-dev-api", "prestige"],
    catchup=False,
) as dag:
    sync_prestige_task = PythonOperator(
        task_id="sync_prestige",
        python_callable=sync_prestige,
        op_kwargs={"postgres_conn_id": POSTGRES_CONN_ID},
    )
