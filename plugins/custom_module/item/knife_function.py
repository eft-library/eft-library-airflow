import json

import pendulum


def new_process_knife(item):
    """
    knife 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Knife"
    image = item.get("gridImageLink")
    image_width = item.get("width")
    image_height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")

    info = json.dumps({"slash_damage": item["properties"].get("slashDamage") if item.get("properties") else None,
                       "stab_damage": item["properties"].get("stabDamage") if item.get("properties") else None,
                       "hit_radius": item["properties"].get("hitRadius") if item.get("properties") else None,
                       "gun_category": 'Knife'})

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