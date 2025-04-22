import json

import pendulum


def v2_rig_process(item_en, item_ko, item_ja):
    """
    rig 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    category = "Rig"
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    weight = item_en.get("weight")
    update_time = pendulum.now("Asia/Seoul")

    properties = item_en.get("properties") or {}

    # 공통 필드 추출
    turn_penalty = properties.get("turnPenalty")
    ergo_penalty = properties.get("ergoPenalty")
    speed_penalty = properties.get("speedPenalty")
    material = properties.get("material")

    # 클래스 있는 경우 추가 정보 추출
    class_value = properties.get("class")
    zones = None
    capacity = None
    durability = None

    if class_value:
        zones = {
            "zones_en": item_en.get("properties").get("zones"),
            "zones_ko": item_ko.get("properties").get("zones"),
            "zones_ja": item_ja.get("properties").get("zones"),
        }
        capacity = properties.get("capacity")
        durability = properties.get("durability")

    info = json.dumps(
        {
            "weight": weight,
            "class_value": class_value,
            "zones": zones,
            "turn_penalty": turn_penalty,
            "ergo_penalty": ergo_penalty,
            "material": material,
            "speed_penalty": speed_penalty,
            "durability": durability,
            "capacity": capacity,
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


def v2_armor_vest_process(item_en, item_ko, item_ja):
    """
    armor vest 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    category = "ArmorVest"
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    update_time = pendulum.now("Asia/Seoul")
    weight = item_en.get("weight")

    properties = item_en.get("properties") or {}

    # 공통 필드 추출
    turn_penalty = properties.get("turnPenalty")
    ergo_penalty = properties.get("ergoPenalty")
    speed_penalty = properties.get("speedPenalty")
    material = properties.get("material")
    zones = None
    durability = None

    class_value = properties.get("class")
    if class_value:
        zones = {
            "zones_en": item_en.get("properties").get("zones"),
            "zones_ko": item_ko.get("properties").get("zones"),
            "zones_ja": item_ja.get("properties").get("zones"),
        }
        durability = properties.get("durability")

    info = json.dumps(
        {
            "weight": weight,
            "class_value": class_value,
            "durability": durability,
            "material": material,
            "turn_penalty": turn_penalty,
            "ergo_penalty": ergo_penalty,
            "speed_penalty": speed_penalty,
            "zones": zones,
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
