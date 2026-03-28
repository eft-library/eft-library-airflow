def generate_hideout_graphql(lang: str) -> str:
    return f"""
{{
  hideoutStations(lang: {lang}) {{
    id
    name
    level
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

    return (master_id, name_en, name_ko, name_ja)


def v3_hideout_level_process(item_en):
    item_id = item_en.get("id")
    level = item_en.get("level")
    construction_time = item_en.get("constructionTime")

    return (item_id, level, construction_time)


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
