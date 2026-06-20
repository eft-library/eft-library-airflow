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


def build_metadata(source_type, raw):
    return Json(
        {
            "source": "tarkov.dev",
            "source_type": source_type,
            "raw": raw,
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
):
    floor_id = match_floor(floors, floor_zones, position)
    return (
        build_static_point_id(map_id, category, source_key),
        map_id,
        floor_id,
        category,
        name,
        name,
        name,
        None,
        None,
        None,
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
):
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
