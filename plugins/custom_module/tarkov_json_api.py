import copy
import json
import time
from urllib.request import Request, urlopen


API_BASE_URL = "https://json.tarkov.dev"


def _request_json(path):
    request = Request(
        f"{API_BASE_URL}/{path.lstrip('/')}",
        headers={"Accept": "application/json", "User-Agent": "eft-library-airflow"},
    )
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def _translate(value, translations):
    if isinstance(value, dict):
        return {key: _translate(item, translations) for key, item in value.items()}
    if isinstance(value, list):
        return [_translate(item, translations) for item in value]
    if isinstance(value, str):
        return translations.get(value, value)
    return value


def get_json_data(endpoint, lang="en", game_mode="regular"):
    payload = _request_json(f"{game_mode}/{endpoint}")
    data = payload["data"]
    if lang:
        translations = _request_json(f"{game_mode}/{endpoint}_{lang}").get(
            "data", {}
        )
        data = _translate(data, translations)
    return data


def get_maps(lang="en"):
    return list(get_json_data("maps", lang)["maps"].values())


def _category_data(item, categories):
    category_ids = item.get("categories") or []
    category = categories.get(category_ids[0], {}) if category_ids else {}
    parent = categories.get(category.get("parent"), {})
    return {
        "name": category.get("name"),
        "parent": {"name": parent.get("name")},
    }


def _item_properties(properties):
    properties = copy.deepcopy(properties) if isinstance(properties, dict) else {}
    properties["allowedAmmo"] = [
        {"id": item_id} for item_id in properties.get("allowedAmmo") or []
    ]
    if isinstance(properties.get("defaultAmmo"), str):
        properties["defaultAmmo"] = {"id": properties["defaultAmmo"]}
    if isinstance(properties.get("material"), str):
        properties["material"] = {"name": properties["material"]}
    fire_mode_names = {
        "single": "Single fire",
        "fullauto": "Full auto",
        "burst": "Burst fire",
        "doubleaction": "Double action",
        "doubletap": "Double tap",
        "semiauto": "Semi-automatic",
    }
    properties["fireModes"] = [
        fire_mode_names.get(str(mode).replace("_", "").lower(), mode)
        for mode in properties.get("fireModes") or []
    ]
    return properties


def get_items(lang="en", game_mode="regular"):
    data = get_json_data("items", lang, game_mode)
    categories = data.get("itemCategories", {})
    items = []
    for raw_item in data.get("items", {}).values():
        item = copy.deepcopy(raw_item)
        item["category"] = _category_data(item, categories)
        item["properties"] = _item_properties(item.get("properties"))
        items.append(item)
    return items


def get_item_prices(game_mode="regular"):
    data = get_json_data("items", "en", game_mode)
    traders = get_json_data("traders", "en", game_mode)
    trader_names = {
        trader_id: trader.get("name") for trader_id, trader in traders.items()
    }
    items = []
    price_timestamp = (int(time.time()) // 3600) * 3600 * 1000
    for raw_item in data.get("items", {}).values():
        item = copy.deepcopy(raw_item)
        item["sellFor"] = [
            {
                "priceRUB": price.get("priceRUB"),
                "vendor": {"name": trader_names.get(price.get("trader"))},
            }
            for price in item.get("sellToTrader") or []
        ]
        if item.get("lastLowPrice") is not None:
            item["sellFor"].append(
                {
                    "priceRUB": item["lastLowPrice"],
                    "vendor": {"name": "Flea Market"},
                }
            )
        item["historicalPrices"] = (
            [{"price": item["lastLowPrice"], "timestamp": price_timestamp}]
            if item.get("lastLowPrice") is not None
            else []
        )
        items.append(item)
    return items


def get_quest_items(lang="en", game_mode="regular"):
    return list(get_json_data("tasks", lang, game_mode)["questItems"].values())


def get_bosses(lang="en"):
    mobs = get_json_data("maps", lang)["mobs"].values()
    body_part_names = {
        "head": "head",
        "chest": "thorax",
        "stomach": "stomach",
        "leftarm": "left arm",
        "rightarm": "right arm",
        "leftleg": "left leg",
        "rightleg": "right leg",
    }
    bosses = []
    for mob in mobs:
        boss = copy.deepcopy(mob)
        boss["health"] = [
            {
                "bodyPart": body_part_names.get(
                    str(health.get("id", "")).replace(" ", "").lower(),
                    str(health.get("bodyPart", "")).lower(),
                ),
                "max": health.get("max"),
            }
            for health in mob.get("health", [])
        ]
        boss["equipment"] = [
            {
                "item": {"id": equipment.get("item")},
                "quantity": equipment.get("count", 1),
            }
            for equipment in mob.get("equipment", [])
            if equipment.get("item")
        ]
        bosses.append(boss)
    return bosses


def get_boss_spawn_maps():
    maps = get_json_data("maps", None)["maps"].values()
    return [
        {
            "id": map_data["id"],
            "bosses": [
                {
                    "spawnChance": boss.get("spawnChance", 0),
                    "boss": {"id": boss.get("mob")},
                }
                for boss in map_data.get("bosses", [])
                if boss.get("mob")
            ],
        }
        for map_data in maps
    ]


def _item_requirement(requirement):
    attributes = requirement.get("attributes") or {}
    return {
        "id": requirement.get("id"),
        "item": {"id": requirement.get("item")},
        "quantity": requirement.get("count", 0),
        "attributes": [
            {"type": key, "value": value} for key, value in attributes.items()
        ],
    }


def get_hideout(lang="en"):
    stations_by_id = get_json_data("hideout", lang)
    crafts = get_json_data("crafts", None)
    crafts_by_station = {}
    for craft in crafts:
        product = craft.get("productItem") or {}
        crafts_by_station.setdefault(craft.get("station"), []).append(
            {
                "id": craft.get("id"),
                "station": {"id": craft.get("station")},
                "level": craft.get("level"),
                "rewardItems": [
                    {
                        "item": {"id": product.get("item")},
                        "quantity": product.get("count", 0),
                    }
                ],
                "duration": (craft.get("duration") or 0) / 1000,
                "requiredItems": [
                    {
                        "item": {"id": item.get("item")},
                        "quantity": item.get("count", 0),
                    }
                    for item in craft.get("requiredItems", [])
                ],
            }
        )

    stations = []
    for raw_station in stations_by_id.values():
        station = copy.deepcopy(raw_station)
        for level in station.get("levels", []):
            level["itemRequirements"] = [
                _item_requirement(item)
                for item in level.get("itemRequirements", [])
            ]
            level["traderRequirements"] = [
                {
                    **requirement,
                    "trader": {"id": requirement.get("trader")},
                }
                for requirement in level.get("traderRequirements", [])
            ]
            level["stationLevelRequirements"] = [
                {
                    **requirement,
                    "station": {"id": requirement.get("station")},
                }
                for requirement in level.get("stationLevelRequirements", [])
            ]
            level["skillRequirements"] = [
                {
                    **requirement,
                    "name": requirement.get("skill"),
                    "skill": {"id": requirement.get("skill")},
                }
                for requirement in level.get("skillRequirements", [])
            ]
            level["bonuses"] = [
                {**bonus, "skillName": bonus.get("skill")}
                for bonus in level.get("bonuses", [])
            ]
        station["crafts"] = crafts_by_station.get(station["id"], [])
        stations.append(station)
    return stations


def get_traders(lang="en"):
    traders_by_id = get_json_data("traders", lang)
    barters = get_json_data("barters", None)
    barters_by_trader = {}
    for barter in barters:
        offered_item = barter.get("offeredItem") or {}
        barters_by_trader.setdefault(barter.get("trader"), []).append(
            {
                "id": barter.get("id"),
                "level": barter.get("minTraderLevel"),
                "requiredItems": [
                    {
                        "item": {"id": item.get("item")},
                        "quantity": item.get("count", 0),
                    }
                    for item in barter.get("requiredItems", [])
                ],
                "rewardItems": [
                    {
                        "item": {"id": offered_item.get("item")},
                        "quantity": offered_item.get("count", 0),
                    }
                ],
            }
        )

    traders = []
    for raw_trader in traders_by_id.values():
        trader = copy.deepcopy(raw_trader)
        trader["barters"] = barters_by_trader.get(trader["id"], [])
        traders.append(trader)
    return traders


def _reward_data(rewards, craft_ids):
    rewards = copy.deepcopy(rewards or {})
    rewards["items"] = [
        {
            "item": {"id": reward.get("item")},
            "quantity": reward.get("count", 0),
        }
        for reward in rewards.get("items", [])
    ]
    rewards["traderStanding"] = [
        {**reward, "trader": {"id": reward.get("trader")}}
        for reward in rewards.get("traderStanding", [])
    ]
    rewards["offerUnlock"] = [
        {
            **reward,
            "trader": {"id": reward.get("trader")},
            "item": {"id": reward.get("item")},
        }
        for reward in rewards.get("offerUnlock", [])
    ]
    rewards["craftUnlock"] = [
        {
            **reward,
            "id": craft_ids.get(
                (reward.get("station"), reward.get("level"), reward.get("item"))
            ),
            "station": {"id": reward.get("station")},
            "rewardItems": [
                {
                    "item": {"id": reward.get("item")},
                    "quantity": reward.get("count", 0),
                }
            ],
        }
        for reward in rewards.get("craftUnlock", [])
    ]
    rewards["skillLevelReward"] = [
        {"name": reward.get("skill"), "level": reward.get("level")}
        for reward in rewards.get("skillLevelReward", [])
    ]
    return rewards


def get_tasks(lang="en"):
    tasks_by_id = get_json_data("tasks", lang)["tasks"]
    craft_ids = {
        (craft.get("station"), craft.get("level"), product.get("item")): craft.get(
            "id"
        )
        for craft in get_json_data("crafts", None)
        for product in [craft.get("productItem") or {}]
    }
    tasks = []
    for raw_task in tasks_by_id.values():
        task = copy.deepcopy(raw_task)
        task["trader"] = {"id": task.get("trader")}
        task["taskRequirements"] = [
            {**requirement, "task": {"id": requirement.get("task")}}
            for requirement in task.get("taskRequirements", [])
        ]
        converted_objectives = []
        for raw_objective in task.get("objectives", []):
            objective = copy.deepcopy(raw_objective)
            objective["items"] = [
                {"id": item_id} for item_id in objective.get("items", [])
            ]
            if objective.get("item") and not objective["items"]:
                objective["items"] = [{"id": objective["item"]}]
            if objective.get("questItem"):
                objective["questItem"] = {"id": objective["questItem"]}
            if objective.get("markerItem"):
                objective["markerItem"] = {"id": objective["markerItem"]}
            objective["requiredKeys"] = [
                [{"id": key_id} for key_id in group]
                for group in objective.get("requiredKeys", [])
            ]
            objective["maps"] = [
                {"id": map_id} for map_id in objective.get("maps", [])
            ]
            converted_objectives.append(objective)
        task["objectives"] = converted_objectives
        task["finishRewards"] = _reward_data(
            task.get("finishRewards"), craft_ids
        )
        tasks.append(task)
    return tasks


def get_live_map_tasks(lang="en"):
    maps = get_json_data("maps", lang)["maps"]
    tasks = get_tasks(lang)
    for task in tasks:
        for objective in task.get("objectives") or []:
            for zone in objective.get("zones") or []:
                map_id = zone.get("map")
                zone["map"] = _map_reference(maps.get(map_id), map_id)
            for location in objective.get("possibleLocations") or []:
                map_id = location.get("map")
                location["map"] = _map_reference(maps.get(map_id), map_id)
    return tasks


def _map_reference(map_data, map_id=None):
    map_data = map_data or {}
    return {
        "id": map_data.get("id", map_id),
        "name": map_data.get("name"),
        "normalizedName": map_data.get("normalizedName"),
    }


def get_live_map_static_maps(lang="en"):
    data = get_json_data("maps", lang)
    maps = data["maps"]
    stationary_weapons = data.get("stationaryWeapons", {})
    result = []
    for raw_map in maps.values():
        map_data = copy.deepcopy(raw_map)
        map_data["stationaryWeapons"] = [
            {
                **weapon,
                "stationaryWeapon": {
                    "id": weapon.get("stationaryWeapon"),
                    "name": (
                        stationary_weapons.get(weapon.get("stationaryWeapon"), {})
                    ).get("name"),
                },
            }
            for weapon in map_data.get("stationaryWeapons") or []
        ]
        converted_transits = []
        for transit in map_data.get("transits") or []:
            target_id = transit.get("map")
            target = maps.get(target_id, {})
            converted_transits.append(
                {
                    **transit,
                    "map": {
                        **_map_reference(target, target_id),
                        "switches": copy.deepcopy(target.get("switches") or []),
                    },
                }
            )
        map_data["transits"] = converted_transits
        result.append(map_data)
    return result
