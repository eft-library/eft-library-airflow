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
    info = json.dumps({})
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