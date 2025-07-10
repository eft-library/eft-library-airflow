import json
import pendulum
import copy
from collections import defaultdict


def generate_boss_graphql(lang: str) -> str:
    return f"""
{{
  bosses(lang: {lang}) {{
    id
    name
    normalizedName
    imagePortraitLink
    health {{
      bodyPart
      max
    }}
    equipment {{
      item {{
        id
        name
        gridImageLink
        normalizedName
      }}
      count
      quantity
    }}
  }}
}}
"""


def generate_boss_spawn_graphql(lang: str) -> str:
    return f"""
{{
  maps(lang: {lang}) {{
    id
    name
    bosses {{
      spawnChance
      boss {{
        id
      }}
    }}
  }}
}}
"""


def v2_boss_process(item_en, item_ko, item_ja):
    boss_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    url_mapping = item_en.get("normalizedName")
    image = item_en.get("imagePortraitLink")
    merged_equipment = []
    merged_health = []

    for eq_en, eq_ko, eq_ja in zip(
        item_en.get("equipment", []),
        item_ko.get("equipment", []),
        item_ja.get("equipment", []),
    ):
        merged_eq = copy.deepcopy(eq_en)  # 기본은 영어 구조 복사
        item = eq_en["item"]

        # 다국어 이름 병합
        item["name_en"] = eq_en["health"].get("bodyPart", "")
        item["name_ko"] = eq_ko["health"].get("bodyPart", "")
        item["name_ja"] = eq_ja["health"].get("bodyPart", "")
        del item["name"]

        merged_eq["item"] = item
        merged_equipment.append(merged_eq)

    for h_en, h_ko, h_ja in zip(
        item_en.get("health", []), item_ko.get("health", []), item_ja.get("health", [])
    ):
        merged_health.append(
            {
                "bodyPart_en": h_en.get("bodyPart", ""),
                "bodyPart_ko": h_ko.get("bodyPart", ""),
                "bodyPart_ja": h_ja.get("bodyPart", ""),
                "max": h_en.get("max", 0),
            }
        )

    update_time = pendulum.now("Asia/Seoul")

    return (
        boss_id,
        json.dumps(name),
        image,
        json.dumps(merged_equipment),
        url_mapping,
        merged_health,
        update_time,
    )


def spawn_list_process(item_en, item_ko, item_ja):
    """
    일단 이름 먼저 합치기
    """
    map_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    bosses = item_en.get("bosses")

    return {"id": map_id, "name": name, "bosses": bosses}


def make_boss_spawn_dict(maps):
    """
    최종 딕셔너리 구현
    """
    # 결과를 담을 딕셔너리
    boss_spawn_dict = defaultdict(list)

    # 원본 데이터 (maps는 이미 주어진 JSON 리스트라고 가정)
    for map_info in maps:
        map_name_en = map_info["name"]["en"]
        map_name_ko = map_info["name"]["ko"]
        map_name_ja = map_info["name"]["ja"]

        for boss_info in map_info.get("bosses", []):
            boss_id = boss_info["boss"]["id"]
            spawn_chance = boss_info["spawnChance"]
            boss_spawn_dict[boss_id].append(
                {
                    "name_en": map_name_en,
                    "name_ko": map_name_ko,
                    "name_ja": map_name_ja,
                    "spawnChance": spawn_chance,
                }
            )

    # 딕셔너리를 일반 dict로 변환 (옵션)
    boss_spawn_dict = dict(boss_spawn_dict)
    return boss_spawn_dict


def make_boss_spawn_map(item_en):
    map_dict = {
        "Factory": "FACTORY",
        "Night Factory": "FACTORY",
        "Customs": "CUSTOMS",
        "Woods": "WOODS",
        "Lighthouse": "LIGHT_HOUSE",
        "Shoreline": "SHORELINE",
        "Reserve": "RESERVE",
        "Interchange": "INTERCHANGE",
        "Streets of Tarkov": "STREET_OF_TARKOV",
        "The Lab": "THE_LAB",
        "Ground Zero": "GROUND_ZERO",
        "Ground Zero 21+": "GROUND_ZERO",
    }

    result = list(
        {map_dict[item["name_en"]] for item in item_en if item["name_en"] in map_dict}
    )

    return result
