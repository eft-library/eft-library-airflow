boss_graphql = """
{
  maps {
    name
    bosses {
      spawnChance
      boss {
        name
      }
    }
  }
}
"""

def process_boss_spawn(map_list):
    """
    보스 출현 확률 데이터 가공
    """
    boss_template = {
        "RESHALA": {"name_en": "Reshala", "name_kr": "르샬라"},
        "KOLLONTAY": {"name_en": "Kollontay", "name_kr": "콜론테이"},
        "KILLA": {"name_en": "Killa", "name_kr": "킬라"},
        "KABAN": {"name_en": "Kaban", "name_kr": "카반"},
        "TAGILLA": {"name_en": "Tagilla", "name_kr": "타길라"},
        "ZRYACHIY": {"name_en": "Zryachiy", "name_kr": "지랴키"},
        "SHTURMAN": {"name_en": "Shturman", "name_kr": "슈트르만"},
        "SANITAR": {"name_en": "Sanitar", "name_kr": "세니타"},
        "GLUKHAR": {"name_en": "Glukhar", "name_kr": "글루하"},
        "KNIGHT": {"name_en": "Knight", "name_kr": "나이트"},
        "BIRDEYE": {"name_en": "Birdeye", "name_kr": "버드아이"},
        "BIG_PIPE": {"name_en": "Big Pipe", "name_kr": "빅파이프"},
        "CULTISTS": {"name_en": "Cultists", "name_kr": "컬티스트"},
        "PARTISAN": {"name_en": "Partisan", "name_kr": "파르티잔"},
    }

    # 보스 정보를 딕셔너리 형태로 변환
    result = {
        boss_id: {
            "id": boss_id,
            "name_en": data["name_en"],
            "name_kr": data["name_kr"],
            "location_spawn_chance_en": [],
            "location_spawn_chance_kr": [],
        }
        for boss_id, data in boss_template.items()
    }

    # 맵 이름 매핑
    map_kr = {
        "Factory": "팩토리",
        "Night Factory": "야간 팩토리",
        "Customs": "세관",
        "Woods": "삼림",
        "Lighthouse": "등대",
        "Shoreline": "해안선",
        "Reserve": "리저브",
        "Interchange": "인터체인지",
        "Streets of Tarkov": "타르코프 시내",
        "The Lab": "연구소",
        "Ground Zero": "그라운드 제로",
        "Ground Zero 21+": "그라운드 제로 (LV.21+)",
    }

    # 보스 스폰 정보 처리
    for map_data in map_list:
        map_name_en = map_data["name"]
        map_name_kr = map_kr.get(map_name_en, map_name_en)

        for boss_data in map_data["bosses"]:
            boss_name = boss_data["boss"]["name"]
            spawn_chance = boss_data["spawnChance"] * 100

            # 특정 예외 처리 (이름이 다른 경우)
            if boss_name == "Cultist Priest":
                boss_id = "CULTISTS"
            elif boss_name == "Knight":
                boss_id = "KNIGHT"
                # Knight는 Big Pipe, Birdeye도 같이 등장
                for extra_boss in ["BIG_PIPE", "BIRDEYE"]:
                    result[extra_boss]["location_spawn_chance_en"].append({
                        "chance": spawn_chance,
                        "location": map_name_en
                    })
                    result[extra_boss]["location_spawn_chance_kr"].append({
                        "chance": spawn_chance,
                        "location": map_name_kr
                    })
            else:
                # 일반적인 매칭
                boss_id = next((key for key, data in boss_template.items() if data["name_en"].lower() in boss_name.lower()), None)

            if boss_id:
                result[boss_id]["location_spawn_chance_en"].append({
                    "chance": spawn_chance,
                    "location": map_name_en
                })
                result[boss_id]["location_spawn_chance_kr"].append({
                    "chance": spawn_chance,
                    "location": map_name_kr
                })

    return list(result.values())  # 딕셔너리를 리스트로 변환하여 반환
