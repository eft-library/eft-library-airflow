import pendulum
import json


def process_medical(item):
    """
    medical 데이터 가공
    """
    check_item = check_morphine(item)

    id = check_item.get("id")
    name_en = check_item.get("name")
    name_kr = check_item.get("name")
    short_name = check_item.get("shortName")
    cures_en = check_item["properties"].get("cures")
    cures_kr = None
    if cures_en is not None:
        cures_kr = get_cures_kr(cures_en)
    category = check_item["category"].get("name")
    buff = json.dumps(check_item["properties"].get("stimEffects"))
    debuff = json.dumps(check_item["properties"].get("stimEffects"))
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
        buff if buff is not 'null' else None,
        debuff if debuff is not 'null' else None,
        use_time,
        uses,
        energy_impact,
        hydration_impact,
        update_duration,
        hitpoints,
        image,
        update_time,
    )


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
        "Morphine injector": 305
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
        "chance": 1
      },
      {
        "duration": 0,
        "skillName": None,
        "type": "energyImpact",
        "delay": 0,
        "value": -10,
        "chance": 1
      },
      {
        "duration": 0,
        "skillName": None,
        "type": "hydrationImpact",
        "delay": 0,
        "value": -15,
        "chance": 1
      }
    ]

    if item.get("name") == "Morphine injector":
        del item['properties']['cures']
        del item['properties']['useTime']
        del item['properties']['uses']
        del item['properties']['energyImpact']
        del item['properties']['hydrationImpact']
        del item['properties']['painkillerDuration']
        item['category']['name'] = "Stimulant"
        item['properties']['stimEffects'] = morphine
        return item

    return item
