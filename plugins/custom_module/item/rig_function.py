import pendulum


def process_rig(item):
    """
    rig 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    weight = item.get("weight")
    image = item.get("image512pxLink")
    class_value = None
    areas_en = None
    areas_kr = None
    capacity = item["properties"].get("capacity")
    # durability = None
    update_time = pendulum.now("Asia/Seoul")

    if item["properties"]["class"] is not None:
        class_value = item["properties"].get("class")
        areas_en = item["properties"].get("zones")
        areas_kr = rig_areas_kr(areas_en)
        # durability = rig_durability_edit(name)

    return (
        id,
        name,
        short_name,
        weight,
        image,
        class_value,
        areas_en,
        areas_kr,
        # durability,
        capacity,
        update_time,
    )


def rig_durability_edit(name):
    """
    전술조끼 내구성 주입
    """
    plate_carriers = {
        "Eagle Allied Industries MBSS plate carrier (Coyote Brown)": 70,
        "Tasmanian Tiger SK plate carrier (MultiCam Black)": 110,
        "S&S Precision PlateFrame plate carrier (Goons Edition)": 120,
        "WARTECH TV-115 plate carrier (Olive Drab)": 122,
        "WARTECH TV-110 plate carrier (Coyote)": 160,
        "Eagle Industries MMAC plate carrier (Ranger Green)": 144,
        "Shellback Tactical Banshee plate carrier (A-TACS AU)": 152,
        "Ars Arma A18 Skanda plate carrier (MultiCam)": 186,
        "ANA Tactical M1 plate carrier (Olive Drab)": 194,
        "FirstSpear Strandhogg plate carrier (Ranger Green)": 198,
        "ECLiPSE RBAV-AF plate carrier (Ranger Green)": 218,
        "CQC Osprey MK4A plate carrier (Assault, MTP)": 222,
        "Crye Precision AVS plate carrier (Tagilla Edition)": 170,
        "5.11 Tactical TacTec plate carrier (Ranger Green)": 170,
        "Crye Precision CPC plate carrier (Goons Edition)": 230,
        "Ars Arma CPC MOD.1 plate carrier (A-TACS FG)": 240,
        "ANA Tactical M2 plate carrier (Digital Flora)": 206,
        "Crye Precision AVS plate carrier (Ranger Green)": 212,
        "NPP KlASS Bagariy plate carrier (Digital Flora)": 232,
        "6B5-16 Zh-86 Uley armored rig (Khaki)": 160,
        "CQC Osprey MK4A plate carrier (Protection, MTP)": 272,
        "6B3TM-01 armored rig (Khaki)": 86,
        "6B5-15 Zh-86 Uley armored rig (Flora)": 110,
    }

    if name in plate_carriers:
        return plate_carriers[name]

    return 0


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