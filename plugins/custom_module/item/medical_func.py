import copy

import pendulum
import json

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

injury_dict = {
    "LightBleeding": {"ko": "가벼운 출혈 치료", "ja": "軽度出血を治療"},
    "HeavyBleeding": {"ko": "과다 출혈 치료", "ja": "重度出血を止血"},
    "Fracture": {"ko": "골절 치료", "ja": "骨折を治療"},
    "Contusion": {
        "ko": "타박상",
        "ja": "脳震とう",  # 뇌진탕(=뇌타박)으로 일본어가 표현된 점 참고
    },
    "Pain": {"ko": "고통 제거", "ja": "痛み"},
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

    info = json.dumps(
        {
            "cures": cures,
            "stim_effects": merged_stim_effects,
            "medical_category": medical_category,
            "use_time": use_time,
            "weight": weight,
            "uses": uses,
            "energy_impact": energy_impact,
            "hydration_impact": hydration_impact,
            "painkiller_duration": update_duration,
            "hitpoints": hitpoints,
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


def get_cures_i18n(cures_en, locale):
    result = []
    for cure in cures_en:
        translations = injury_dict.get(cure)
        if translations:
            result.append(translations.get(locale, cure))  # locale이 없으면 영어 그대로
        else:
            result.append(cure)  # 딕셔너리에 없는 키면 영어 그대로
    return result
