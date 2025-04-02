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


    class_value = None
    durability = None
    blindness_protection = None
    if item["properties"]["class"] is not None:
        class_value = item["properties"].get("class")
        durability = get_durability(name_en)
        blindness_protection = item["properties"].get("blindnessProtection")


    info = json.dumps({"class_value": class_value,
                       "durability": durability,
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

def get_durability(name):
    if name == 'Oakley SI Batwolf glasses':
        return 20
    if name == 'NPP KlASS Condor glasses':
        return 25

    return 0
