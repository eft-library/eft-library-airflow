def generate_quest_graphql(lang: str) -> str:
    return f"""
{{
  tasks(lang: {lang}) {{
    id
    name
    kappaRequired
    minPlayerLevel
    normalizedName
    experience
    availableDelaySecondsMin
    availableDelaySecondsMax
    wikiLink
    trader {{
      id
    }}
    taskRequirements {{
      task {{
        id
      }}
    }}
    objectives {{
      id
      type
      description
      optional
      ... on TaskObjectiveMark {{
        id
        markerItem {{
          gridImageLink
          id
          name
        }}
        maps {{
          id
          name
        }}
      }}
      ... on TaskObjectiveShoot {{
        count
      }}
      ... on TaskObjectiveQuestItem {{
        questItem {{
          id
        }}
        requiredKeys {{
          id
        }}
        count
      }}
      ... on TaskObjectiveItem {{
        items {{
          id
        }}
        requiredKeys {{
          id
        }}
        count
        foundInRaid
      }}
    }}
    finishRewards {{
      items {{
        item {{
          id
        }}
        quantity
      }}
      skillLevelReward{{
        name
        level
      }}
      traderStanding {{
        standing
        trader {{
          id
        }}
      }}
      offerUnlock {{
        id
        trader {{
          id
        }}
        item {{
          id
        }}
        level
      }}
      craftUnlock {{
        id
        station {{
          id
        }}
        level
        rewardItems {{
          item {{
            id
          }}
          quantity
        }}
      }}
    }}
  }}
}}
"""


def generate_quest_name_graphql(lang: str) -> str:
    return f"""
{{
  tasks(lang: {lang}) {{
    id
    name
  }}
}}
"""


def v3_quest_objectives_process(item_en, item_ko=None, item_ja=None):
    quest_id = item_en.get("id")
    objectives = item_en.get("objectives") or []
    objectives_ko = {
        obj.get("id"): obj
        for obj in (item_ko or {}).get("objectives") or []
        if obj.get("id")
    }
    objectives_ja = {
        obj.get("id"): obj
        for obj in (item_ja or {}).get("objectives") or []
        if obj.get("id")
    }
    rows = []
    seen = set()
    for obj in objectives:
        objective_id = obj.get("id")
        if not objective_id:
            continue
        key = (objective_id, quest_id)
        if key in seen:
            continue
        seen.add(key)
        sort_order = len(rows) + 1
        rows.append(
            (
                objective_id,
                quest_id,
                obj.get("type"),
                obj.get("description"),
                objectives_ko.get(objective_id, {}).get("description"),
                objectives_ja.get(objective_id, {}).get("description"),
                obj.get("count"),
                obj.get("foundInRaid"),
                obj.get("optional", False),
                sort_order,
            )
        )
    return rows


def v3_quest_objective_items_process(item_en):
    objectives = item_en.get("objectives") or []
    rows = []
    for obj in objectives:
        objective_id = obj.get("id")
        if not objective_id:
            continue
        # questItem
        quest_item = obj.get("questItem") or {}
        quest_item_id = quest_item.get("id")
        if quest_item_id:
            rows.append((objective_id, quest_item_id, "questItem"))
        # items[]
        for item in obj.get("items") or []:
            item_id = item.get("id")
            if item_id:
                rows.append((objective_id, item_id, "item"))
        # markerItem
        marker_item = obj.get("markerItem") or {}
        marker_item_id = marker_item.get("id")
        if marker_item_id:
            rows.append((objective_id, marker_item_id, "markerItem"))
    return rows


def v3_quest_objective_required_keys_process(item_en):
    objectives = item_en.get("objectives") or []
    rows = []
    for obj in objectives:
        objective_id = obj.get("id")
        if not objective_id:
            continue
        required_keys_groups = obj.get("requiredKeys")
        if required_keys_groups:
            for group_idx, group in enumerate(required_keys_groups):
                for key in group or []:
                    key_id = key.get("id")
                    if key_id:
                        rows.append((objective_id, key_id))
    return rows


def v3_quest_objective_maps_process(item_en):
    objectives = item_en.get("objectives") or []
    rows = []
    for obj in objectives:
        objective_id = obj.get("id")
        if not objective_id:
            continue
        for map_data in obj.get("maps") or []:
            map_id = map_data.get("id")
            if map_id:
                rows.append((objective_id, map_id))
    return rows


def v3_quest_process(item_en, item_ko, item_ja):
    item_ko = item_ko or {}
    item_ja = item_ja or {}
    quest_id = item_en.get("id")
    normalized_name = item_en.get("normalizedName")
    name_en = item_en.get("name")
    name_ko = item_ko.get("name")
    name_ja = item_ja.get("name")
    trader_id = (item_en.get("trader") or {}).get("id")
    experience = item_en.get("experience")
    delay_max = item_en.get("availableDelaySecondsMax")
    delay_min = item_en.get("availableDelaySecondsMin")
    kappa_required = item_en.get("kappaRequired")
    min_player_level = item_en.get("minPlayerLevel")
    wiki_url = item_en.get("wikiLink")

    return (
        quest_id,
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
        False,
    )


def v3_quest_relations_process(item_en):
    quest_id = item_en.get("id")
    task_requirements = item_en.get("taskRequirements") or []
    rows = []
    for relation in task_requirements:
        required_task = relation.get("task") or {}
        related_quest_id = required_task.get("id")
        if related_quest_id:
            rows.append((quest_id, related_quest_id, "require"))
    return rows


def v3_quest_finish_rewards_process(item_en, item_ko, item_ja):
    item_ko = item_ko or {}
    item_ja = item_ja or {}
    quest_id = item_en.get("id")
    finish_rewards = item_en.get("finishRewards") or {}
    finish_rewards_ko = item_ko.get("finishRewards") or {}
    finish_rewards_ja = item_ja.get("finishRewards") or {}
    skill_map = {}
    standing_map = {}
    offer_map = {}

    for idx, reward in enumerate(finish_rewards.get("skillLevelReward") or []):
        skill_name_en = reward.get("name")
        level = reward.get("level")
        skill_name_ko = None
        skill_name_ja = None
        try:
            skill_name_ko = (finish_rewards_ko.get("skillLevelReward") or [])[idx].get(
                "name"
            )
        except Exception:
            pass
        try:
            skill_name_ja = (finish_rewards_ja.get("skillLevelReward") or [])[idx].get(
                "name"
            )
        except Exception:
            pass
        if skill_name_en:
            skill_map[(quest_id, skill_name_en, level)] = (
                quest_id,
                skill_name_en,
                skill_name_ko,
                skill_name_ja,
                level,
            )

    for reward in finish_rewards.get("traderStanding") or []:
        trader_id = (reward.get("trader") or {}).get("id")
        standing = reward.get("standing")
        if trader_id:
            standing_map[(quest_id, trader_id)] = (quest_id, trader_id, standing)

    for reward in finish_rewards.get("offerUnlock") or []:
        offer_id = reward.get("id")
        trader_id = (reward.get("trader") or {}).get("id")
        item_id = (reward.get("item") or {}).get("id")
        level = reward.get("level")
        if offer_id:
            offer_map[(quest_id, offer_id, item_id)] = (
                quest_id,
                offer_id,
                trader_id,
                item_id,
                level,
            )

    return list(skill_map.values()), list(standing_map.values()), list(offer_map.values())


def v3_quest_finish_reward_items_process(item_en):
    quest_id = item_en.get("id")
    finish_rewards = item_en.get("finishRewards") or {}

    item_map = {}  # item_id 기준 dedupe

    for reward in finish_rewards.get("items") or []:
        item_id = (reward.get("item") or {}).get("id")
        quantity = reward.get("quantity")

        if not item_id:
            continue

        # 마지막 값으로 overwrite
        item_map[item_id] = (
            quest_id,
            item_id,
            quantity,
        )

    return list(item_map.values())


def v3_quest_finish_reward_craft_unlocks_process(item_en):
    quest_id = item_en.get("id")
    finish_rewards = item_en.get("finishRewards") or {}

    row_map = {}

    for craft in finish_rewards.get("craftUnlock") or []:
        craft_id = craft.get("id")
        station_level = craft.get("level")

        if craft_id:
            row_map[(quest_id, craft_id)] = (
                quest_id,
                craft_id,
                station_level,
            )

    return list(row_map.values())


def _localized_customization_value(raw_value, localized_value):
    if localized_value in (None, "") or localized_value == raw_value:
        return None
    return localized_value


def v3_quest_reward_customizations_process(
    item_raw, item_en=None, item_ko=None, item_ja=None
):
    """Build shared customization rows, item links, and quest reward links."""
    item_en = item_en or {}
    item_ko = item_ko or {}
    item_ja = item_ja or {}
    quest_id = item_raw.get("id")
    customization_rows = []
    customization_item_rows = []
    reward_rows = []
    reward_fields = {
        "start": "startRewards",
        "finish": "finishRewards",
        "failure": "failureOutcome",
    }

    for reward_type, reward_field in reward_fields.items():
        raw_rewards = item_raw.get(reward_field) or {}
        localized_by_language = {}
        for lang, item in (("en", item_en), ("ko", item_ko), ("ja", item_ja)):
            rewards = item.get(reward_field) or {}
            localized_by_language[lang] = {
                row.get("id"): row
                for row in rewards.get("customization") or []
                if row.get("id")
            }

        for sort_order, customization in enumerate(
            raw_rewards.get("customization") or [], start=1
        ):
            customization_id = customization.get("id")
            if not customization_id:
                continue
            name_key = customization.get("name")
            type_name_key = customization.get("customizationTypeName")

            def localized_value(lang, field, raw_value):
                value = localized_by_language[lang].get(customization_id, {}).get(field)
                return _localized_customization_value(raw_value, value)

            customization_rows.append(
                (
                    customization_id,
                    name_key,
                    localized_value("en", "name", name_key),
                    localized_value("ko", "name", name_key),
                    localized_value("ja", "name", name_key),
                    customization.get("imageLink"),
                    customization.get("customizationType"),
                    type_name_key,
                    localized_value("en", "customizationTypeName", type_name_key),
                    localized_value("ko", "customizationTypeName", type_name_key),
                    localized_value("ja", "customizationTypeName", type_name_key),
                )
            )
            for item_sort_order, item_id in enumerate(
                customization.get("items") or [], start=1
            ):
                customization_item_rows.append(
                    (customization_id, item_id, item_sort_order)
                )
            reward_rows.append(
                (quest_id, customization_id, reward_type, sort_order)
            )

    return customization_rows, customization_item_rows, reward_rows
