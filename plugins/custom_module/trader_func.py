import copy
import json
import pendulum


def generate_trader_graphql(lang: str) -> str:
    return f"""
{{
  traders(lang: {lang}) {{
    id
    name
    imageLink
    barters {{
      level
      requiredItems {{
        item {{
          id
          name
          gridImageLink
        }}
        quantity
      }}
      rewardItems {{
        item {{
          id
          name
          gridImageLink
        }}
        quantity
      }}
    }}
  }}
}}
"""


def v2_trader_process(item_en, item_ko, item_ja):
    """
    trader 가공
    """
    npc_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    trader_image = item_en.get("imageLink")
    merged_barters = []

    for b_en, b_ko, b_ja in zip(
        item_en.get("barters"), item_ko.get("barters"), item_ja.get("barters")
    ):
        merged_barter = copy.deepcopy(b_en)  # 기본 구조는 en 기준 복사

        # requiredItems 병합
        for i, (r_en, r_ko, r_ja) in enumerate(
            zip(b_en["requiredItems"], b_ko["requiredItems"], b_ja["requiredItems"])
        ):
            item = r_en["item"]
            item["name_en"] = r_en["item"]["name"]
            item["name_ko"] = r_ko["item"]["name"]
            item["name_ja"] = r_ja["item"]["name"]
            del item["name"]  # 기존 name 제거
            merged_barter["requiredItems"][i]["item"] = item

        # rewardItems 병합
        for i, (r_en, r_ko, r_ja) in enumerate(
            zip(b_en["rewardItems"], b_ko["rewardItems"], b_ja["rewardItems"])
        ):
            item = r_en["item"]
            item["name_en"] = r_en["item"]["name"]
            item["name_ko"] = r_ko["item"]["name"]
            item["name_ja"] = r_ja["item"]["name"]
            del item["name"]
            merged_barter["rewardItems"][i]["item"] = item

        merged_barters.append(merged_barter)

    update_time = pendulum.now("Asia/Seoul")

    return npc_id, name, trader_image, json.dumps(merged_barters), update_time
