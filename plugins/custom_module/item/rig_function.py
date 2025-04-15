import json

import pendulum


def new_process_rig(item):
    """
    rig 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Rig"
    image = item.get("gridImageLink")
    image_width = item.get("width")
    image_height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")
    turn_penalty = item["properties"].get("turnPenalty") if item.get("properties") else None
    ergo_penalty = item["properties"].get("ergoPenalty") if item.get("properties") else None
    speed_penalty = item["properties"].get("speedPenalty") if item.get("properties") else None
    material = item["properties"].get("ricochetY") if item.get("properties") else None
    class_value = None
    areas_en = None
    areas_kr = None
    capacity = None
    durability = None

    if item["properties"]["class"] is not None:
        class_value = item["properties"].get("class")
        areas_en = item["properties"].get("zones")
        capacity = item["properties"].get("capacity")
        areas_kr = rig_areas_kr(areas_en)
        durability = item["properties"].get("durability")

    info = json.dumps({"weight": item.get("weight"),
                       "class_value": class_value,
                       "areas_en":areas_en,
                       "areas_kr": areas_kr,
                       "turn_penalty": turn_penalty,
                       "ergo_penalty": ergo_penalty,
                       "material": material,
                       "speed_penalty": speed_penalty,
                       "durability": durability,
                       "capacity": capacity})

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

def rig_areas_kr(areas_en):
    """
    전술조끼 보호 부위 한글
    """
    parts = {
        "F. PLATE": "앞쪽 방탄판",
        "FR. PLATE": "앞쪽 방탄판",
        "BCK. PLATE": "뒤쪽 방탄판",
        "L. PLATE": "왼쪽 방탄판",
        "R. PLATE": "오른쪽 방탄판",
        "Thorax": "흉부",
        "Thorax, Upper back": "흉부 - 위쪽 등",
        "Stomach": "복부",
        "Stomach, Lower back": "복부 - 아래쪽 등",
        "Stomach, Left Side": "복부 - 왼쪽 옆구리",
        "Stomach, Right Side": "복부 - 오른쪽 옆구리",
        "Stomach, Groin": "복부 - 골반",
        "Stomach, Buttocks": "복부 - 엉덩이",
        "Head, Throat": "머리 - 목 앞쪽",
        "Head, Neck": "머리 - 목 뒤쪽",
        "Left arm, Shoulder": "왼팔 - 어깨",
        "Right arm, Shoulder": "오른팔 - 어깨",
    }
    result = []
    for area in areas_en:
        if area in parts:
            result.append(parts[area])
    return result