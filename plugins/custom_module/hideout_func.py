import json
import pendulum


def generate_hideout_stations_graphql(lang: str) -> str:
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
          name
          gridImageLink
        }}
        quantity
        count
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
        requirementType
        value
        trader {{
          name
          imageLink
        }}
        compareMethod
      }}
      stationLevelRequirements {{
        id
        level
        station {{
          id
          name
          imageLink
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
          name
          width
          height
          gridImageLink
        }}
        quantity
      }}
      duration
      requiredItems {{
        item {{
          id
          name
          gridImageLink
          width
          height
        }}
        quantity
      }}
    }}
  }}
}}
"""


def v2_hideout_master_process(item_en, item_ko, item_ja):
    """
    hideout master 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    level_ids = get_level_ids(item_en.get("levels"))
    update_time = pendulum.now("Asia/Seoul")

    return (item_id, json.dumps(name), level_ids, update_time)


def get_level_ids(levels):
    """
    level id list 추출
    """
    level_ids = []
    for level in levels:
        level_ids.append(level["id"])

    return level_ids


def v2_hideout_level_process(item_en):
    """
    hideout level 가공
    """
    item_id = item_en.get("id")
    level = item_en.get("level")
    construction_time = item_en.get("constructionTime")
    update_time = pendulum.now("Asia/Seoul")

    return (item_id, level, construction_time, update_time)


def v2_hideout_item_require_process(level_id, item_en, item_ko, item_ja):
    """
    hideout item_require 가공
    """
    update_time = pendulum.now("Asia/Seoul")
    lev_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    quantity = item_en.get("quantity")
    count = item_en.get("count")

    item_info = item_en["item"]
    image = item_info.get("gridImageLink")
    item_id = item_info.get("id")

    return (
        lev_id,
        level_id,
        json.dumps(name),
        quantity,
        count,
        image,
        item_id,
        update_time,
    )
