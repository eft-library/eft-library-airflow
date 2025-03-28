import json

import pendulum


def process_glasses(item):
    """
    glasses 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("gridImageLink")
    class_value = None
    durability = None
    blindness_protection = None
    width = item.get("width")
    height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")

    if item["properties"]["class"] is not None:
        class_value = item["properties"].get("class")
        durability = item["properties"].get("durability")
        blindness_protection = item["properties"].get("blindnessProtection")

    return (
        id,
        name,
        short_name,
        class_value,
        durability,
        blindness_protection,
        image,
        width,
        height,
        update_time,
    )

def new_process_glasses(item):
    """
    glasses 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Glasses"
    image = item.get("gridImageLink")
    image_width = item.get("width")
    image_height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")


    class_value = None
    durability = None
    blindness_protection = None
    if item["properties"]["class"] is not None:
        class_value = item["properties"].get("class")
        durability = item["properties"].get("durability")
        blindness_protection = item["properties"].get("blindnessProtection")


    info = json.dumps({"weight": item.get("weight"), "class_value": class_value, "durability": durability, "blindness_protection": blindness_protection})

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