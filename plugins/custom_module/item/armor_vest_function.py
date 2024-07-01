import pendulum


def process_armor_vest(item):
    """
    armor vest 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    weight = item.get("weight")
    image = item.get("image512pxLink")
    class_value = item["properties"].get("class")
    areas_en = item["properties"].get("zones")
    areas_kr = armor_vest_areas_kr(areas_en)
    durability = armor_vest_durability(name)
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        weight,
        image,
        class_value,
        areas_en,
        areas_kr,
        durability,
        update_time,
    )


def armor_vest_durability(name):
    """
    전술조끼 내구성 주입
    """
    body_armors_and_plate_carriers = {
        "LBT-6094A Slick Plate Carrier (Olive Drab)": 200,
        "LBT-6094A Slick Plate Carrier (Coyote Tan)": 200,
        "LBT-6094A Slick Plate Carrier (Black)": 200,
        "NPP KlASS Kora-Kulon body armor (Digital Flora)": 128,
        "NPP KlASS Kora-Kulon body armor (Black)": 128,
        "6B13 assault armor (Flora)": 203,
        "6B13 assault armor (Digital Flora)": 203,
        "Hexatac HPC Plate Carrier (MultiCam Black)": 90,
        "5.11 Tactical Hexgrid plate carrier": 100,
        "6B2 body armor (Flora)": 128,
        "BNTI Module-3M body armor": 80,
        "PACA Soft Armor": 100,
        "PACA Soft Armor (Rivals Edition)": 100,
        "Interceptor OTV body armor (UCP)": 222,
        "BNTI Zhuk body armor (Press)": 185,
        "BNTI Kirasa-N body armor": 240,
        "6B23-1 body armor (Digital Flora)": 206,
        "6B23-2 body armor (Mountain Flora)": 246,
        "NPP KlASS Korund-VM body armor (Black)": 310,
        "HighCom Trooper TFO body armor (MultiCam)": 180,
        "NFM THOR Concealable Reinforced Vest body armor": 170,
        "MF-UNTAR body armor": 100,
        "DRD body armor": 120,
        "BNTI Gzhel-K body armor": 259,
        "BNTI Zhuk body armor (Digital Flora)": 305,
        "FORT Defender-2 body armor": 320,
        "6B13 M assault armor (Killa Edition)": 249,
        "IOTV Gen4 body armor (Assault Kit, MultiCam)": 362,
        "FORT Redut-M body armor": 350,
        "IOTV Gen4 body armor (High Mobility Kit, MultiCam)": 320,
        "NFM THOR Integrated Carrier body armor": 466,
        "FORT Redut-T5 body armor (Smog)": 496,
        "6B43 Zabralo-Sh body armor (Digital Flora)": 510,
        "IOTV Gen4 body armor (Full Protection Kit, MultiCam)": 398,
    }

    if name in body_armors_and_plate_carriers:
        return body_armors_and_plate_carriers[name]

    return 0


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
        result.append(parts[area])
    return result
