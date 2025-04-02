import json

import pendulum


def new_process_loot(item):
    """
    loot 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Loot"
    info = json.dumps({"loot_category": change_category(item["category"].get("name"), name_en) if item.get("category") else None,
                       "weight": item.get("weight"),})
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


def change_category(category, name):
    """
    카테고리 변경
    """
    special_list = [
        "Portable Range Finder",
        "Radio Transmitter",
        "Repair Kits",
        "Compass",
        "Cultist Amulet",
    ]

    jewelry_list = [
        "Battered antique book",
        "Loot Lord plushie",
        'Old firesteel'
    ]

    lubricant_list = [
        'Gunpowder "Eagle"',
        'Gunpowder "Hawk"',
        'Gunpowder "Kite"',
        "Metal fuel tank",
        "Expeditionary fuel tank"
    ]

    if category in special_list:
        return "Special equipment"
    elif name in jewelry_list:
        return "Jewelry"
    elif name in lubricant_list:
        return "Lubricant"

    return category