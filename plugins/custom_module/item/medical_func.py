import copy

import pendulum
import json

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


injury_dict = {
    "LightBleeding": {
        "en": "Light bleeding treatment",
        "ko": "가벼운 출혈 치료",
        "ja": "軽度出血を治療",
    },
    "HeavyBleeding": {
        "en": "Heavy bleeding treatment",
        "ko": "과다 출혈 치료",
        "ja": "重度出血を止血",
    },
    "Fracture": {"en": "Fracture treatment", "ko": "골절 치료", "ja": "骨折を治療"},
    "Contusion": {"en": "Contusion", "ko": "타박상", "ja": "脳震とう"},
    "Pain": {"en": "Pain", "ko": "고통 제거", "ja": "痛み"},
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
}


def v2_medical_process(item_en, item_ko, item_ja):
    """
    medical 데이터 가공
    """

    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    category = "Medical"
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    weight = item_en.get("weight")
    update_time = pendulum.now("Asia/Seoul")
    url_mapping = item_en.get("normalizedName")
    medical_category = item_en["category"].get("name")

    en_properties = item_en.get("properties") or {}
    ko_properties = item_ko.get("properties") or {}
    ja_properties = item_ja.get("properties") or {}

    cures = {
        "en": en_properties.get("cures", []),
        "ko": get_cures_i18n(en_properties.get("cures", []), "ko"),
        "ja": get_cures_i18n(en_properties.get("cures", []), "ja"),
    }

    energy_impact = en_properties.get("energyImpact")
    hydration_impact = en_properties.get("hydrationImpact")
    painkiller_duration = en_properties.get("painkillerDuration")
    hitpoints = en_properties.get("hitpoints")
    use_time = en_properties.get("useTime")
    uses = en_properties.get("uses")

    update_duration = (
        update_painkiller_duration(painkiller_duration, item_en.get("name"))
        if painkiller_duration is not None
        else None
    )
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

    painkiller_add_stim_effects = add_painkiller(
        item_en.get("name"), merged_stim_effects
    )
    buff = []
    de_buff = []
    advantage = []
    malus = []

    for effect in painkiller_add_stim_effects:
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
            "cures": cures,
            "stim_effects": painkiller_add_stim_effects,
            "medical_category": medical_category,
            "use_time": use_time,
            "weight": weight,
            "uses": uses,
            "energy_impact": energy_impact,
            "hydration_impact": hydration_impact,
            "painkiller_duration": update_duration,
            "hitpoints": hitpoints,
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


def update_painkiller_duration(duration, name):
    """
    진통제 지속시간 수정
    """

    update_list = {
        "Analgin painkillers": 95,
        "Augmentin antibiotic pills": 155,
        "Ibuprofen painkillers": 290,
        "Vaseline balm": 350,
        "Golden Star balm": 370,
        "Morphine injector": 305,
    }

    if name in update_list:
        return update_list[name]

    return duration


def add_painkiller(name_en, stim_effects):
    """
    진통제 추가
    """
    pain_list = {
        "L1 (Norepinephrine) injector": {
            "duration": 120,
            "skill_name_en": "Painkiller",
            "skill_name_ko": "진통제",
            "skill_name_ja": "鎮痛剤",
            "type": "painkillerDuration",
            "delay": 0,
            "value": 0,
            "chance": 1,
        },
        "Trimadol stimulant injector": {
            "duration": 185,
            "skill_name_en": "Painkiller",
            "skill_name_ko": "진통제",
            "skill_name_ja": "鎮痛剤",
            "type": "painkillerDuration",
            "delay": 0,
            "value": 0,
            "chance": 1,
        },
        "Adrenaline injector": {
            "duration": 65,
            "skill_name_en": "Painkiller",
            "skill_name_ko": "진통제",
            "skill_name_ja": "鎮痛剤",
            "type": "painkillerDuration",
            "delay": 0,
            "value": 0,
            "chance": 1,
        },
        "Propital regenerative stimulant injector": {
            "duration": 245,
            "skill_name_en": "Painkiller",
            "skill_name_ko": "진통제",
            "skill_name_ja": "鎮痛剤",
            "type": "painkillerDuration",
            "delay": 0,
            "value": 0,
            "chance": 1,
        },
    }

    if name_en in pain_list:
        stim_effects.append(pain_list[name_en])

    return stim_effects


def get_cures_i18n(cures_en, locale):
    result = []
    for cure in cures_en:
        translations = injury_dict.get(cure)
        if translations:
            result.append(translations.get(locale, cure))  # locale이 없으면 영어 그대로
        else:
            result.append(cure)  # 딕셔너리에 없는 키면 영어 그대로
    return result
