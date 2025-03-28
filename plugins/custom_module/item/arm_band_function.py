import json

import pendulum


def process_arm_band(item):
    """
    arm_band 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("gridImageLink")
    weight = item.get("weight")
    width = item.get("width")
    height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        weight,
        image,
        width,
        height,
        update_time,
    )

def new_process_arm_band(item):
    """
    arm_band 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Armband"
    info = json.dumps({"weight": item.get("weight")})
    image = item.get("gridImageLink")
    image_width = item.get("width")
    image_height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")

    return (
        item_id,
        name_en,
        category,
        info,
        image,
        image_width,
        image_height,
        update_time
    )