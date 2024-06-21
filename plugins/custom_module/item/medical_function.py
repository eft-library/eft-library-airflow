import pendulum
import json


def process_medical(item):
    """
    medical 데이터 가공
    """
    check_item = check_morphine(item)

    id = check_item.get("id")
    name_en = check_item.get("name")
    name_kr = get_name_kr(name_en)
    short_name = check_item.get("shortName")
    cures_en = check_item["properties"].get("cures")
    cures_kr = None
    if cures_en is not None:
        cures_kr = get_cures_kr(cures_en)
    category = check_item["category"].get("name")
    stim_effect = check_item["properties"].get("stimEffects")
    buff = None
    debuff = None
    if stim_effect is not None:
        buff = json.dumps(get_buff(check_item["properties"].get("stimEffects")))
        debuff = json.dumps(get_debuff(check_item["properties"].get("stimEffects")))
    image = check_item.get("image512pxLink")
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

    return (
        id,
        name_en,
        name_kr,
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
        update_time,
    )


def get_name_kr(name):
    """
    name kr 값 반환
    """
    kr_list = {
        "AFAK tactical individual first aid kit": "AFAK 개인 전술 응급 치료 키트",
        "AI-2 medkit": "AI-2 응급 치료 키트",
        "Aluminum splint": "Aluminum splint 알루미늄 부목",
        "Analgin painkillers": "Analgin painkillers 아날긴 진통제",
        "Army bandage": "Army bandage 군용 붕대",
        "Aseptic bandage": "Aseptic bandage 무균 붕대",
        "Augmentin antibiotic pills": "Augmentin 아목시실린 항생제",
        "CALOK-B hemostatic applicator": "CALOK-B 지혈제 주입기",
        "Car first aid kit": "Car 차량용 응급 치료 키트",
        "CAT hemostatic tourniquet": "CAT 지혈대",
        "CMS surgical kit": "CMS 휴대용 수술 키트",
        "Esmarch tourniquet": "Esmarch 에스마르호 지혈대",
        "Golden Star balm": "Golden Star 골든스타 연고",
        "Grizzly medical kit": "Grizzly 응급 치료 키트",
        "Ibuprofen painkillers": "Ibuprofen painkillers 이부프로펜 진통제",
        "IFAK individual first aid kit": "IFAK 개인용 응급 치료 키트",
        "Immobilizing splint": "Immobilizing splint 고정용 부목",
        "Salewa first aid kit": "Salewa 응급 치료 키트",
        "Surv12 field surgical kit": "Surv12 야전 수술 키트",
        "Vaseline balm": "Vaseline 바셀린 연고",
        '"Obdolbos 2" cocktail injector': '"Obdolbos 2" 칵테일 주사기',
        '"Obdolbos" cocktail injector': '"Obdolbos" 칵테일 주사기',
        "2A2-(b-TG) stimulant injector": "2A2-(b-TG) stimulant injector",
        "3-(b-TG) stimulant injector": "3-(b-TG) 자극제 주사기",
        "Adrenaline injector": "Adrenaline 아드레날린 주사기",
        "AHF1-M stimulant injector": "AHF1-M 자극제 주사기",
        "eTG-change regenerative stimulant injector": "eTG-change 재생 자극제 주사기",
        "L1 (Norepinephrine) injector": "L1 (노르에피네프린) 주사기",
        "M.U.L.E. stimulant injector": "M.U.L.E. 자극제 주사기",
        "Meldonin injector": "Meldonin 멜도닌 주사기",
        "Morphine injector": "Morphine 모르핀 주사기",
        "P22 (Product 22) stimulant injector": "P22 자극제 주사기",
        "Perfotoran (Blue Blood) stimulant injector": "Perfotoran (Blue Blood) stimulant injector",
        "PNB (Product 16) stimulant injector": "PNB (Product 16) stimulant injector",
        "Propital regenerative stimulant injector": "Propital 프로피탈 재생 자극제 주사기",
        "SJ1 TGLabs combat stimulant injector": "SJ1 TGLabs 전투 자극제 주사기",
        "SJ12 TGLabs combat stimulant injector": "SJ12 TGLabs combat stimulant injector",
        "SJ6 TGLabs combat stimulant injector": "SJ6 TGLabs 전투 자극제 주사기",
        "SJ9 TGLabs combat stimulant injector": "SJ9 TGLabs 전투 자극제 주사기",
        "Trimadol stimulant injector": "Trimadol stimulant injector",
        "xTG-12 antidote injector": "xTG-12 antidote injector",
        "Zagustin hemostatic drug injector": "Zagustin 자구스틴 지혈제",
    }

    if name in kr_list:
        return kr_list[name]

    return name


def get_buff(stim_effect):
    """
    buff 분류
    """

    buff_list = []

    for effect in stim_effect:
        if effect.get("type") == "Antidote":
            buff_list.append(effect)
        elif effect.get("type") == "Body temperature" and effect.get("value") < 0:
            buff_list.append(effect)
        elif effect.get("type") == "Energy recovery" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "Health regeneration" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "Hydration recovery" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "Max stamina" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "Stamina recovery" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "Weight limit" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "energyImpact" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "hydrationImpact" and effect.get("value") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "painkillerDuration" and effect.get("duration") > 0:
            buff_list.append(effect)
        elif effect.get("type") == "Stops and prevents bleedings":
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
    buff 분류
    """

    debuff_list = []

    for effect in stim_effect:
        if effect.get("type") == "Body temperature" and effect.get("value") > 0:
            debuff_list.append(effect)
        elif effect.get("type") == "Hands tremor":
            debuff_list.append(effect)
        elif effect.get("type") == "Pain":
            debuff_list.append(effect)
        elif effect.get("type") == "Tunnel effect":
            debuff_list.append(effect)
        elif effect.get("type") == "Energy recovery" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "Health regeneration" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "Hydration recovery" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "Max stamina" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "Stamina recovery" and effect.get("value") < 0:
            debuff_list.append(effect)
        elif effect.get("type") == "Weight limit" and effect.get("value") < 0:
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
    }

    kr_result = []

    for heal in cures:
        if heal in kr_list:
            kr_result.append(kr_list[heal])

    return kr_result


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
