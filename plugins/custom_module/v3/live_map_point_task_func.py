import hashlib
import re


def normalize_map_name(value):
    if not value:
        return ""
    normalized = value.lower()
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def match_floor(floors, y_value):
    if not floors:
        return None, None

    if y_value is not None:
        y_float = float(y_value)
        for floor in floors:
            min_y = floor.get("min_y")
            max_y = floor.get("max_y")
            if min_y is None or max_y is None:
                continue
            if float(min_y) <= y_float <= float(max_y):
                return floor.get("id"), floor.get("floor_no")

    default_floor = floors[0]
    for floor in floors:
        if floor.get("floor_no") == 1:
            default_floor = floor
            break
    return default_floor.get("id"), default_floor.get("floor_no")


def generate_live_map_point_graphql(lang: str):
    return f"""
{{
  tasks(lang: {lang}) {{
    id
    name
    normalizedName
    objectives {{
      id
      type
      description
      maps {{
        id
        name
        normalizedName
      }}

      ... on TaskObjectiveBasic {{
        zones {{
          id
          map {{
            id
            normalizedName
          }}
          position {{
            x
            y
            z
          }}
          top
          bottom
        }}
      }}

      ... on TaskObjectiveItem {{
        zones {{
          id
          map {{
            id
            normalizedName
          }}
          position {{
            x
            y
            z
          }}
          top
          bottom
        }}
      }}

      ... on TaskObjectiveMark {{
        zones {{
          id
          map {{
            id
            normalizedName
          }}
          position {{
            x
            y
            z
          }}
          top
          bottom
        }}
      }}

      ... on TaskObjectiveQuestItem {{
        possibleLocations {{
          map {{
            id
            normalizedName
          }}
          positions {{
            x
            y
            z
          }}
        }}
        zones {{
          id
          map {{
            id
            normalizedName
          }}
          position {{
            x
            y
            z
          }}
        }}
      }}

      ... on TaskObjectiveShoot {{
        zones {{
          id
          map {{
            id
            normalizedName
          }}
          position {{
            x
            y
            z
          }}
          top
          bottom
        }}
      }}

      ... on TaskObjectiveUseItem {{
        zones {{
          id
          map {{
            id
            normalizedName
          }}
          position {{
            x
            y
            z
          }}
          top
          bottom
        }}
      }}
    }}
  }}
}}
"""


def build_live_map_point_id(objective_id, map_id, source_type, source_key):
    raw = f"{objective_id}|{map_id}|{source_type}|{source_key}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"{objective_id}:{digest}"


def build_live_map_point_detail_id(point_id):
    return f"{point_id}:detail:1"


def get_local_map(local_maps, api_map):
    if not api_map:
        return None

    for key in (
        api_map.get("id"),
        api_map.get("normalizedName"),
        normalize_map_name(api_map.get("normalizedName")),
        normalize_map_name(api_map.get("name")),
    ):
        if key and key in local_maps:
            return local_maps[key]

    return None


def is_valid_position(position):
    return (
        isinstance(position, dict)
        and position.get("x") is not None
        and position.get("y") is not None
        and position.get("z") is not None
    )


def build_point_row(
    *,
    quest_id,
    objective_id,
    local_map,
    floors_by_map_id,
    position,
    source_type,
    source_key,
):
    map_id = local_map["id"]
    floor_id, floor_no = match_floor(floors_by_map_id.get(map_id, []), position.get("y"))
    point_id = build_live_map_point_id(
        objective_id,
        map_id,
        source_type,
        source_key,
    )

    return (
        point_id,
        quest_id,
        objective_id,
        map_id,
        floor_id,
        floor_no,
        position.get("x"),
        position.get("z"),
        position.get("y"),
    )


def objective_description_by_id(tasks):
    descriptions = {}
    for task in tasks:
        for objective in task.get("objectives") or []:
            objective_id = objective.get("id")
            if objective_id:
                descriptions[objective_id] = objective.get("description")
    return descriptions


def append_point(rows, seen, **kwargs):
    position = kwargs["position"]
    local_map = kwargs["local_map"]
    objective_id = kwargs["objective_id"]
    dedupe_key = (
        objective_id,
        local_map["id"],
        position.get("x"),
        position.get("y"),
        position.get("z"),
    )
    if dedupe_key in seen:
        return

    seen.add(dedupe_key)
    rows.append(build_point_row(**kwargs))


def build_live_map_point_rows(
    tasks_en,
    tasks_ko,
    tasks_ja,
    local_maps,
    floors_by_map_id,
):
    descriptions_ko = objective_description_by_id(tasks_ko)
    descriptions_ja = objective_description_by_id(tasks_ja)

    point_rows = []
    detail_rows = []
    seen_positions = set()

    for task in tasks_en:
        quest_id = task.get("id")

        for objective in task.get("objectives") or []:
            objective_id = objective.get("id")
            if not quest_id or not objective_id:
                continue

            before_count = len(point_rows)

            for zone_index, zone in enumerate(objective.get("zones") or []):
                position = zone.get("position") or {}
                if not is_valid_position(position):
                    continue

                local_map = get_local_map(local_maps, zone.get("map"))
                if not local_map:
                    continue

                append_point(
                    point_rows,
                    seen_positions,
                    quest_id=quest_id,
                    objective_id=objective_id,
                    local_map=local_map,
                    floors_by_map_id=floors_by_map_id,
                    position=position,
                    source_type="zone",
                    source_key=(
                        f"{zone.get('id')}:{zone_index}:"
                        f"{position.get('x')}:{position.get('y')}:{position.get('z')}"
                    ),
                )

            for location_index, location in enumerate(
                objective.get("possibleLocations") or []
            ):
                local_map = get_local_map(local_maps, location.get("map"))
                if not local_map:
                    continue

                for position_index, position in enumerate(
                    location.get("positions") or []
                ):
                    if not is_valid_position(position):
                        continue

                    append_point(
                        point_rows,
                        seen_positions,
                        quest_id=quest_id,
                        objective_id=objective_id,
                        local_map=local_map,
                        floors_by_map_id=floors_by_map_id,
                        position=position,
                        source_type="possible_location",
                        source_key=(
                            f"{location_index}:{position_index}:"
                            f"{position.get('x')}:{position.get('y')}:{position.get('z')}"
                        ),
                    )

            if len(point_rows) == before_count:
                continue

            description_en = objective.get("description")
            description_ko = descriptions_ko.get(objective_id)
            description_ja = descriptions_ja.get(objective_id)
            for row in point_rows[before_count:]:
                point_id = row[0]
                detail_rows.append(
                    (
                        build_live_map_point_detail_id(point_id),
                        point_id,
                        description_en,
                        description_ko,
                        description_ja,
                        None,
                        1,
                    )
                )

    return point_rows, detail_rows
