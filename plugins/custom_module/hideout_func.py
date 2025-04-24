import copy
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
          normalizedName
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
          normalizedName
          gridImageLink
        }}
        quantity
      }}
      duration
      requiredItems {{
        item {{
          id
          name
          normalizedName
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
    quantity = item_en.get("quantity")
    count = item_en.get("count")

    item_info = item_en["item"] or {}
    image = item_info.get("gridImageLink")
    item_id = item_info.get("id")
    name = {
        "en": item_en["item"].get("name"),
        "ko": item_ko["item"].get("name"),
        "ja": item_ja["item"].get("name"),
    }

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


def v2_hideout_trader_process(level_id, item_en, item_ko, item_ja):
    """
    hideout trader 가공
    """
    update_time = pendulum.now("Asia/Seoul")
    item_id = item_en.get("id")
    value = item_en.get("value")
    trader = item_en["trader"] or {}

    image = trader.get("imageLink")
    name = {
        "en": item_en["trader"].get("name"),
        "ko": item_ko["trader"].get("name"),
        "ja": item_ja["trader"].get("name"),
    }

    return (
        item_id,
        level_id,
        json.dumps(name),
        value,
        image,
        update_time,
    )


def v2_hideout_station_require_process(level_id, item_en, item_ko, item_ja):
    """
    hideout station_require 가공
    """
    lev_id = item_en.get("id")
    level = item_en.get("level")
    station = item_en["station"]
    station_master_id = station.get("id")
    name = {
        "en": item_en["station"].get("name"),
        "ko": item_ko["station"].get("name"),
        "ja": item_ja["station"].get("name"),
    }
    update_time = pendulum.now("Asia/Seoul")

    return (lev_id, level_id, level, json.dumps(name), station_master_id, update_time)


def v2_hideout_skill_require_process(level_id, item_en, item_ko, item_ja):
    """
    hideout skill require 가공
    """
    update_time = pendulum.now("Asia/Seoul")
    lev_id = item_en.get("id")
    level = item_en.get("level")
    name = {
        "en": item_en["skill"].get("name"),
        "ko": item_ko["skill"].get("name"),
        "ja": item_ja["skill"].get("name"),
    }
    return (lev_id, level_id, level, json.dumps(name), update_time)


def v2_hideout_bonus_process(level_id, item_en, item_ko, item_ja):
    """
    hideout bonus 가공
    """
    update_time = pendulum.now("Asia/Seoul")
    type = item_en.get("type")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    value = item_en.get("value")
    skill_name = {
        "en": item_en.get("skillName"),
        "ko": item_ko.get("skillName"),
        "ja": item_ja.get("skillName"),
    }

    return (
        level_id,
        type,
        json.dumps(name),
        value,
        json.dumps(skill_name),
        update_time,
    )


def v2_hideout_crafts_process(item_en, item_ko, item_ja):
    """
    hideout crafts 가공
    """
    update_time = pendulum.now("Asia/Seoul")
    lev_id = item_en.get("id")
    name = {
        "en": item_en.get("rewardItems")[0].get("item").get("name"),
        "ko": item_ko.get("rewardItems")[0].get("item").get("name"),
        "ja": item_ja.get("rewardItems")[0].get("item").get("name"),
    }
    station_id = item_en["station"].get("id") if item_en.get("station") else None
    level = item_en.get("level")
    reward_item = item_en.get("rewardItems")[0].get("item")

    width = reward_item.get("width")
    height = reward_item.get("height")
    duration = item_en.get("duration")
    image = reward_item.get("gridImageLink")
    quantity = item_en.get("rewardItems")[0].get("quantity")
    reward_item_id = reward_item.get("id")
    merged_required_items = []

    for req_en, req_ko, req_ja in zip(
        item_en.get("requiredItems", []),
        item_ko.get("requiredItems", []),
        item_ja.get("requiredItems", []),
    ):
        merged_req = copy.deepcopy(req_en)  # 영어 기준 구조 복사
        item = req_en["item"]

        # 다국어 이름 병합
        item["name_en"] = req_en["item"].get("name", "")
        item["name_ko"] = req_ko["item"].get("name", "")
        item["name_ja"] = req_ja["item"].get("name", "")
        del item["name"]

        merged_req["item"] = item
        merged_required_items.append(merged_req)

    return (
        lev_id,
        f"{station_id}-{level}",
        level,
        width,
        height,
        json.dumps(name),
        duration,
        json.dumps(merged_required_items),
        image,
        quantity,
        reward_item_id,
        update_time,
    )
