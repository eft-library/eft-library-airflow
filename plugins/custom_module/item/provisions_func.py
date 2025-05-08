import copy
import json
import pendulum

status_dict = {
    "HealthRate": {"ko": "체력 재생", "ja": "体力回復"},
    "HandsTremor": {"ko": "손 떨림", "ja": "手の震え"},
    "QuantumTunnelling": {"ko": "터널 효과", "ja": "視野狭窄"},
    "EnergyRate": {"ko": "에너지 회복", "ja": "エネルギー回復"},
    "HydrationRate": {"ko": "수분 회복", "ja": "水分回復"},
    "MaxStamina": {"ko": "최대 스태미나", "ja": "最大スタミナ"},
    "StaminaRate": {"ko": "스태미나 회복", "ja": "スタミナ回復"},
    "Removeallbloodlosses": {
        "ko": "출혈 멈춤 & 추가 출혈 방지",
        "ja": "出血を止める/防ぐ",
    },
    "WeightLimit": {"ko": "무게 제한", "ja": "重量制限"},
    "DamageModifier": {
        "ko": "받은 피해량 (머리 제외)",
        "ja": "受けるダメージが増加(頭部以外)",
    },
    "Antidote": {"ko": "해독제", "ja": "解毒剤"},
    "BodyTemperature": {"ko": "체온", "ja": "体温"},
    "Pain": {"ko": "고통 제거", "ja": "痛み"},
}


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
    url_mapping = item_en.get("normalizedName")
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
        effect_type = se_en.get("type")

        if effect_type in status_dict:
            merged["skill_name_en"] = effect_type
            merged["skill_name_ko"] = status_dict[effect_type]["ko"]
            merged["skill_name_ja"] = status_dict[effect_type]["ja"]
        else:
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
        url_mapping,
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
