import copy

import pendulum
import json
from datetime import datetime


def price_list_process(item_en, item_ko, item_ja):
    """
    일단 이름 먼저 합치기
    """
    id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    width = item_en.get("width")
    height = item_en.get("height")
    category = categorize_item(item_en.get("category"))
    historicalPrices = item_en.get("historicalPrices")
    image = item_en.get("gridImageLink")
    merged_sell_for = []

    for s_en, s_ko, s_ja in zip(
        item_en.get("sellFor", []),
        item_ko.get("sellFor", []),
        item_ja.get("sellFor", []),
    ):
        merged = copy.deepcopy(s_en)  # 영어 데이터를 기본으로 복사

        vendor = s_en.get("vendor", {})
        vendor["name_en"] = s_en["vendor"].get("name", "")
        vendor["name_ko"] = s_ko["vendor"].get("name", "")
        vendor["name_ja"] = s_ja["vendor"].get("name", "")
        vendor.pop("name", None)  # 기존 name 제거

        merged["vendor"] = vendor
        merged_sell_for.append(merged)

    return {
        "id": id,
        "name": name,
        "width": width,
        "height": height,
        "category": category,
        "historicalPrices": historicalPrices,
        "sellFor": merged_sell_for,
        "gridImageLink": image,
    }


def v2_item_price_process(item):
    """
    price 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    image = item.get("gridImageLink")
    trader = item.get("sellFor")
    category = item.get("category")
    width = item.get("width")
    height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        json.dumps(name),
        image,
        json.dumps(trader),
        category,
        width,
        height,
        update_time,
    )


def process_price_history(id, item, price_type):
    """
    price history 가공
    """
    price = item.get("price")
    price_time = datetime.utcfromtimestamp(int(item.get("timestamp")) / 1000)
    execute_time = pendulum.now("Asia/Seoul")

    return (id, price, price_type, price_time, execute_time)


def categorize_item(origin_category):
    loot_categories = {
        "Battery",
        "Building material",
        "Compass",
        "Electronics",
        "Flyer",
        "Fuel",
        "Household goods",
        "Info",
        "Jewelry",
        "Lubricant",
        "Medical supplies",
        "Multitools",
        "Repair Kits",
        "Special item",
        "Tool",
        "Map",
        "Other",
        "Planting Kits",
        "Portable Range Finder",
    }

    mods_categories = {
        "Pistol grip",
        "Magazine",
        "Comb. muzzle device",
        "Comb. tact. device",
        "Compact reflex sight",
        "Cylinder Magazine",
        "Gas block",
        "Handguard",
        "Foregrip",
        "Mount",
        "Assault scope",
        "Reflex sight",
        "Scope",
        "Special scope",
        "Thermal Vision",
        "Stock",
        "Flashlight",
        "Auxiliary Mod",
        "Barrel",
        "Bipod",
        "Charging handle",
        "Flashhider",
        "Ironsight",
        "Silencer",
        "Spring Driven Cylinder",
        "Receiver",
        "UBGL",
    }

    weapon_categories = {
        "Assault rifle",
        "Grenade launcher",
        "Marksman rifle",
        "Machinegun",
        "Sniper rifle",
        "Throwable weapon",
        "Knife",
        "Assault carbine",
        "SMG",
        "Shotgun",
        "Handgun",
        "Revolver",
    }

    provisions_categories = {"Drink", "Food"}

    container_categories = {
        "Ammo container",
        "Common container",
        "Locking container",
        "Random Loot Container",
    }

    wearables_categories = {
        "Chest rig",
        "Backpack",
        "Arm Band",
        "Armor",
        "Armor Plate",
        "Armored equipment",
        "Face Cover",
        "Headphones",
        "Headwear",
        "Night Vision",
        "Vis. observ. device",
    }

    meds_categories = {"Drug", "Medical item", "Medikit", "Stimulant"}

    keys_categories = {"Keycard", "Mechanical Key"}

    ammo_categories = {"Ammo"}

    if origin_category in loot_categories:
        return "LOOT"
    elif origin_category in mods_categories:
        return "Mods"
    elif origin_category in weapon_categories:
        return "Weapon"
    elif origin_category in provisions_categories:
        return "Provisions"
    elif origin_category in container_categories:
        return "Container"
    elif origin_category in wearables_categories:
        return "Wearables"
    elif origin_category in meds_categories:
        return "Meds"
    elif origin_category in keys_categories:
        return "Keys"
    elif origin_category in ammo_categories:
        return "Ammo"

    return "ETC"


def merge_item_price_data(pvp_data, pve_data):
    """
    pvp, pve 데이터 가공
    """
    merged_data = []
    # 두 데이터 리스트를 병합 (ID로 매칭)
    pve_items = {item["id"]: item for item in pve_data}

    for pvp_item in pvp_data:
        pve_item = pve_items.get(pvp_item["id"])
        # 가격 정보 통합
        merged_item = {
            "id": pvp_item["id"],
            "name": pvp_item["name"],
            "gridImageLink": pvp_item["gridImageLink"],
            "sellFor": {
                "pvp_trader": (
                    mapping_trader(pvp_item["sellFor"]) if pvp_item["sellFor"] else None
                ),
                "pve_trader": (
                    mapping_trader(pve_item["sellFor"]) if pve_item["sellFor"] else None
                ),
            },
            "width": pvp_item["width"],
            "height": pvp_item["height"],
            "pvpHistoricalPrices": pvp_item["historicalPrices"],
            "pveHistoricalPrices": pve_item["historicalPrices"],
            "category": pvp_item["category"],
        }

        merged_data.append(merged_item)

    return merged_data


def mapping_trader(sell_for):
    """
    trader 정보 연결
    """
    npc_data = {
        "Peacekeeper": {
            "npc_id": "5935c25fb3acc3127c3d8cd9",
            "npc_name_en": "Peace Keeper",
            "npc_name_kr": "피스키퍼",
            "npc_image": "https://assets.tarkov.dev/5935c25fb3acc3127c3d8cd9.webp",
        },
        "Mechanic": {
            "npc_id": "5a7c2eca46aef81a7ca2145d",
            "npc_name_en": "Mechanic",
            "npc_name_kr": "메카닉",
            "npc_image": "https://assets.tarkov.dev/5a7c2eca46aef81a7ca2145d.webp",
        },
        "Prapor": {
            "npc_id": "54cb50c76803fa8b248b4571",
            "npc_name_en": "Prapor",
            "npc_name_kr": "프라퍼",
            "npc_image": "https://assets.tarkov.dev/54cb50c76803fa8b248b4571.webp",
        },
        "Skier": {
            "npc_id": "58330581ace78e27b8b10cee",
            "npc_name_en": "Skier",
            "npc_name_kr": "스키어",
            "npc_image": "https://assets.tarkov.dev/58330581ace78e27b8b10cee.webp",
        },
        "Fence": {
            "npc_id": "579dc571d53a0658a154fbec",
            "npc_name_en": "Fence",
            "npc_name_kr": "펜스",
            "npc_image": "https://assets.tarkov.dev/579dc571d53a0658a154fbec.webp",
        },
        "Therapist": {
            "npc_id": "54cb57776803fa99248b456e",
            "npc_name_en": "Therapist",
            "npc_name_kr": "테라피스트",
            "npc_image": "https://assets.tarkov.dev/54cb57776803fa99248b456e.webp",
        },
        "Jaeger": {
            "npc_id": "JAEGER",
            "npc_name_en": "Jaeger",
            "npc_name_kr": "예거",
            "npc_image": "https://assets.tarkov.dev/5c0647fdd443bc2504c2d371.webp",
        },
        "Ragman": {
            "npc_id": "5ac3b934156ae10c4430e83c",
            "npc_name_en": "Ragman",
            "npc_name_kr": "래그맨",
            "npc_image": "https://assets.tarkov.dev/5ac3b934156ae10c4430e83c.webp",
        },
        "Ref": {
            "npc_id": "6617beeaa9cfa777ca915b7c",
            "npc_name_en": "Ref",
            "npc_name_kr": "레프",
            "npc_image": "https://assets.tarkov.dev/6617beeaa9cfa777ca915b7c.webp",
        },
        "Flea Market": {
            "npc_id": "FLEA_MARKET",
            "npc_name_en": "Flea Market",
            "npc_name_kr": "플리마켓",
            "npc_image": "https://image.eftlibrary.com/eftlibrary/tkl_main/fleamarket.webp",
        },
    }

    process_sell = []
    for sell in sell_for:
        new_sell = {
            "price": sell.get("priceRUB"),
            "trader": npc_data.get(sell["vendor"]["name"]),
        }
        process_sell.append(new_sell)

    return process_sell
