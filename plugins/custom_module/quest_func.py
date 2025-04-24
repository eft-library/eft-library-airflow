import copy
import json
import pendulum


def generate_quest_graphql(lang: str) -> str:
    return f"""
{{
  tasks(lang: {lang}) {{
    id
    name
    normalizedName
    kappaRequired
    lightkeeperRequired
    wikiLink
    trader {{
      id
    }}
    taskRequirements {{
      task {{
        id
        name
        normalizedName
      }}
    }}
    objectives {{
      id
      type
      description
      ... on TaskObjectiveQuestItem {{
        questItem {{
          id
          name
          normalizedName
          gridImageLink
        }}
        count
      }}
      ... on TaskObjectiveItem {{
        items {{
          id
          name
          normalizedName
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
          normalizedName
          gridImageLink
        }}
        count
        quantity
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

    merged_finish_rewards = copy.deepcopy(item_en["finishRewards"])
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
        json.dumps(merged_objectives),
        wiki_url,
        json.dumps(merged_finish_rewards),
        url_mapping,
        update_time,
    )
