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

    properties = item_en.get("properties") or {}
    units = properties.get("units")
    hydration = properties.get("hydration")
    energy = properties.get("energy")
    stim_effects = properties.get("stimEffects")

    update_stime_effects = process_stim_effect(stim_effects)
    result_stim_effects = add_painkiller(update_stime_effects, item_en.get("name"))
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


def process_stim_effect(stim_effects):
    """
    stim effect 효과 추가
    """
    new_effects = stim_effects
    kr_skill = {
        "Intellect": "지력",
        "Attention": "주의력",
        "Stress Resistance": "스트레스 저항력",
        "Endurance": "지구력",
        "Mag Drills": "탄창 훈련",
        "Strength": "근력",
        "Metabolism": "신진대사",
        "Memory": "기억력",
        "Health": "체력",
        "Vitality": "활력",
        "Immunity": "면역력",
        "Perception": "인지능력",
        "Charisma": "카리스마",
    }

    kr_type = {
        "Energy recovery": "에너지 회복",
        "Health regeneration": "체력 재생",
        "HandsTremor": "손 떨림",
        "Hydration recovery": "수분 회복",
        "EnergyRate": "에너지 회복",
        "HydrationRate": "수분 회복",
        "HealthRate": "체력 재생",
    }

    for effects in new_effects:
        if effects["type"] == "Skill" and effects["skillName"] in kr_skill:
            effects["krSkill"] = kr_skill[effects["skillName"]]
        else:
            if effects["type"] in kr_type:
                effects["krSkill"] = kr_type[effects["type"]]

    return new_effects


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
            "krSkill": "진통제",
            "duration": 210,
            "skillName": "Painkiller",
        },
        "Bottle of Tarkovskaya vodka": {
            "type": "Skill",
            "delay": 1,
            "value": 1,
            "krSkill": "진통제",
            "duration": 250,
            "skillName": "Painkiller",
        },
        "Bottle of Fierce Hatchling moonshine": {
            "type": "Skill",
            "delay": 1,
            "value": 1,
            "krSkill": "진통제",
            "duration": 500,
            "skillName": "Painkiller",
        },
    }

    if name in painkiller:
        new_effects.append(painkiller[name])

    return new_effects
