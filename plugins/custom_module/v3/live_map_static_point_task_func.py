import hashlib
import re

from psycopg2.extras import Json

from custom_module.v3.live_map_point_task_func import match_floor


def generate_live_map_static_point_graphql():
    return """
{
  maps(gameMode: regular) {
    name
    btrStops {
      name
      x
      y
      z
    }
    stationaryWeapons {
      position {
        x
        y
        z
      }
      stationaryWeapon {
        name
        id
      }
    }
    transits {
      position {
        y
        x
        z
      }
      map {
        id
        name
        switches {
          id
          name
          position {
            x
            y
            z
          }
        }
      }
    }
    extracts {
      position {
        x
        y
        z
      }
      id
      name
      faction
    }
  }
}
"""


def normalize_map_name(value):
    if not value:
        return ""
    normalized = value.lower()
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def build_static_point_id(map_id, category, source_key):
    raw = f"{map_id}|{category}|{source_key}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"{map_id}:{category}:{digest}"


def boss_spawn_category(boss_id):
    if boss_id in {
        "blackDivision",
        "bossBullyBlackDiv",
        "pmcBotBlackDiv",
    }:
        return "black_div_spawn"
    if boss_id == "sectantPriest":
        return "cultist_spawn"
    if boss_id == "bossKnight":
        return "goons_spawn"
    if boss_id == "ExUsec":
        return "rogue_spawn"
    if boss_id in {"PmcBot", "Sentry", "vsRF", "vsRFSniper"}:
        return "raider_spawn"
    return "boss_spawn"


def build_metadata(source_type, raw, **values):
    return Json(
        {
            "source": "tarkov.dev",
            "source_type": source_type,
            "raw": raw,
            **values,
        }
    )


def build_static_point_row(
    *,
    map_id,
    floors,
    floor_zones,
    category,
    source_key,
    name,
    position,
    metadata,
    sort_order,
    image=None,
    name_en=None,
    name_ko=None,
    name_ja=None,
):
    floor_id = match_floor(floors, floor_zones, position)
    return (
        build_static_point_id(map_id, category, source_key),
        map_id,
        floor_id,
        category,
        name_en or name,
        name_ko or name,
        name_ja or name,
        None,
        None,
        None,
        image,
        position.get("x"),
        position.get("z"),
        metadata,
        sort_order,
    )


def build_live_map_static_point_rows(
    api_maps,
    local_maps,
    floors_by_map_id,
    floor_zones_by_map_id,
    items_by_id=None,
):
    items_by_id = items_by_id or {}
    rows = []
    skipped_maps = []

    for api_map in api_maps:
        local_map = local_maps.get(normalize_map_name(api_map.get("name")))
        if not local_map:
            skipped_maps.append(api_map.get("name"))
            continue

        map_id = local_map["id"]
        floors = floors_by_map_id.get(map_id, [])
        floor_zones = floor_zones_by_map_id.get(map_id, [])
        sort_order = 1

        for stop in api_map.get("btrStops") or []:
            position = {"x": stop.get("x"), "y": stop.get("y"), "z": stop.get("z")}
            rows.append(
                build_static_point_row(
                    map_id=map_id,
                    floors=floors,
                    floor_zones=floor_zones,
                    category="btr_stop",
                    source_key=f"btr:{stop.get('name')}:{position}",
                    name=stop.get("name"),
                    position=position,
                    metadata=build_metadata("btr_stop", stop),
                    sort_order=sort_order,
                )
            )
            sort_order += 1

        for weapon in api_map.get("stationaryWeapons") or []:
            stationary_weapon = weapon.get("stationaryWeapon") or {}
            position = weapon.get("position") or {}
            rows.append(
                build_static_point_row(
                    map_id=map_id,
                    floors=floors,
                    floor_zones=floor_zones,
                    category="stationary_weapon",
                    source_key=(
                        f"stationary:{stationary_weapon.get('id')}:{position}"
                    ),
                    name=stationary_weapon.get("name"),
                    position=position,
                    metadata=build_metadata("stationary_weapon", weapon),
                    sort_order=sort_order,
                )
            )
            sort_order += 1

        for lock in api_map.get("locks") or []:
            api_key_item = lock.get("keyItem") or {}
            key_item_id = api_key_item.get("id") or lock.get("key")
            db_key_item = items_by_id.get(key_item_id) or {}
            key_item = {
                "id": key_item_id,
                "normalized_name": db_key_item.get("normalized_name")
                or api_key_item.get("normalizedName"),
                "name_en": db_key_item.get("name_en")
                or api_key_item.get("name"),
                "name_ko": db_key_item.get("name_ko"),
                "name_ja": db_key_item.get("name_ja"),
                "image": db_key_item.get("image") or api_key_item.get("image"),
            }
            position = lock.get("position") or {}
            lock_type = lock.get("lockType")
            category = (
                "locked_door" if lock_type == "door" else "locked_container"
            )
            rows.append(
                build_static_point_row(
                    map_id=map_id,
                    floors=floors,
                    floor_zones=floor_zones,
                    category=category,
                    source_key=f"lock:{lock.get('id')}",
                    name=key_item.get("name_en") or "Locked location",
                    name_en=key_item.get("name_en"),
                    name_ko=key_item.get("name_ko"),
                    name_ja=key_item.get("name_ja"),
                    position=position,
                    image=key_item.get("image"),
                    metadata=build_metadata(
                        "lock",
                        lock,
                        lock_id=lock.get("id"),
                        lock_type=lock_type,
                        key_item_id=key_item_id,
                        key_item=key_item,
                        needs_power=bool(lock.get("needsPower")),
                    ),
                    sort_order=sort_order,
                )
            )
            sort_order += 1

        for loot in api_map.get("lootLoose") or []:
            position = loot.get("position") or {}
            key_items = loot.get("keyItems") or []
            item_groups = (
                (
                    "key_spawn",
                    [item for item in key_items if not item.get("isKeycard")],
                ),
                (
                    "keycard_spawn",
                    [item for item in key_items if item.get("isKeycard")],
                ),
            )
            for category, items in item_groups:
                if not items:
                    continue
                item_ids = sorted({item.get("id") for item in items if item.get("id")})
                if len(items) == 1:
                    name = items[0].get("name")
                    image = items[0].get("image")
                else:
                    name = "Keycard spawn" if category == "keycard_spawn" else "Key spawn"
                    image = None
                rows.append(
                    build_static_point_row(
                        map_id=map_id,
                        floors=floors,
                        floor_zones=floor_zones,
                        category=category,
                        source_key=f"{category}:{position}",
                        name=name,
                        position=position,
                        image=image,
                        metadata=build_metadata(
                            "loose_loot",
                            {"position": position, "keyItems": items},
                            spawn_type=(
                                "keycard" if category == "keycard_spawn" else "key"
                            ),
                            item_ids=item_ids,
                        ),
                        sort_order=sort_order,
                    )
                )
                sort_order += 1

        for transit in api_map.get("transits") or []:
            target_map = transit.get("map") or {}
            position = transit.get("position") or {}
            rows.append(
                build_static_point_row(
                    map_id=map_id,
                    floors=floors,
                    floor_zones=floor_zones,
                    category="transit",
                    source_key=f"transit:{target_map.get('id')}:{position}",
                    name=target_map.get("name"),
                    position=position,
                    metadata=build_metadata("transit", transit),
                    sort_order=sort_order,
                )
            )
            sort_order += 1

            for switch in target_map.get("switches") or []:
                switch_position = switch.get("position") or {}
                if not switch_position:
                    continue
                rows.append(
                    build_static_point_row(
                        map_id=map_id,
                        floors=floors,
                        floor_zones=floor_zones,
                        category="transit_switch",
                        source_key=(
                            f"transit_switch:{target_map.get('id')}:"
                            f"{switch.get('id')}:{switch_position}"
                        ),
                        name=switch.get("name"),
                        position=switch_position,
                        metadata=build_metadata(
                            "transit_switch",
                            {"target_map": target_map, "switch": switch},
                        ),
                        sort_order=sort_order,
                    )
                )
                sort_order += 1

        for extract in api_map.get("extracts") or []:
            position = extract.get("position") or {}
            rows.append(
                build_static_point_row(
                    map_id=map_id,
                    floors=floors,
                    floor_zones=floor_zones,
                    category="extract",
                    source_key=f"extract:{extract.get('id')}:{position}",
                    name=extract.get("name"),
                    position=position,
                    metadata=build_metadata("extract", extract),
                    sort_order=sort_order,
                )
            )
            sort_order += 1

    if skipped_maps:
        print(f"Skipped maps without local match: {skipped_maps}")

    return rows


def _boss_info(boss_id, bosses_by_id):
    return bosses_by_id.get(boss_id) or {
        "id": boss_id,
        "normalized_name": None,
        "name_en": boss_id,
        "name_ko": None,
        "name_ja": None,
        "image": None,
    }


def _escort_info(escort, bosses_by_id):
    return {
        **_boss_info(escort.get("mob"), bosses_by_id),
        "amount": escort.get("amount") or [],
    }


def build_boss_spawn_metadata_updates(
    api_maps,
    existing_points,
    bosses_by_id,
):
    candidates_by_map_category = {}
    definitions_by_map_category = {}
    definitions_by_category = {}
    for api_map in api_maps:
        map_id = api_map.get("id")
        for spawn in api_map.get("bosses") or []:
            boss_id = spawn.get("mob")
            category = boss_spawn_category(boss_id)
            boss = _boss_info(boss_id, bosses_by_id)
            escorts = [
                _escort_info(escort, bosses_by_id)
                for escort in spawn.get("escorts") or []
            ]
            definition = {
                "boss": boss,
                "escorts": escorts,
                "spawn_chance": spawn.get("spawnChance"),
            }
            definitions_by_map_category.setdefault(
                (map_id, category), []
            ).append(definition)
            definitions_by_category.setdefault(category, []).append(definition)
            for location in spawn.get("spawnLocations") or []:
                spawn_key = location.get("spawnKey") or location.get("name")
                for position in location.get("positions") or []:
                    if position.get("x") is None or position.get("z") is None:
                        continue
                    candidates_by_map_category.setdefault(
                        (map_id, category), []
                    ).append(
                        {
                            "boss": boss,
                            "escorts": escorts,
                            "spawn_chance": spawn.get("spawnChance"),
                            "location_chance": location.get("chance"),
                            "spawn_key": spawn_key,
                            "location_name": location.get("name"),
                            "position": position,
                        }
                    )

    updates = []
    for point in existing_points:
        candidates = candidates_by_map_category.get(
            (point.get("map_id"), point.get("category")), []
        )
        point_name = normalize_map_name(point.get("name_en"))
        if not candidates or point.get("x") is None or point.get("z") is None:
            definitions = definitions_by_map_category.get(
                (point.get("map_id"), point.get("category")), []
            )
            if not definitions:
                definitions = definitions_by_category.get(
                    point.get("category"), []
                )
            named_definitions = [
                definition
                for definition in definitions
                if definition["boss"].get("normalized_name")
                and definition["boss"]["normalized_name"] in point_name
            ]
            match_pool = named_definitions or definitions
            if not match_pool:
                continue
            primary = match_pool[0]
            related_bosses = {}
            for definition in match_pool:
                boss_id = definition["boss"].get("id")
                related_bosses[boss_id] = {
                    **definition["boss"],
                    "spawn_chance": (
                        definition["spawn_chance"]
                        if definitions_by_map_category.get(
                            (point.get("map_id"), point.get("category"))
                        )
                        else None
                    ),
                    "escorts": definition["escorts"],
                }
            metadata = dict(point.get("metadata") or {})
            metadata.update(
                {
                    "source": "tarkov.dev",
                    "source_type": "boss_spawn",
                    "boss": primary["boss"],
                    "bosses": list(related_bosses.values()),
                    "escorts": primary["escorts"],
                    "spawn_chance": (
                        primary["spawn_chance"]
                        if definitions_by_map_category.get(
                            (point.get("map_id"), point.get("category"))
                        )
                        else None
                    ),
                    "location_chance": None,
                    "matched_location": None,
                }
            )
            updates.append((point["id"], Json(metadata)))
            continue

        named_candidates = [
            candidate
            for candidate in candidates
            if candidate["boss"].get("normalized_name")
            and candidate["boss"]["normalized_name"] in point_name
        ]
        match_pool = named_candidates or candidates

        def distance_squared(candidate):
            position = candidate["position"]
            return (
                float(position["x"]) - float(point["x"])
            ) ** 2 + (
                float(position["z"]) - float(point["z"])
            ) ** 2

        nearest = min(match_pool, key=distance_squared)
        related_candidates = [
            candidate
            for candidate in match_pool
            if candidate["spawn_key"] == nearest["spawn_key"]
        ]
        related_bosses = {}
        for candidate in related_candidates:
            boss_id = candidate["boss"].get("id")
            related_bosses[boss_id] = {
                **candidate["boss"],
                "spawn_chance": candidate["spawn_chance"],
                "escorts": candidate["escorts"],
            }

        metadata = dict(point.get("metadata") or {})
        metadata.update(
            {
                "source": "tarkov.dev",
                "source_type": "boss_spawn",
                "boss": nearest["boss"],
                "bosses": list(related_bosses.values()),
                "escorts": nearest["escorts"],
                "spawn_chance": nearest["spawn_chance"],
                "location_chance": nearest["location_chance"],
                "matched_location": {
                    "spawn_key": nearest["spawn_key"],
                    "name": nearest["location_name"],
                    "position": nearest["position"],
                    "distance": distance_squared(nearest) ** 0.5,
                },
            }
        )
        updates.append((point["id"], Json(metadata)))

    return updates
