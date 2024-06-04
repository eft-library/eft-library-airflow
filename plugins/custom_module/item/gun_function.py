import pendulum


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
    무기 이름 변경하기
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
