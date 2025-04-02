import json
import pendulum


def new_process_provisions(item):
    """
    provisions 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Provisions"
    image = item.get("gridImageLink")
    image_width = item.get("width")
    image_height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")
    stim_effects = (
        item["properties"].get("stimEffects") if item.get("properties") else None
    )
    new_stim_effects = process_stim_effect(stim_effects)
    info = json.dumps({"stim_effects": add_painkiller(new_stim_effects, name_en),
                       "weight": item.get("weight"),
                       "hydration": item["properties"].get("hydration") if item.get("properties") else None,
                       "energy": item["properties"].get("energy") if item.get("properties") else None
                       })

    return (
        item_id,
        name_en,
        category,
        info,
        image,
        image_width,
        image_height,
        update_time
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
