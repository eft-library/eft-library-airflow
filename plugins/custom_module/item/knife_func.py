import json

import pendulum


def v2_knife_process(item_en, item_ko, item_ja):
    """
    knife 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    category = "Knife"
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    update_time = pendulum.now("Asia/Seoul")

    info = json.dumps(
        {
            "slash_damage": (
                item_en["properties"].get("slashDamage")
                if item_en.get("properties")
                else None
            ),
            "stab_damage": (
                item_en["properties"].get("stabDamage")
                if item_en.get("properties")
                else None
            ),
            "hit_radius": (
                item_en["properties"].get("hitRadius")
                if item_en.get("properties")
                else None
            ),
            "weight": item_en.get("weight"),
            "gun_category": "Knife",
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
