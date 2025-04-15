import json

import pendulum


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
    class_value = item["properties"].get("class")
    durability = item["properties"].get("durability")
    blindness_protection = item["properties"].get("blindnessProtection")

    info = json.dumps({"weight": item.get("weight"),
                       "class_value": class_value,
                       "durability": durability,
                       "material": item["properties"].get("material"),
                       "blindness_protection": blindness_protection})

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
