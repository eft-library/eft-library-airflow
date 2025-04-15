import json

import pendulum

def new_process_armor_vest(item):
    """
    armor vest 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "ArmorVest"
    image = item.get("gridImageLink")
    image_width = item.get("width")
    image_height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")
    durability = item["properties"].get("durability") if item.get("properties") else None
    areas_en = item["properties"].get("zones") if item.get("properties") else None
    material = item["properties"].get("ricochetY") if item.get("properties") else None
    turn_penalty = item["properties"].get("turnPenalty") if item.get("properties") else None
    ergo_penalty = item["properties"].get("ergoPenalty") if item.get("properties") else None
    speed_penalty = item["properties"].get("speedPenalty") if item.get("properties") else None

    info = json.dumps({"weight": item.get("weight"),
                       "class_value": item["properties"].get("class"),
                       "durability": durability,
                       "material": material,
                       "turn_penalty": turn_penalty,
                       "ergo_penalty": ergo_penalty,
                       "speed_penalty": speed_penalty,
                       "areas_en": item["properties"].get("zones"),
                       "areas_kr": armor_vest_areas_kr(areas_en)})

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



def armor_vest_areas_kr(areas_en):
    """
    방탄조끼 보호 부위 한글
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
