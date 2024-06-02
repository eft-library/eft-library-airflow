import pendulum

weapon_graphql = """
{
  items {
    id
    name
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
    weapon_id = item.get("id")
    weapon_name = item.get("name")
    weapon_short_name = check_short_name(weapon_name, item.get("shortName"))
    weapon_img = item.get("image512pxLink")
    weapon_original_category = (
        item["category"].get("name") if item.get("category") else None
    )
    weapon_category = check_weapon_category(weapon_short_name, weapon_original_category)
    weapon_carliber = (
        item["properties"].get("caliber") if item.get("properties") else None
    )
    weapon_default_ammo = (
        item["properties"]["defaultAmmo"].get("name")
        if item.get("properties") and item["properties"].get("defaultAmmo")
        else None
    )
    weapon_modes_en = (
        item["properties"].get("fireModes") if item.get("properties") else None
    )
    weapon_fire_rate = (
        item["properties"].get("fireRate") if item.get("properties") else None
    )
    weapon_ergonomics = (
        item["properties"].get("defaultErgonomics") if item.get("properties") else None
    )
    weapon_recoil_vertical = (
        item["properties"].get("defaultRecoilVertical")
        if item.get("properties")
        else None
    )
    weapon_recoil_horizontal = (
        item["properties"].get("defaultRecoilHorizontal")
        if item.get("properties")
        else None
    )
    weapon_update_time = pendulum.now("Asia/Seoul")
    weapon_modes_kr = gun_modes_kr(weapon_modes_en)

    return (
        weapon_id,
        weapon_name,
        weapon_short_name,
        weapon_img,
        weapon_category,
        weapon_carliber,
        weapon_default_ammo,
        weapon_modes_en,
        weapon_modes_kr,
        weapon_fire_rate,
        weapon_ergonomics,
        weapon_recoil_vertical,
        weapon_recoil_horizontal,
        weapon_update_time,
    )


def process_knife(item):
    """
    knife 데이터 가공
    """
    knife_id = item.get("id")
    knife_name = item.get("name")
    knife_short_name = item.get("shortName")
    knife_image = item.get("image512pxLink")
    knife_category = item["category"].get("name") if item.get("category") else None
    knife_slash_damage = (
        item["properties"].get("slashDamage") if item.get("properties") else None
    )
    knife_stab_damage = (
        item["properties"].get("stabDamage") if item.get("properties") else None
    )
    knife_hit_radius = (
        item["properties"].get("hitRadius") if item.get("properties") else None
    )
    knife_update_time = pendulum.now("Asia/Seoul")

    return (
        knife_id,
        knife_name,
        knife_short_name,
        knife_image,
        knife_category,
        knife_slash_damage,
        knife_stab_damage,
        knife_hit_radius,
        knife_update_time,
    )


def process_throwable(item):
    """
    throwable 데이터 가공
    """
    throwable_id = item.get("id")
    throwable_name = item.get("name")
    throwable_short_name = item.get("shortName")
    throwable_image = item.get("image512pxLink")
    throwable_category = item["category"].get("name") if item.get("category") else None
    throwable_fuse = item["properties"].get("fuse") if item.get("properties") else None
    throwable_min_explosion_distance = (
        item["properties"].get("minExplosionDistance")
        if item.get("properties")
        else None
    )
    throwable_max_explosion_distance = (
        item["properties"].get("maxExplosionDistance")
        if item.get("properties")
        else None
    )
    throwable_fragments = (
        item["properties"].get("fragments") if item.get("properties") else None
    )
    throwable_update_time = pendulum.now("Asia/Seoul")

    return (
        throwable_id,
        throwable_name,
        throwable_short_name,
        throwable_image,
        throwable_category,
        throwable_fuse,
        throwable_min_explosion_distance,
        throwable_max_explosion_distance,
        throwable_fragments,
        throwable_update_time,
    )


def process_head_phone(item):
    """
    head_phone 데이터 가공
    """
    head_phone_id = item.get("id")
    head_phone_name = item.get("name")
    head_phone_short_name = item.get("shortName")
    head_phone_image = item.get("image512pxLink")
    head_phone_update_time = pendulum.now("Asia/Seoul")

    return (
        head_phone_id,
        head_phone_name,
        head_phone_short_name,
        head_phone_image,
        head_phone_update_time,
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
