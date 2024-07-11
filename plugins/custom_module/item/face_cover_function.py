import pendulum

def process_face_cover(item):
    """
    face cover 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    weight = item.get("weight")
    image = item.get("image512pxLink")
    update_time = pendulum.now("Asia/Seoul")
    class_value = None
    areas_en = None
    areas_kr = None
    ricochet_chance = None
    ricochet_str_en = None
    ricochet_str_kr = None

    if item["properties"] != {}:
        class_value = (
            item["properties"].get("class") if item.get("properties") else None
        )
        areas_en = modify_helmet_area(
            item["properties"].get("headZones") if item.get("properties") else None
        )
        areas_kr = check_helmet_area_kr(areas_en)
        ricochet_chance = (
            item["properties"].get("ricochetY") if item.get("properties") else None
        )
        ricochet_chance = ricochet_chance_edit(name, ricochet_chance)
        ricochet_str_en = ricochet_chance_en(ricochet_chance)
        ricochet_str_kr = ricochet_chance_kr(ricochet_chance)

    return (
        id,
        name,
        short_name,
        class_value,
        areas_en,
        areas_kr,
        ricochet_chance,
        weight,
        image,
        ricochet_str_en,
        ricochet_str_kr,
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