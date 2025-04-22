import json

import pendulum


def v2_headwear_process(item_en, item_ko, item_ja):
    """
    headwear 데이터 가공
    """
    item_en_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    category = "Headwear"
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    update_time = pendulum.now("Asia/Seoul")
    weight = item_en.get("weight")

    properties = item_en.get("properties") or {}
    turn_penalty = properties.get("turnPenalty")
    ergo_penalty = properties.get("ergoPenalty")
    speed_penalty = properties.get("speedPenalty")
    material = properties.get("material")
    deafening = properties.get("deafening")

    class_value = properties.get("class")
    zones = None
    durability = None
    ricochet_result = None

    if class_value:
        zones = {
            "zones_en": item_en.get("properties").get("zones"),
            "zones_ko": item_ko.get("properties").get("zones"),
            "zones_ja": item_ja.get("properties").get("zones"),
        }
        durability = properties.get("durability")
        en_ricochet_chance = properties.get("ricochetY")
        ricochet_chance = ricochet_chance_edit(name_en, en_ricochet_chance)
        ricochet_result = {
            "ricochet_chance_en": ricochet_chance_en(ricochet_chance),
            "ricochet_chance_ko": ricochet_chance_kr(ricochet_chance),
            "ricochet_chance_ja": ricochet_chance_ja(ricochet_chance),
        }

    info = json.dumps(
        {
            "weight": weight,
            "class_value": class_value,
            "durability": durability,
            "zones": zones,
            "material": material,
            "deafening": deafening,
            "turn_penalty": turn_penalty,
            "ergo_penalty": ergo_penalty,
            "speed_penalty": speed_penalty,
            "ricochet_chance": ricochet_result,
        }
    )

    return (
        item_en_id,
        json.dumps(name),
        category,
        info,
        image,
        image_width,
        image_height,
        update_time,
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


def ricochet_chance_en(item_en):
    """
    head wear 도탄 기회 영문
    """
    if item_en < 0.2:
        return "Low"
    elif item_en < 0.4:
        return "Medium"
    else:
        return "High"


def ricochet_chance_kr(item_en):
    """
    head wear 도탄 기회 한글
    """
    if item_en < 0.2:
        return "낮음"
    elif item_en < 0.4:
        return "중간"
    else:
        return "높음"


def ricochet_chance_ja(item_en):
    """
    head wear 도탄 기회 일본
    """
    if item_en < 0.2:
        return "低い"  # 낮음
    elif item_en < 0.4:
        return "中"  # 중간
    else:
        return "高い"  # 높음
