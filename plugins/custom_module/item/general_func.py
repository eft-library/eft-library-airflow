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
    url_mapping = item_en.get("normalizedName")
    category = "Rig"
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    weight = item_en.get("weight")
    update_time = pendulum.now("Asia/Seoul")

    properties = item_en.get("properties") or {}
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
        url_mapping,
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
    url_mapping = item_en.get("normalizedName")
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
        url_mapping,
        update_time,
    )


def v2_headset_process(item_en, item_ko, item_ja):
    """
    headset 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    url_mapping = item_en.get("normalizedName")
    weight = item_en.get("weight")
    category = "Headset"
    image = item_en.get("gridImageLink")
    distance_modifier = (
        item_en["properties"].get("distanceModifier")
        if item_en.get("properties")
        else None
    )
    info = json.dumps({"weight": weight, "distance_modifier": distance_modifier})
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    update_time = pendulum.now("Asia/Seoul")

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


def v2_backpack_process(item_en, item_ko, item_ja):
    """
    backpack 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    category = "Backpack"
    weight = item_en.get("weight")
    url_mapping = item_en.get("normalizedName")

    properties = item_en.get("properties") or {}
    turn_penalty = properties.get("turnPenalty")
    ergo_penalty = properties.get("ergoPenalty")
    speed_penalty = properties.get("speedPenalty")
    capacity = properties.get("capacity")
    grids = properties.get("grids")

    info = json.dumps(
        {
            "weight": weight,
            "capacity": capacity,
            "turn_penalty": turn_penalty,
            "ergo_penalty": ergo_penalty,
            "speed_penalty": speed_penalty,
            "grids": grids,
        }
    )
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    update_time = pendulum.now("Asia/Seoul")

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


def v2_container_process(item_en, item_ko, item_ja):
    """
    container 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    url_mapping = item_en.get("normalizedName")
    category = "Container"
    weight = item_en.get("weight")
    width = item_en.get("width")
    height = item_en.get("height")

    properties = item_en.get("properties") or {}
    capacity = properties.get("capacity")
    grids = properties.get("grids")

    info = json.dumps(
        {
            "width": width,
            "height": height,
            "weight": weight,
            "capacity": capacity,
            "grids": grids,
        }
    )
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    update_time = pendulum.now("Asia/Seoul")

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


def v2_loot_process(item_en, item_ko, item_ja):
    """
    loot 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    category = "Loot"
    loot_category = item_en["category"].get("name") if item_en.get("category") else None
    weight = item_en.get("weight")
    info = json.dumps(
        {
            "loot_category": loot_category,
            "weight": weight,
        }
    )
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    url_mapping = item_en.get("normalizedName")
    update_time = pendulum.now("Asia/Seoul")

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


def v2_arm_band_process(item_en, item_ko, item_ja):
    """
    arm_band 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    url_mapping = item_en.get("normalizedName")
    weight = item_en.get("weight")
    category = "Armband"
    info = json.dumps({"weight": weight})
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    update_time = pendulum.now("Asia/Seoul")

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


def v2_other_process(item_en, item_ko, item_ja):
    """
    other 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    url_mapping = item_en.get("normalizedName")
    weight = item_en.get("weight")
    category = "Other"
    info = json.dumps({"weight": weight})
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    update_time = pendulum.now("Asia/Seoul")

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
