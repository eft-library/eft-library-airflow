import json

import pendulum

def new_process_face_cover(item):
    """
    face_cover 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "FaceCover"
    image = item.get("gridImageLink")
    image_width = item.get("width")
    image_height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")
    areas_kr = None
    ricochet_str_en = None
    ricochet_str_kr = None
    class_value = None
    areas_en = None
    material = None
    turn_penalty = None
    ergo_penalty = None
    speed_penalty = None
    ricochet_chance = None
    durability = get_durability(name_en)

    if item["properties"] is not {} and item["properties"] is not None:
        material = item["properties"].get("ricochetY") if item.get("properties") else None
        turn_penalty = item["properties"].get("turnPenalty") if item.get("properties") else None
        ergo_penalty = item["properties"].get("ergoPenalty") if item.get("properties") else None
        speed_penalty = item["properties"].get("speedPenalty") if item.get("properties") else None
        class_value = (
            item["properties"].get("class") if item.get("properties") else None
        )
        areas_en = modify_face_cover_area(
            item["properties"].get("headZones") if item.get("properties") else None
        )
        ricochet_chance = (
            item["properties"].get("ricochetY") if item.get("properties") else None
        )
        areas_kr = check_face_cover_area_kr(areas_en)
        ricochet_str_en = ricochet_chance_en(ricochet_chance)
        ricochet_str_kr = ricochet_chance_kr(ricochet_chance)

    info = json.dumps({"weight": item.get("weight"),
                       "class_value": class_value,
                       "areas_en": areas_en,
                       "areas_kr": areas_kr,
                       "material": material,
                       "turn_penalty": turn_penalty,
                       "ergo_penalty": ergo_penalty,
                       "speed_penalty": speed_penalty,
                       "ricochet_chance": ricochet_chance,
                       "ricochet_str_en": ricochet_str_en,
                       "ricochet_str_kr": ricochet_str_kr,
                       "durability": durability})

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
    masks = {
        "Death Knight mask": 55,
        "Glorious E lightweight armored mask": 40,
        "Shattered lightweight armored mask": 40,
        "Death Shadow lightweight armored mask": 30,
        "Tagilla's welding mask 'Gorilla'": 40,
        "Tagilla's welding mask 'UBEY'": 40,
        "Tagilla's welding mask 'ZABEY'": 100,
        "Atomic Defense CQCM up armored ballistic mask (Black)": 35,
        "Atomic Defense CQCM ballistic mask (Smile)": 35,
        "Atomic Defense CQCM ballistic mask (Stop Me)": 35,
        "Atomic Defense CQCM ballistic mask (Scars)": 35,
        "Atomic Defense CQCM ballistic mask (Target)": 35,
        "Atomic Defense CQCM ballistic mask (Skull)": 35,
        "Atomic Defense CQCM ballistic mask (Demon)": 35,
        "Atomic Defense CQCM ballistic mask (El Día de Muertos)": 35
    }

    if name in masks:
        return masks[name]

    return None

def ricochet_chance_en(item):
    """
    face cover 도탄 기회 영문
    """
    if item < 0.2:
        return "Low"
    elif item < 0.4:
        return "Medium"
    else:
        return "High"


def ricochet_chance_kr(item):
    """
    face cover 도탄 기회 한글
    """
    if item < 0.2:
        return "낮음"
    elif item < 0.4:
        return "중간"
    else:
        return "높음"


def check_face_cover_area_kr(area_list):
    """
    face cover 보호 부위 한글로 번역
    """
    result = []
    helmet_area_kr = {
        "Head, Top of the head": "윗머리",
        "Head, Nape": "뒷머리",
        "Head, Ears": "귀",
        "Head, Face": "얼굴",
        "Head, Eyes": "눈",
        "Head, Jaws": "턱",
        "Head, Throat": "목 앞쪽",
        "Head, Back Neck": "목 뒤쪽",
    }

    for area in area_list:
        if area in helmet_area_kr:
            result.append(helmet_area_kr[area])
        else:
            result.append("알 수 없는 부위")  # 사전에 없는 경우

    return result


def modify_face_cover_area(area_list):
    """
    face cover 명칭 변경
    :param area:
    :return:
    """
    result = []

    for area in area_list:
        if area == "Head, Neck":
            result.append("Head, Back Neck")
        else:
            result.append(area)
    return result