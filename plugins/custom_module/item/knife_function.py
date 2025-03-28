import json

import pendulum


def process_knife(item):
    """
    knife 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("gridImageLink")
    width = item.get("width")
    height = item.get("height")
    category = item["category"].get("name") if item.get("category") else None
    slash_damage = (
        item["properties"].get("slashDamage") if item.get("properties") else None
    )
    stab_damage = (
        item["properties"].get("stabDamage") if item.get("properties") else None
    )
    hit_radius = item["properties"].get("hitRadius") if item.get("properties") else None
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        image,
        category,
        slash_damage,
        stab_damage,
        hit_radius,
        width,
        height,
        update_time,
    )

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
                       "hit_radius": item["properties"].get("hitRadius") if item.get("properties") else None})

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