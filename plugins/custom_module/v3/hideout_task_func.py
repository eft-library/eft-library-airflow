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


# def v3_hideout_skill_require_process(item_en, item_ko, item_ja):
#     lev_id = item_en.get("id")
#     level = item_en.get("level")
#     name_en = item_en.get("name")
#     name_ko = item_ko.get("name")
#     name_ja = item_ja.get("name")
#
#     return (lev_id, level_id, level, name_en, name_ko, name_ja)
