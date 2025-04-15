import json

import pendulum


def new_process_headwear(item):
    """
    headwear 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Headwear"
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
    durability = None
    deafening = None

    if item["properties"] != {} and item["properties"] is not None:
        class_value = (
            item["properties"].get("class") if item.get("properties") else None
        )
        areas_en = modify_helmet_area(
            item["properties"].get("headZones") if item.get("properties") else None
        )
        ricochet_chance = (
            item["properties"].get("ricochetY") if item.get("properties") else None
        )
        material = item["properties"].get("material") if item.get("properties") else None
        deafening = item["properties"].get("deafening") if item.get("properties") else None
        turn_penalty = item["properties"].get("turnPenalty") if item.get("properties") else None
        ergo_penalty = item["properties"].get("ergoPenalty") if item.get("properties") else None
        speed_penalty = item["properties"].get("speedPenalty") if item.get("properties") else None
        durability = item["properties"].get("durability") if item.get("properties") else None
        ricochet_chance = ricochet_chance_edit(name_en, ricochet_chance)
        ricochet_str_en = ricochet_chance_en(ricochet_chance)
        ricochet_str_kr = ricochet_chance_kr(ricochet_chance)
        areas_kr = check_helmet_area_kr(areas_en)

    info = json.dumps({"weight": item.get("weight"),
                       "class_value": class_value,
                       "durability": durability,
                       "areas_en": areas_en,
                       "areas_kr": areas_kr,
                       "material": material,
                       "deafening": deafening,
                       "turn_penalty": turn_penalty,
                       "ergo_penalty": ergo_penalty,
                       "speed_penalty": speed_penalty,
                       "ricochet_chance": ricochet_chance,
                       "ricochet_str_en": ricochet_str_en,
                       "ricochet_str_kr": ricochet_str_kr
                       })

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

def ricochet_chance_edit(name, ricochet_chance):
    """
    도탄 기회 주입
    """
    if name == "Team Wendy EXFIL Ballistic Helmet (Black)":
        return 0.4
    elif name == "Team Wendy EXFIL Ballistic Helmet (Coyote Brown)":
        return 0.4
    elif name == "DevTac Ronin ballistic helmet":
        return 0.4
    else:
        return ricochet_chance


def ricochet_chance_en(item):
    """
    head wear 도탄 기회 영문
    """
    if item < 0.2:
        return "Low"
    elif item < 0.4:
        return "Medium"
    else:
        return "High"


def ricochet_chance_kr(item):
    """
    head wear 도탄 기회 한글
    """
    if item < 0.2:
        return "낮음"
    elif item < 0.4:
        return "중간"
    else:
        return "높음"


def check_helmet_area_kr(area_list):
    """
    방탄모 보호 부위 한글로 번역
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


def modify_helmet_area(area_list):
    """
    방탄모 명칭 변경
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