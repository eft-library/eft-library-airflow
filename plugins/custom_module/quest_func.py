import copy
import json
import pendulum


def generate_quest_graphql(lang: str) -> str:
    return f"""
{{
  tasks(lang: {lang}) {{
    id
    name
    kappaRequired
    lightkeeperRequired
    minPlayerLevel
    normalizedName
    wikiLink
    trader {{
      id
      name
    }}
    taskRequirements {{
      task {{
        id
        name
      }}
    }}
    objectives {{
      id
      type
      description
      ... on TaskObjectiveShoot {{
        count
      }}
      ... on TaskObjectiveQuestItem {{
        questItem {{
          id
          name
          gridImageLink
        }}
        count
      }}
      ... on TaskObjectiveItem {{
        items {{
          id
          name
          gridImageLink
        }}
        count
        foundInRaid
      }}
    }}
    finishRewards {{
      items {{
        item {{
          id
          name
          gridImageLink
        }}
        count
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
          name
          imageLink
          normalizedName
        }}
      }}
      offerUnlock {{
        trader {{
          id
          name
          imageLink
          normalizedName
        }}
        item {{
          id
          name
          gridImageLink
          normalizedName
        }}
        level
      }}
      craftUnlock {{
        station {{
          id
          name
        }}
        level
        rewardItems {{
          item {{
            id
            name
            gridImageLink
            normalizedName
          }}
          count
          quantity
        }}
      }}
    }}
  }}
}}
"""


def v2_quest_process(item_en, item_ko, item_ja):
    """
    quest 가공
    """
    id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    url_mapping = item_en.get("normalizedName")
    npc_id = (
        item_en.get("trader").get("id") if item_en.get("trader").get("id") else None
    )
    min_player_level = item_en.get("minPlayerLevel")
    wiki_url = item_en.get("wikiLink")
    lightkeeper_required = item_en.get("lightkeeperRequired")
    kappa_required = item_en.get("kappaRequired")
    update_time = pendulum.now("Asia/Seoul")

    merged_task_requirements = []

    for req_en, req_ko, req_ja in zip(
        item_en.get("taskRequirements", []),
        item_ko.get("taskRequirements", []),
        item_ja.get("taskRequirements", []),
    ):
        merged_req = copy.deepcopy(req_en)
        task = req_en["task"]
        task["name_en"] = req_en["task"].get("name", "")
        task["name_ko"] = req_ko["task"].get("name", "")
        task["name_ja"] = req_ja["task"].get("name", "")
        del task["name"]
        merged_req["task"] = task
        merged_task_requirements.append(merged_req)

    # 기존 finishRewards 복사
    merged_finish_rewards = copy.deepcopy(item_en["finishRewards"])

    # 1. items 병합
    merged_items = []
    for r_en, r_ko, r_ja in zip(
        item_en["finishRewards"]["items"],
        item_ko["finishRewards"]["items"],
        item_ja["finishRewards"]["items"],
    ):
        merged_r = copy.deepcopy(r_en)
        item = r_en["item"]
        item["name_en"] = r_en["item"].get("name", "")
        item["name_ko"] = r_ko["item"].get("name", "")
        item["name_ja"] = r_ja["item"].get("name", "")
        del item["name"]
        merged_r["item"] = item
        merged_items.append(merged_r)

    merged_finish_rewards["items"] = merged_items

    # 2. traderStanding 병합
    if "traderStanding" in item_en["finishRewards"]:
        merged_trader_standing = []
        for r_en, r_ko, r_ja in zip(
            item_en["finishRewards"]["traderStanding"],
            item_ko["finishRewards"]["traderStanding"],
            item_ja["finishRewards"]["traderStanding"],
        ):
            merged_r = copy.deepcopy(r_en)
            trader = r_en["trader"]
            trader["name_en"] = r_en["trader"].get("name", "")
            trader["name_ko"] = r_ko["trader"].get("name", "")
            trader["name_ja"] = r_ja["trader"].get("name", "")
            del trader["name"]
            merged_r["trader"] = trader
            merged_trader_standing.append(merged_r)

        merged_finish_rewards["traderStanding"] = merged_trader_standing

    # 3. offerUnlock 병합
    if "offerUnlock" in item_en["finishRewards"]:
        merged_offer_unlock = []
        for r_en, r_ko, r_ja in zip(
            item_en["finishRewards"]["offerUnlock"],
            item_ko["finishRewards"]["offerUnlock"],
            item_ja["finishRewards"]["offerUnlock"],
        ):
            merged_r = copy.deepcopy(r_en)

            # trader 이름 병합
            trader = r_en["trader"]
            trader["name_en"] = r_en["trader"].get("name", "")
            trader["name_ko"] = r_ko["trader"].get("name", "")
            trader["name_ja"] = r_ja["trader"].get("name", "")
            del trader["name"]
            merged_r["trader"] = trader

            # item 이름 병합
            item = r_en["item"]
            item["name_en"] = r_en["item"].get("name", "")
            item["name_ko"] = r_ko["item"].get("name", "")
            item["name_ja"] = r_ja["item"].get("name", "")
            del item["name"]
            merged_r["item"] = item

            merged_offer_unlock.append(merged_r)

        merged_finish_rewards["offerUnlock"] = merged_offer_unlock

    # 4. craftUnlock 병합
    if "craftUnlock" in item_en["finishRewards"]:
        merged_craft_unlock = []
        for r_en, r_ko, r_ja in zip(
            item_en["finishRewards"]["craftUnlock"],
            item_ko["finishRewards"]["craftUnlock"],
            item_ja["finishRewards"]["craftUnlock"],
        ):
            merged_r = copy.deepcopy(r_en)

            # station 이름 병합
            station = r_en["station"]
            station["name_en"] = r_en["station"].get("name", "")
            station["name_ko"] = r_ko["station"].get("name", "")
            station["name_ja"] = r_ja["station"].get("name", "")
            del station["name"]
            merged_r["station"] = station

            # rewardItems 병합
            merged_reward_items = []
            for i_en, i_ko, i_ja in zip(
                r_en["rewardItems"],
                r_ko["rewardItems"],
                r_ja["rewardItems"],
            ):
                merged_item = copy.deepcopy(i_en)
                item = merged_item["item"]
                item["name_en"] = i_en["item"].get("name", "")
                item["name_ko"] = i_ko["item"].get("name", "")
                item["name_ja"] = i_ja["item"].get("name", "")
                del item["name"]
                merged_item["item"] = item

                # quantity는 그대로 유지됨
                merged_reward_items.append(merged_item)

            merged_r["rewardItems"] = merged_reward_items
            merged_craft_unlock.append(merged_r)

        merged_finish_rewards["craftUnlock"] = merged_craft_unlock

    merged_objectives = []

    for obj_en, obj_ko, obj_ja in zip(
        item_en.get("objectives", []),
        item_ko.get("objectives", []),
        item_ja.get("objectives", []),
    ):
        merged_obj = copy.deepcopy(obj_en)

        merged_obj["description_en"] = obj_en.get("description", "")
        merged_obj["description_ko"] = obj_ko.get("description", "")
        merged_obj["description_ja"] = obj_ja.get("description", "")
        if "description" in merged_obj:
            del merged_obj["description"]

        # questItem
        if "questItem" in obj_en:
            item = obj_en["questItem"]
            item["name_en"] = obj_en["questItem"].get("name", "")
            item["name_ko"] = obj_ko["questItem"].get("name", "")
            item["name_ja"] = obj_ja["questItem"].get("name", "")
            del item["name"]
            merged_obj["questItem"] = item

        # items 리스트
        if "items" in obj_en:
            merged_items = []
            for i_en, i_ko, i_ja in zip(
                obj_en["items"], obj_ko["items"], obj_ja["items"]
            ):
                merged_item = copy.deepcopy(i_en)
                merged_item["name_en"] = i_en.get("name", "")
                merged_item["name_ko"] = i_ko.get("name", "")
                merged_item["name_ja"] = i_ja.get("name", "")
                del merged_item["name"]
                merged_items.append(merged_item)
            merged_obj["items"] = merged_items

        merged_objectives.append(merged_obj)

    return (
        id,
        json.dumps(name),
        npc_id,
        lightkeeper_required,
        kappa_required,
        json.dumps(merged_task_requirements),
        # json.dumps(merged_objectives),
        wiki_url,
        json.dumps(merged_finish_rewards),
        url_mapping,
        min_player_level,
        update_time,
    )
