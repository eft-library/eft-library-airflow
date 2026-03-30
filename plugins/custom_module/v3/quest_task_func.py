from psycopg2.extras import Json


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


def v3_quest_objectives_process(item_en):
    quest_id = item_en.get("id")
    objectives = item_en.get("objectives") or []
    rows = []
    for idx, obj in enumerate(objectives):
        objective_id = obj.get("id")
        if not objective_id:
            continue
        rows.append(
            (
                objective_id,
                quest_id,
                obj.get("type"),
                obj.get("description"),
                obj.get("count"),
                obj.get("foundInRaid"),
                Json(obj),
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
                        rows.append((objective_id, group_idx, key_id))
    return rows


def v3_quest_objective_maps_process(item_en):
    objectives = item_en.get("objectives") or []
    rows = []
    for obj in objectives:
        objective_id = obj.get("id")
        if not objective_id:
            continue
        for idx, map_data in enumerate(obj.get("maps") or []):
            map_id = map_data.get("id")
            if map_id:
                rows.append((objective_id, map_id))
    return rows


def v3_quest_requirements_process(item_en):
    quest_id = item_en.get("id")
    task_requirements = item_en.get("taskRequirements") or []
    rows = []
    for idx, relation in enumerate(task_requirements):
        required_task = relation.get("task") or {}
        required_quest_id = required_task.get("id")
        if required_quest_id:
            rows.append((quest_id, required_quest_id))
    return rows


def v3_quest_process(item_en, item_ko, item_ja):
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
    )


def v3_quest_relations_process(item_en):
    quest_id = item_en.get("id")
    task_requirements = item_en.get("taskRequirements") or []

    rows = []

    for relation in task_requirements:
        required_task = relation.get("task") or {}
        related_quest_id = required_task.get("id")

        if related_quest_id:
            rows.append(
                (
                    quest_id,
                    related_quest_id,
                    "require",
                )
            )

    return rows


def v3_quest_finish_rewards_process(item_en):
    quest_id = item_en.get("id")
    finish_rewards = item_en.get("finishRewards") or {}

    rows = []

    # 1) skillLevelReward
    for reward in finish_rewards.get("skillLevelReward") or []:
        skill_name = reward.get("name")
        level = reward.get("level")

        if skill_name:
            rows.append(
                (
                    quest_id,
                    "skill_level",
                    skill_name,
                    level,
                    Json(reward),
                )
            )

    # 2) traderStanding
    for reward in finish_rewards.get("traderStanding") or []:
        trader_id = (reward.get("trader") or {}).get("id")
        standing = reward.get("standing")

        if trader_id:
            rows.append(
                (
                    quest_id,
                    "trader_standing",
                    trader_id,
                    standing,
                    Json(reward),
                )
            )

    # 3) offerUnlock
    for reward in finish_rewards.get("offerUnlock") or []:
        offer_id = reward.get("id")
        level = reward.get("level")

        if offer_id:
            rows.append(
                (
                    quest_id,
                    "offer_unlock",
                    offer_id,
                    level,
                    Json(reward),
                )
            )

    return rows


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

    rows = []

    for craft in finish_rewards.get("craftUnlock") or []:
        craft_id = craft.get("id")
        station_level = craft.get("level")

        if craft_id:
            rows.append(
                (
                    quest_id,
                    craft_id,
                    station_level,
                )
            )

    return rows
