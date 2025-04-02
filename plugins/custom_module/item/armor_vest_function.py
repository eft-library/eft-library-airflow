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
    durability = armor_vest_durability(name_en)
    areas_en = item["properties"].get("zones")

    info = json.dumps({"weight": item.get("weight"),
                       "class_value": item["properties"].get("class"),
                       "durability": durability,
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


def armor_vest_durability(name):
    """
    전술조끼 내구성 주입
    """
    body_armors_and_plate_carriers = {
        "NPP KlASS Korund-VM body armor (Black)": 310,
        "LBT-6094A Slick Plate Carrier (Coyote Tan)": 200,
        "LBT-6094A Slick Plate Carrier (Olive Drab)": 200,
        "PACA Soft Armor (Rivals Edition)": 100,
        "6B13 assault armor (EMR)": 203,
        "6B13 M assault armor (Killa Edition)": 249,
        "BNTI Module-3M body armor": 80,
        "6B2 body armor (Flora)": 128,
        "LBT-6094A Slick Plate Carrier (Black)": 200,
        "NFM THOR Concealable Reinforced Vest body armor": 170,
        "NFM THOR Integrated Carrier body armor": 466,
        "DRD body armor": 120,
        "6B13 M assault armor (Christmas Edition)": 0,
        "PACA Soft Armor": 100,
        "MF-UNTAR body armor": 100,
        "BNTI Gzhel-K body armor": 259,
        "IOTV Gen4 body armor (Full Protection Kit, MultiCam)": 398,
        "6B43 Zabralo-Sh body armor (EMR)": 510,
        "IOTV Gen4 body armor (Assault Kit, MultiCam)": 362,
        "BNTI Zhuk body armor (EMR)": 305,
        "HighCom Trooper TFO body armor (MultiCam)": 180,
        "FORT Redut-M body armor": 350,
        "FORT Defender-2 body armor": 320,
        "Hexatac HPC Plate Carrier (MultiCam Black)": 90,
        "Interceptor OTV body armor (UCP)": 222,
        "NPP KlASS Kora-Kulon body armor (Black)": 128,
        "IOTV Gen4 body armor (High Mobility Kit, MultiCam)": 320,
        "BNTI Kirasa-N body armor": 240,
        "6B13 assault armor (Flora)": 203,
        "5.11 Tactical Hexgrid plate carrier": 100,
        "6B23-1 body armor (EMR)": 206,
        "BNTI Zhuk body armor (Press)": 185,
        "FORT Redut-T5 body armor (Smog)": 496,
        "NPP KlASS Kora-Kulon body armor (EMR)": 128,
        "6B23-2 body armor (Mountain Flora)": 246
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
        if area in parts:
            result.append(parts[area])
    return result
