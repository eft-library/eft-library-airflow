import json

import pendulum


def new_process_throwable(item):
    """
    throwable 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Throwable"
    image = item.get("gridImageLink")
    image_width = item.get("width")
    image_height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")
    min_explosion_distance = (
        item["properties"].get("minExplosionDistance")
        if item.get("properties")
        else None
    )
    max_explosion_distance = (
        item["properties"].get("maxExplosionDistance")
        if item.get("properties")
        else None
    )
    info = json.dumps({"fragments": item["properties"].get("fragments") if item.get("properties") else None,
                       "fuse": item["properties"].get("fuse") if item.get("properties") else None,
                       "min_explosion_distance": min_explosion_distance,
                       "max_explosion_distance": max_explosion_distance,
                       "gun_categoy": 'Throwable weapon'})

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