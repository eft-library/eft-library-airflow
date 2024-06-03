import pendulum

weapon_graphql = """
{
  items {
    id
    name
    weight
    shortName
    image512pxLink
    category {
      name
      parent {
        name
      }
    }
    properties {
      ... on ItemPropertiesWeapon {
        caliber
        defaultAmmo {
          name
        }
        fireModes
        fireRate
        defaultErgonomics
        defaultRecoilVertical
        defaultRecoilHorizontal
      }
      ... on ItemPropertiesMelee {
        slashDamage
        stabDamage
        hitRadius
      }
      ... on ItemPropertiesGrenade {
        type
        fuse
        minExplosionDistance
        maxExplosionDistance
        fragments
        contusionRadius
      }
      ... on ItemPropertiesHelmet {
        durability
        class
        headZones
        ricochetY
      }
      ... on ItemPropertiesArmor {
        durability
        class
        zones
      } 
      ... on ItemPropertiesChestRig {
        class
        zones
        capacity
      }
    }
  }
}
"""


def check_category(weapon_list, weapon_category):
    """
    category 별 데이터 변경
    """
    if weapon_category == "Gun":
        return [
            item
            for item in weapon_list
            if item["category"]["parent"]["name"] == "Weapon"
            and item["properties"] != {}
        ]
    elif weapon_category == "Gun image":
        return [
            item
            for item in weapon_list
            if item["category"]["parent"]["name"] == "Weapon"
            and item["properties"] == {}
            and (
                "Default" in item["name"]
                or "Lobaev Arms DVL-10 7.62x51 bolt-action sniper rifle Urbana"
                in item["name"]
                or "Colt M4A1 5.56x45 assault rifle Carbine" in item["name"]
                or "Kalashnikov PKP 7.62x54R infantry machine gun Zenit" in item["name"]
            )
        ]
    elif weapon_category == "Headphones":
        return [
            item for item in weapon_list if item["category"]["name"] == weapon_category
        ]
    elif weapon_category == "Headwear":
        return [
            item
            for item in weapon_list
            if item["category"]["name"] == weapon_category
            and item["name"] != "Maska-1SCh bulletproof helmet (Killa Edition) Default"
            and item["name"] != "Ops-Core FAST MT Super High Cut helmet (Black) RAC"
            and item["name"] != "Wilcox Skull Lock head mount PVS-14"
        ]
    elif weapon_category == "Armor":
        return [
            item
            for item in weapon_list
            if item["category"]["name"] == weapon_category and item["properties"] != {}
        ]
    elif weapon_category == "Chest rig":
        return [
            item
            for item in weapon_list
            if item["category"]["name"] == weapon_category and item["properties"] != {}
        ]
    else:
        return [
            item
            for item in weapon_list
            if item["category"]["name"] == weapon_category and item["properties"] != {}
        ]


def gun_image_change(original_list, image_list):
    """
    총의 경우 이미지를 다른 데이터에서 써야해서 변환하는 과정을 거쳐야 함
    """
    # 이미지 딕셔너리 생성
    image_dict = {item["shortName"][:-8]: item["image512pxLink"] for item in image_list}
    image_dvl_dict = {
        item["shortName"][:-7]: item["image512pxLink"] for item in image_list
    }
    image_pkp_dict = {
        item["shortName"][:-6]: item["image512pxLink"] for item in image_list
    }

    # original_list 수정
    for original_item in original_list:
        name = original_item["shortName"]
        # 하필이면 이름이 중복이라 방법이 없다.
        if original_item["name"] == "Desert Tech MDR 5.56x45 assault rifle":
            original_item["image512pxLink"] = (
                "https://assets.tarkov.dev/5c98bd7386f7740cfb15654e-512.webp"
            )
        elif name in image_dict:
            original_item["image512pxLink"] = image_dict[name]
        elif name in image_dvl_dict:
            original_item["image512pxLink"] = image_dvl_dict[name]
        elif name in image_pkp_dict:
            original_item["image512pxLink"] = image_pkp_dict[name]

    return original_list


def process_gun(item):
    """
    gun 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = check_short_name(name, item.get("shortName"))
    img = item.get("image512pxLink")
    original_category = item["category"].get("name") if item.get("category") else None
    category = check_weapon_category(short_name, original_category)
    carliber = item["properties"].get("caliber") if item.get("properties") else None
    default_ammo = (
        item["properties"]["defaultAmmo"].get("name")
        if item.get("properties") and item["properties"].get("defaultAmmo")
        else None
    )
    modes_en = item["properties"].get("fireModes") if item.get("properties") else None
    fire_rate = item["properties"].get("fireRate") if item.get("properties") else None
    ergonomics = (
        item["properties"].get("defaultErgonomics") if item.get("properties") else None
    )
    recoil_vertical = (
        item["properties"].get("defaultRecoilVertical")
        if item.get("properties")
        else None
    )
    recoil_horizontal = (
        item["properties"].get("defaultRecoilHorizontal")
        if item.get("properties")
        else None
    )
    update_time = pendulum.now("Asia/Seoul")
    modes_kr = gun_modes_kr(modes_en)

    return (
        id,
        name,
        short_name,
        img,
        category,
        carliber,
        default_ammo,
        modes_en,
        modes_kr,
        fire_rate,
        ergonomics,
        recoil_vertical,
        recoil_horizontal,
        update_time,
    )


def process_knife(item):
    """
    knife 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("image512pxLink")
    category = item["category"].get("name") if item.get("category") else None
    slash_damage = (
        item["properties"].get("slashDamage") if item.get("properties") else None
    )
    stab_damage = (
        item["properties"].get("stabDamage") if item.get("properties") else None
    )
    hit_radius = item["properties"].get("hitRadius") if item.get("properties") else None
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        image,
        category,
        slash_damage,
        stab_damage,
        hit_radius,
        update_time,
    )


def process_throwable(item):
    """
    throwable 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("image512pxLink")
    category = item["category"].get("name") if item.get("category") else None
    fuse = item["properties"].get("fuse") if item.get("properties") else None
    min_explosion_distance = (
        item["properties"].get("minExplosionDistance")
        if item.get("properties")
        else None
    )
    max_explosion_distance = (
        item["properties"].get("maxExplosionDistance")
        if item.get("properties")
        else None
    )
    fragments = item["properties"].get("fragments") if item.get("properties") else None
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        image,
        category,
        fuse,
        min_explosion_distance,
        max_explosion_distance,
        fragments,
        update_time,
    )


def process_head_phone(item):
    """
    head_phone 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("image512pxLink")
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        image,
        update_time,
    )


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
    areas_kr = armor_vest_rig_areas_kr(areas_en)
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


def process_rigs(item):
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
    durability = None
    update_time = pendulum.now("Asia/Seoul")

    if item["properties"]["class"] != None:
        class_value = item["properties"].get("class")
        areas_en = item["properties"].get("zones")
        areas_kr = armor_vest_rig_areas_kr(areas_en)
        durability = rig_durability_edit(name)

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
        capacity,
        update_time,
    )


def rig_durability_edit(item):
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
    return plate_carriers[item] if item in plate_carriers else 0


def armor_vest_durability(item):
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
    return (
        body_armors_and_plate_carriers[item]
        if item in body_armors_and_plate_carriers
        else 0
    )


def armor_vest_rig_areas_kr(areas_en):
    """
    방탄조끼, 전술조끼 보호 부위 한글
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


def process_head_wear(item):
    """
    head_wear 데이터 가공
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
    durability = None
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
        durability = durability_edit(name)
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
        durability,
        ricochet_chance,
        weight,
        image,
        ricochet_str_en,
        ricochet_str_kr,
        update_time,
    )


def durability_edit(name):
    """
    내구성 주입
    """
    helmets = {
        "Bomber beanie": 150,
        "Tac-Kek FAST MT helmet (Replica)": 48,
        "TSh-4M-L soft tank crew helmet": 105,
        "Kolpak-1S riot helmet": 45,
        "PSh-97 DJETA riot helmet": 156,
        "ShPM Firefighter helmet": 96,
        "Jack-o'-lantern tactical pumpkin helmet": 40,
        "LShZ lightweight helmet (Olive Drab)": 36,
        "Galvion Caiman Hybrid helmet (Grey)": 60,
        "Diamond Age NeoSteel High Cut helmet (Black)": 72,
        "NFM HJELM helmet (Hellhound Grey)": 78,
        "UNTAR helmet": 45,
        "6B47 Ratnik-BSh helmet (Olive Drab)": 45,
        "6B47 Ratnik-BSh helmet (Digital Flora cover)": 45,
        "SSh-68 steel helmet (Olive Drab)": 54,
        "FORT Kiver-M bulletproof helmet": 63,
        "NPP KlASS Tor-2 helmet (Olive Drab)": 81,
        "SSSh-94 SFERA-S helmet": 135,
        "DevTac Ronin ballistic helmet": 180,
        "MSA ACH TC-2001 MICH Series helmet (Olive Drab)": 30,
        "MSA ACH TC-2002 MICH Series helmet (Olive Drab)": 32,
        "HighCom Striker ACHHC IIIA helmet (Olive Drab)": 36,
        "HighCom Striker ACHHC IIIA helmet (Black)": 36,
        "MSA Gallet TC 800 High Cut combat helmet (Black)": 36,
        "Diamond Age Bastion helmet (Black)": 48,
        "Ops-Core FAST MT Super High Cut helmet (Black)": 48,
        "Ops-Core FAST MT Super High Cut helmet (Urban Tan)": 48,
        "Crye Precision AirFrame helmet (Tan)": 48,
        "Team Wendy EXFIL Ballistic Helmet (Coyote Brown)": 54,
        "Team Wendy EXFIL Ballistic Helmet (Black)": 54,
        "ZSh-1-2M helmet (Olive Drab)": 63,
        "ZSh-1-2M helmet (Black cover)": 63,
        "HighCom Striker ULACH IIIA helmet (Black)": 66,
        "HighCom Striker ULACH IIIA helmet (Desert Tan)": 66,
        "BNTI LShZ-2DTM helmet (Black)": 99,
        "Maska-1SCh bulletproof helmet (Killa Edition)": 108,
        "Maska-1SCh bulletproof helmet (Olive Drab)": 108,
        "Altyn bulletproof helmet (Olive Drab)": 81,
        "Rys-T bulletproof helmet (Black)": 90,
        "Vulkan-5 LShZ-5 bulletproof helmet (Black)": 99,
    }
    return helmets[name] if name in helmets else None


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


def gun_modes_kr(weapon_modes_en):
    """
    weapon 발사모드 한글로 변경
    """
    weapon_modes_kr = []
    for mode in weapon_modes_en:
        if "Single fire" in mode:
            weapon_modes_kr.append("단발")
        if "Full auto" in mode:
            weapon_modes_kr.append("자동")
        if "Burst Fire" in mode:
            weapon_modes_kr.append("점사")
        if "Double-Tap" in mode:
            weapon_modes_kr.append("더블 탭")
        if "Double action" in mode:
            weapon_modes_kr.append("더블 액션")
        if "Semi-auto" in mode:
            weapon_modes_kr.append("반자동")

    return weapon_modes_kr


def check_weapon_category(weapon_short_name, weapon_category):
    """
    weapon category 확인
    """
    special_weapons = ["SP-81", "Green", "Red", "Flare", "Yellow"]
    grenade_weapons = ["MSGL"]
    carbine_weapons = [
        "ADAR 2-15",
        "TX-15 DML",
        'VPO-136 "Vepr-KM"',
        "VPO-209",
        "AK-545",
        "AK-545 Short",
        "RFB",
    ]
    rifle_weapons = ["AS VAL"]

    if weapon_short_name in special_weapons:
        return "Special weapons"
    elif weapon_short_name in grenade_weapons:
        return "Grenade launcher"
    elif weapon_short_name == "MTs-255-12":
        return "Shotgun"
    elif weapon_category == "Revolver":
        return "Handgun"
    elif weapon_short_name in carbine_weapons:
        return "Assault carbine"
    elif weapon_short_name in rifle_weapons:
        return "Assault rifle"
    else:
        return weapon_category


def check_short_name(weapon_name, weapon_short_name):
    """
    mk16, 17 무기 이름을 scar로 변경하기
    """
    if weapon_name == "FN SCAR-L 5.56x45 assault rifle":
        return "FN SCAR-L"
    elif weapon_name == "FN SCAR-L 5.56x45 assault rifle (FDE)":
        return "FN SCAR-L FDE"
    elif weapon_name == "FN SCAR-H 7.62x51 assault rifle":
        return "FN SCAR-H"
    elif weapon_name == "FN SCAR-H 7.62x51 assault rifle (FDE)":
        return "FN SCAR-H FDE"
    elif weapon_name == "SWORD International Mk-18 .338 LM marksman rifle":
        return "Mk-18"
    else:
        return weapon_short_name


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
