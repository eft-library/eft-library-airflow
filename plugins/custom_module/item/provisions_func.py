import copy
import json
import pendulum

status_dict = {
    "Health regeneration": {"ko": "체력 재생", "ja": "体力回復"},
    "Hands tremor": {"ko": "손 떨림", "ja": "手の震え"},
    "Tunnel effect": {"ko": "터널 효과", "ja": "視野狭窄"},
    "Energy recovery": {"ko": "에너지 회복", "ja": "エネルギー回復"},
    "Hydration recovery": {"ko": "수분 회복", "ja": "水分回復"},
    "Max stamina": {"ko": "최대 스태미나", "ja": "最大スタミナ"},
    "Stamina recovery": {"ko": "스태미나 회복", "ja": "スタミナ回復"},
    "Stops and prevents bleedings": {
        "ko": "출혈 멈춤 & 추가 출혈 방지",
        "ja": "出血を止める/防ぐ",
    },
    "Weight limit": {"ko": "무게 제한", "ja": "重量制限"},
    "Damage taken (except the head)": {
        "ko": "받은 피해량 (머리 제외)",
        "ja": "受けるダメージが増加(頭部以外)",
    },
    "Antidote": {"ko": "해독제", "ja": "解毒剤"},
    "Body temperature": {"ko": "체온", "ja": "体温"},
    "Pain": {"ko": "고통 제거", "ja": "痛み"},
}

effect_dict = {
    "Antidote": {
        "is_positive": True,
        "is_use_value": False,
    },
    "Body temperature": {
        "is_positive": False,
        "is_use_value": True,
    },
    "Damage taken (except the head)": {
        "is_positive": False,
        "is_use_value": True,
    },
    "Energy recovery": {
        "is_positive": True,
        "is_use_value": True,
    },
    "energyImpact": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Hands tremor": {
        "is_positive": False,
        "is_use_value": False,
    },
    "Health regeneration": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Hydration recovery": {
        "is_positive": True,
        "is_use_value": True,
    },
    "hydrationImpact": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Max stamina": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Pain": {
        "is_positive": False,
        "is_use_value": False,
    },
    "painkillerDuration": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Attention": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Charisma": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Endurance": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Health": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Immunity": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Intellect": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Metabolism": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Perception": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Recoil Control": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Strength": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Stress Resistance": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Vitality": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Stamina recovery": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Stops and prevents bleedings": {
        "is_positive": True,
        "is_use_value": False,
    },
    "Tunnel effect": {
        "is_positive": False,
        "is_use_value": True,
    },
    "Weight limit": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Mag Drills": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Memory": {
        "is_positive": True,
        "is_use_value": True,
    },
    "Contusion": {
        "is_positive": True,
        "is_use_value": False,
    },
    "LightBleeding": {
        "is_positive": True,
        "is_use_value": False,
    },
    "HeavyBleeding": {
        "is_positive": True,
        "is_use_value": False,
    },
    "Fracture": {
        "is_positive": True,
        "is_use_value": False,
    },
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
    buff = []
    de_buff = []
    advantage = []
    malus = []

    for effect in result_stim_effects:
        effect_info = effect_dict.get(effect["skill_name_en"])
        value = effect.get("value", 0)

        if not effect_info:
            continue  # 정의되지 않은 타입은 무시

        # 1. advantage / malus 분류
        if not effect_info["is_use_value"]:
            if effect_info["is_positive"]:
                advantage.append(effect)
            else:
                malus.append(effect)
        # 2. buff / de_buff 분류
        else:
            if effect_info["is_positive"]:
                if value > 0:
                    buff.append(effect)
                elif value < 0:
                    de_buff.append(effect)
            else:
                if value > 0:
                    de_buff.append(effect)
                elif value < 0:
                    buff.append(effect)

    info = json.dumps(
        {
            "stim_effects": result_stim_effects,
            "weight": weight,
            "units": units,
            "hydration": hydration,
            "energy": energy,
            "buff": buff,
            "de_buff": de_buff,
            "advantage": advantage,
            "malus": malus,
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
            "skill_name_ko": "진통제",
            "skill_name_ja": "鎮痛剤",
            "skill_name_en": "Painkiller",
        },
        "Bottle of Tarkovskaya vodka": {
            "type": "Skill",
            "delay": 1,
            "value": 1,
            "duration": 250,
            "skill_name_ko": "진통제",
            "skill_name_ja": "鎮痛剤",
            "skill_name_en": "Painkiller",
        },
        "Bottle of Fierce Hatchling moonshine": {
            "type": "Skill",
            "delay": 1,
            "value": 1,
            "duration": 500,
            "skill_name_ko": "진통제",
            "skill_name_ja": "鎮痛剤",
            "skill_name_en": "Painkiller",
        },
    }

    if name in painkiller:
        new_effects.append(painkiller[name])

    return new_effects
