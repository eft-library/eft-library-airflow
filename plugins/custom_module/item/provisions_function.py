import copy
import json
import pendulum


def v2_provisions_process(item_en, item_ko, item_ja):
    """
    provisions 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    category = "Provisions"
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    weight = item_en.get("weight")
    update_time = pendulum.now("Asia/Seoul")

    en_properties = item_en.get("properties") or {}
    ko_properties = item_ko.get("properties") or {}
    ja_properties = item_ja.get("properties") or {}

    units = en_properties.get("units")
    hydration = en_properties.get("hydration")
    energy = en_properties.get("energy")
    merged_stim_effects = []

    for se_en, se_ko, se_ja in zip(
        en_properties.get("stimEffects", []),
        ko_properties.get("stimEffects", []),
        ja_properties.get("stimEffects", []),
    ):
        merged = copy.deepcopy(se_en)
        merged["skill_name_en"] = se_en.get("skillName", "")
        merged["skill_name_ko"] = se_ko.get("skillName", "")
        merged["skill_name_ja"] = se_ja.get("skillName", "")
        merged.pop("skillName", None)
        merged_stim_effects.append(merged)

    result_stim_effects = add_painkiller(merged_stim_effects, item_en.get("name"))
    info = json.dumps(
        {
            "stim_effects": result_stim_effects,
            "weight": weight,
            "units": units,
            "hydration": hydration,
            "energy": energy,
        }
    )

    return (
        item_id,
        json.dumps(name),
        category,
        info,
        image,
        image_width,
        image_height,
        update_time,
    )


def add_painkiller(stim_effects, name):
    """
    진통제 추가
    """
    new_effects = stim_effects

    painkiller = {
        "Bottle of Dan Jackiel whiskey": {
            "type": "Skill",
            "delay": 1,
            "value": 1,
            "duration": 210,
            "skill_name_kr": "진통제",
            "skill_name_ja": "鎮痛剤",
            "skill_name_en": "Painkiller",
        },
        "Bottle of Tarkovskaya vodka": {
            "type": "Skill",
            "delay": 1,
            "value": 1,
            "duration": 250,
            "skill_name_kr": "진통제",
            "skill_name_ja": "鎮痛剤",
            "skill_name_en": "Painkiller",
        },
        "Bottle of Fierce Hatchling moonshine": {
            "type": "Skill",
            "delay": 1,
            "value": 1,
            "duration": 500,
            "skill_name_kr": "진통제",
            "skill_name_ja": "鎮痛剤",
            "skill_name_en": "Painkiller",
        },
    }

    if name in painkiller:
        new_effects.append(painkiller[name])

    return new_effects
