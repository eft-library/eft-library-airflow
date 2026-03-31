import re


def generate_hideout_graphql(lang: str) -> str:
    return f"""
{{
  hideoutStations(lang: {lang}) {{
    id
    name
    levels {{
      id
      itemRequirements {{
        id
        item {{
          id
        }}
        quantity
        attributes {{
          type
          value
        }}
      }}
      skillRequirements {{
        id
        name
        level
        skill {{
          id
          name
        }}
      }}
      traderRequirements {{
        id
        value
        trader {{
          id
        }}
      }}
      stationLevelRequirements {{
        id
        level
        station {{
          id
        }}
      }}
      level
      bonuses {{
        type
        name
        value
        skillName
      }}
      constructionTime
    }}
    imageLink
    crafts {{
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
      duration
      requiredItems {{
        item {{
          id
        }}
        quantity
      }}
    }}
  }}
}}
"""


def v3_hideout_master_process(item_en, item_ko, item_ja):
    master_id = item_en.get("id")
    name_en = item_en.get("name")
    name_ko = item_ko.get("name")
    name_ja = item_ja.get("name")
    normalized_name = normalize_hideout_name(name_en)

    return (master_id, normalized_name, name_en, name_ko, name_ja)


def normalize_hideout_name(name_en):
    if not name_en:
        return None

    normalized_name = name_en.lower()
    normalized_name = re.sub(r"['\"]", "", normalized_name)
    normalized_name = re.sub(r"[^a-z0-9]+", "-", normalized_name)
    normalized_name = re.sub(r"-+", "-", normalized_name).strip("-")

    return normalized_name or None


def v3_hideout_level_process(item_en):
    rows = []

    master_id = item_en.get("id")
    levels_en = item_en.get("levels", [])

    for level_en in levels_en:
        level_id = level_en.get("id")
        level = level_en.get("level")
        construction_time = level_en.get("constructionTime")

        rows.append((level_id, master_id, level, construction_time))

    return rows


def v3_hideout_skill_require_process(item_en, item_ko, item_ja):
    rows = []

    levels_en = item_en.get("levels", [])
    levels_ko = item_ko.get("levels", [])
    levels_ja = item_ja.get("levels", [])

    level_ko_dict = {level["id"]: level for level in levels_ko if level.get("id")}
    level_ja_dict = {level["id"]: level for level in levels_ja if level.get("id")}

    for level_en in levels_en:
        hideout_level_id = level_en.get("id")
        if not hideout_level_id:
            continue

        level_ko = level_ko_dict.get(hideout_level_id, {})
        level_ja = level_ja_dict.get(hideout_level_id, {})

        skill_en_list = level_en.get("skillRequirements", [])
        skill_ko_list = level_ko.get("skillRequirements", [])
        skill_ja_list = level_ja.get("skillRequirements", [])

        skill_ko_dict = {
            skill["id"]: skill for skill in skill_ko_list if skill.get("id")
        }
        skill_ja_dict = {
            skill["id"]: skill for skill in skill_ja_list if skill.get("id")
        }

        for skill_en in skill_en_list:
            req_id = skill_en.get("id")
            if not req_id:
                continue

            skill_ko = skill_ko_dict.get(req_id, {})
            skill_ja = skill_ja_dict.get(req_id, {})

            require_level = skill_en.get("level", 0)
            name_en = skill_en.get("name")
            name_ko = skill_ko.get("name")
            name_ja = skill_ja.get("name")

            rows.append(
                (
                    req_id,
                    hideout_level_id,
                    require_level,
                    name_en,
                    name_ko,
                    name_ja,
                )
            )

    return rows


def v3_hideout_trader_require_process(item_en):
    rows = []

    levels_en = item_en.get("levels", [])

    for level_en in levels_en:
        level_id = level_en.get("id")
        trader_list = level_en.get("traderRequirements", [])

        for trader in trader_list:
            id = trader["id"]
            trader_id = trader["trader"].get("id")
            trader_level = trader["value"]

            rows.append((id, level_id, trader_id, trader_level))
    return rows


def v3_hideout_station_require_process(item_en):
    rows = []

    levels_en = item_en.get("levels", [])

    for level_en in levels_en:
        level_id = level_en.get("id")
        station_list = level_en.get("stationLevelRequirements", [])

        for station in station_list:
            id = station["id"]
            station_level = station["level"]
            require_master_id = station["station"].get("id")

            rows.append((id, level_id, require_master_id, station_level))
    return rows


def v3_hideout_item_require_process(item_en):
    rows = []

    levels_en = item_en.get("levels", [])

    for level_en in levels_en:
        level_id = level_en.get("id")
        item_list = level_en.get("itemRequirements", [])

        for item_en in item_list:
            id = item_en.get("id")
            quantity = item_en.get("quantity")
            attributes = item_en.get("attributes", [])
            first_attr = attributes[0] if attributes else {}

            in_raid = str(first_attr.get("value", "false")).lower() == "true"

            item_id = item_en.get("item", {}).get("id")

            rows.append((id, level_id, item_id, quantity, in_raid))

    return rows


def v3_hideout_craft_process(station_en):
    craft_rows = []
    require_rows = []

    crafts = station_en.get("crafts", [])
    levels = station_en.get("levels", [])

    level_id_map = {
        level.get("level"): level.get("id")
        for level in levels
        if level.get("level") is not None and level.get("id")
    }

    for craft in crafts:
        craft_id = craft.get("id")
        if not craft_id:
            continue

        craft_level = craft.get("level")
        hideout_level_id = level_id_map.get(craft_level)
        if not hideout_level_id:
            continue

        duration = craft.get("duration", 0)

        reward_item = craft.get("rewardItems", [{}])[0]
        reward_item_id = reward_item.get("item", {}).get("id")
        reward_quantity = reward_item.get("quantity", 0)

        craft_rows.append(
            (
                craft_id,
                hideout_level_id,
                reward_item_id,
                duration,
                reward_quantity,
            )
        )

        for idx, req in enumerate(craft.get("requiredItems", [])):
            item_id = req.get("item", {}).get("id")
            quantity = req.get("quantity", 0)

            if not item_id:
                continue

            require_rows.append(
                (
                    f"{craft_id}-{idx}",
                    craft_id,
                    item_id,
                    quantity,
                )
            )

    return craft_rows, require_rows


def v3_hideout_bonus_process(item_en, item_ko, item_ja):
    rows = []

    levels_en = item_en.get("levels", [])
    levels_ko = item_ko.get("levels", [])
    levels_ja = item_ja.get("levels", [])

    level_ko_dict = {l["id"]: l for l in levels_ko if l.get("id")}
    level_ja_dict = {l["id"]: l for l in levels_ja if l.get("id")}

    for level_en in levels_en:
        level_id = level_en.get("id")
        if not level_id:
            continue

        level_ko = level_ko_dict.get(level_id, {})
        level_ja = level_ja_dict.get(level_id, {})

        bonus_en_list = level_en.get("bonuses", [])
        bonus_ko_list = level_ko.get("bonuses", [])
        bonus_ja_list = level_ja.get("bonuses", [])

        for idx, bonus_en in enumerate(bonus_en_list):
            bonus_ko = bonus_ko_list[idx] if idx < len(bonus_ko_list) else {}
            bonus_ja = bonus_ja_list[idx] if idx < len(bonus_ja_list) else {}

            bonus_type = bonus_en.get("type")
            name_en = bonus_en.get("name")
            name_ko = bonus_ko.get("name")
            name_ja = bonus_ja.get("name")

            skill_name_en = bonus_en.get("skillName")
            skill_name_ko = bonus_ko.get("skillName")
            skill_name_ja = bonus_ja.get("skillName")

            bonus_value = bonus_en.get("value")
            bonus_id = f"{level_id}-{idx}"

            rows.append(
                (
                    bonus_id,
                    level_id,
                    bonus_type,
                    name_en,
                    name_ko,
                    name_ja,
                    skill_name_en,
                    skill_name_ko,
                    skill_name_ja,
                    bonus_value,
                )
            )

    return rows
