import pendulum
import json


def v2_medical_process(item_en, item_ko, item_ja):
    """
    medical 데이터 가공
    """
    check_item = check_morphine(item_en)

    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    add_painkiller(item_en)
    category = "Medical"
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    weight = item_en.get("weight")
    update_time = pendulum.now("Asia/Seoul")
    medical_category = check_item["category"].get("name")

    en_properties = check_item.get("properties") or {}

    cures = en_properties.get("cures")
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
    stim_effects = en_properties.get("stimEffects")
    buff = get_buff(stim_effects) if stim_effects is not None else None
    debuff = get_debuff(stim_effects) if stim_effects is not None else None

    info = json.dumps(
        {
            "cures": cures,
            "buff": buff,
            "debuff": debuff,
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
        update_time,
    )


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
