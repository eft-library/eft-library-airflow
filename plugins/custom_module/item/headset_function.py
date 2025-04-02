import json

import pendulum




def new_process_headset(item):
    """
    headset 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Headset"
    image = item.get("gridImageLink")
    distance_modifier = (
        item["properties"].get("distanceModifier")
        if item.get("properties")
        else None
    )
    info = json.dumps({"distance_modifier": distance_modifier})
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
        update_time,
    )