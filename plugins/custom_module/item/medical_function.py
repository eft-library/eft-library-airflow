import pendulum
import json


def process_medical(item):
    """
    medical 데이터 가공
    """
    check_item = check_morphine(item)

    id = check_item.get("id")
    name_en = check_item.get("name")
    short_name = check_item.get("shortName")
    cures_en = check_item["properties"].get("cures")
    cures_kr = None
    if cures_en is not None:
        cures_kr = get_cures_kr(cures_en)
    category = check_item["category"].get("name")
    stim_effect = check_item["properties"].get("stimEffects")
    add_painkiller(item)
    buff = None
    debuff = None
    if stim_effect is not None:
        new_stim_effect = process_stim_effect(stim_effect)
        buff = json.dumps(get_buff(new_stim_effect))
        debuff = json.dumps(get_debuff(new_stim_effect))
    image = check_item.get("gridImageLink")
    energy_impact = check_item["properties"].get("energyImpact")
    hydration_impact = check_item["properties"].get("hydrationImpact")
    painkiller_duration = check_item["properties"].get("painkillerDuration")
    hitpoints = check_item["properties"].get("hitpoints")
    update_duration = None
    if painkiller_duration is not None:
        update_duration = update_painkiller_duration(painkiller_duration, name_en)
    use_time = check_item["properties"].get("useTime")
    uses = check_item["properties"].get("uses")
    update_time = pendulum.now("Asia/Seoul")
    width = item.get("width")
    height = item.get("height")

    return (
        id,
        name_en,
        short_name,
        cures_en,
        cures_kr,
        category,
        buff if buff is not "null" else None,
        debuff if debuff is not "null" else None,
        use_time,
        uses,
        energy_impact,
        hydration_impact,
        update_duration,
        hitpoints,
        image,
        width,
        height,
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
        "Recoil Control": "반동 제어",
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
        "Antidote": "해독제",
        "BodyTemperature": "체온",
        "DamageModifier": "받은 피해량 (머리 제외)",
        "energyImpact": "에너지",
        "hydrationImpact": "수분",
        "MaxStamina": "최대 스태미나",
        "Pain": "고통",
        "StaminaRate": "스태미나 회복",
        "Removeallbloodlosses": "출혈 멈춤 & 추가 출혈 방지",
        "QuantumTunnelling": "터널 효과",
        "WeightLimit": "무게 제한",
        "painkillerDuration": "진통제",
        "EnergyRate": "에너지 회복",
        "HealthRate": "체력 재생",
        "HandsTremor": "손 떨림",
        "HydrationRate": "수분 회복",
    }

    for effects in new_effects:
        if effects["type"] == "Skill" and effects["skillName"] in kr_skill:
            effects["krSkill"] = kr_skill[effects["skillName"]]
        else:
            if effects["type"] in kr_type:
                effects["krSkill"] = kr_type[effects["type"]]

    return new_effects

def get_buff(stim_effect):
    """
    buff 분류
    """

    buff_list = []

    for effect in stim_effect:
        if effect.get("type") == "Antidote":
            buff_list.append(effect)
        elif effect.get("type") == "BodyTemperature" and effect.get("value") < 0:
            buff_list.append(effect)
        elif effect.get("type") == "EnergyRate" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "HealthRate" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "HydrationRate" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "MaxStamina" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "StaminaRate" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "WeightLimit" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "energyImpact" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "hydrationImpact" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "painkillerDuration" and effect.get("duration") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "Removeallbloodlosses":
            buff_list.append(effect)
        elif effect.get("type") == "Skill":
            if effect.get("skillName") == "Health" and effect.get("value") > 0:
                buff_list.append(effect)
            elif effect.get("skillName") == "Strength" and effect.get("value") > 0:
                buff_list.append(effect)
            elif effect.get("skillName") == "Vitality" and effect.get("value") > 0:
                buff_list.append(effect)
            elif effect.get("skillName") == "Metabolism" and effect.get("value") > 0:
                buff_list.append(effect)
            elif effect.get("skillName") == "Endurance" and effect.get("value") > 0:
                buff_list.append(effect)
            elif (
                effect.get("skillName") == "Recoil Control" and effect.get("value") > 0
            ):
                buff_list.append(effect)
            elif (
                effect.get("skillName") == "Stress Resistance"
                and effect.get("value") > 0
            ):
                buff_list.append(effect)
            elif effect.get("skillName") == "Perception" and effect.get("value") > 0:
                buff_list.append(effect)
            elif effect.get("skillName") == "Immunity" and effect.get("value") > 0:
                buff_list.append(effect)
            elif effect.get("skillName") == "Attention" and effect.get("value") > 0:
                buff_list.append(effect)
            elif effect.get("skillName") == "Intellect" and effect.get("value") > 0:
                buff_list.append(effect)
            elif effect.get("skillName") == "Charisma" and effect.get("value") > 0:
                buff_list.append(effect)

    return buff_list


def get_debuff(stim_effect):
    """
    debuff 분류
    """

    debuff_list = []

    for effect in stim_effect:
        if effect.get("type") == "BodyTemperature" and effect.get("value") > 0:
            debuff_list.append(effect)
        elif effect.get("type") == "DamageModifier":
            debuff_list.append(effect)
        elif effect.get("type") == "HandsTremor":
            debuff_list.append(effect)
        elif effect.get("type") == "Pain":
            debuff_list.append(effect)
        elif effect.get("type") == "QuantumTunnelling":
            debuff_list.append(effect)
        elif effect.get("type") == "EnergyRate" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "HealthRate" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "HydrationRate" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "MaxStamina" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "StaminaRate" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "WeightLimit" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "energyImpact" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "hydrationImpact" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "painkillerDuration" and effect.get("duration") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "Skill":
            if effect.get("skillName") == "Health" and effect.get("value") < 0:
                debuff_list.append(effect)
            elif effect.get("skillName") == "Strength" and effect.get("value") < 0:
                debuff_list.append(effect)
            elif effect.get("skillName") == "Vitality" and effect.get("value") < 0:
                debuff_list.append(effect)
            elif effect.get("skillName") == "Metabolism" and effect.get("value") < 0:
                debuff_list.append(effect)
            elif effect.get("skillName") == "Endurance" and effect.get("value") < 0:
                debuff_list.append(effect)
            elif (
                effect.get("skillName") == "Recoil Control" and effect.get("value") < 0
            ):
                debuff_list.append(effect)
            elif (
                effect.get("skillName") == "Stress Resistance"
                and effect.get("value") < 0
            ):
                debuff_list.append(effect)
            elif effect.get("skillName") == "Perception" and effect.get("value") < 0:
                debuff_list.append(effect)
            elif effect.get("skillName") == "Immunity" and effect.get("value") < 0:
                debuff_list.append(effect)
            elif effect.get("skillName") == "Attention" and effect.get("value") < 0:
                debuff_list.append(effect)
            elif effect.get("skillName") == "Intellect" and effect.get("value") < 0:
                debuff_list.append(effect)
            elif effect.get("skillName") == "Charisma" and effect.get("value") < 0:
                debuff_list.append(effect)

    return debuff_list


def get_cures_kr(cures):
    """
    cures kr 값 반환
    """

    kr_list = {
        "Pain": "고통 제거",
        "Contusion": "뇌진탕 제거",
        "LightBleeding": "가벼운 출혈 제거",
        "HeavyBleeding": "깊은 출혈 제거",
        "Fracture": "골절 제거",
        "EnergyRate": "에너지 회복",
        "HydrationRate": "수분 회복",
        "HealthRate": "체력 재생",
        "HandsTremor": "손 떨림"
    }

    kr_result = []

    for heal in cures:
        if heal in kr_list:
            kr_result.append(kr_list[heal])

    return kr_result


def add_painkiller(item):
    """
    진통제 추가
    """
    pain_list = {
        "L1 (Norepinephrine) injector": {
            "duration": 120,
            "skillName": None,
            "type": "painkillerDuration",
            "delay": 0,
            "value": 0,
            "chance": 1,
        },
        "Trimadol stimulant injector": {
            "duration": 185,
            "skillName": None,
            "type": "painkillerDuration",
            "delay": 0,
            "value": 0,
            "chance": 1,
        },
        "Adrenaline injector": {
            "duration": 65,
            "skillName": None,
            "type": "painkillerDuration",
            "delay": 0,
            "value": 0,
            "chance": 1,
        },
        "Propital regenerative stimulant injector": {
            "duration": 245,
            "skillName": None,
            "type": "painkillerDuration",
            "delay": 0,
            "value": 0,
            "chance": 1,
        },
    }

    if item.get("name") in pain_list:
        item["properties"].get("stimEffects").append(pain_list[item.get("name")])


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


def check_morphine(item):
    """
    morphine은 drug에서 주사기로 변경
    처음에 값 자체를 받아서 수정하는 것으로
    """
    morphine = [
        {
            "duration": 305,
            "skillName": None,
            "type": "painkillerDuration",
            "delay": 0,
            "value": 0,
            "chance": 1,
        },
        {
            "duration": 0,
            "skillName": None,
            "type": "energyImpact",
            "delay": 0,
            "value": -10,
            "chance": 1,
        },
        {
            "duration": 0,
            "skillName": None,
            "type": "hydrationImpact",
            "delay": 0,
            "value": -15,
            "chance": 1,
        },
    ]

    if item.get("name") == "Morphine injector":
        del item["properties"]["cures"]
        del item["properties"]["useTime"]
        del item["properties"]["uses"]
        del item["properties"]["energyImpact"]
        del item["properties"]["hydrationImpact"]
        del item["properties"]["painkillerDuration"]
        item["category"]["name"] = "Stimulant"
        item["properties"]["stimEffects"] = morphine
        return item

    return item
