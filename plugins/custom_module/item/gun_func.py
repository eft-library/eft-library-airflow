import json
import pendulum


def v2_gun_process(item_en, item_ko, item_ja):
    """
    gun 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    category = "Gun"
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    weight = item_en.get("weight")
    image_height = item_en.get("height")
    update_time = pendulum.now("Asia/Seoul")
    gun_category = item_en["category"].get("name") if item_en.get("category") else None
    properties = item_en.get("properties")

    if properties:
        caliber = properties.get("caliber")
        default_ammo = (
            properties.get("defaultAmmo").get("name")
            if properties.get("defaultAmmo") is not None
            else None
        )
        modes = {
            "modes_en": item_en.get("properties").get("fireModes"),
            "modes_ko": item_ko.get("properties").get("fireModes"),
            "modes_ja": item_ja.get("properties").get("fireModes"),
        }
        fire_rate = properties.get("fireRate")
        ergonomics = properties.get("defaultErgonomics")
        recoil_vertical = properties.get("defaultRecoilVertical")
        recoil_horizontal = properties.get("defaultRecoilHorizontal")
        allowed_ammo = properties.get("allowedAmmo")
    else:
        caliber = None
        default_ammo = None
        modes = None
        fire_rate = None
        ergonomics = None
        recoil_vertical = None
        recoil_horizontal = None
        allowed_ammo = None

    info = json.dumps(
        {
            "weight": weight,
            "caliber": caliber,
            "default_ammo": default_ammo,
            "modes": modes,
            "gun_category": gun_category,
            "fire_rate": fire_rate,
            "ergonomics": ergonomics,
            "allowed_ammo": allowed_ammo,
            "recoil_vertical": recoil_vertical,
            "recoil_horizontal": recoil_horizontal,
        }
    )

    return (
        item_id,
        json.dumps(name),
        category,
        info,
        image,
        image_width,
        image_height,
        update_time,
    )
