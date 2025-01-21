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
    boss location chance 가공
    """
    result = [{'id': "RESHALA", 'location_spawn_chance_en': [], 'location_spawn_chance_kr': [], 'name_en': 'Reshala', 'name_kr': '르샬라'},
        {'id': "KOLLONTAY", 'location_spawn_chance_en': [], 'location_spawn_chance_kr': [], 'name_en': 'Kollontay', 'name_kr': '콜론테이'},
        {'id': "KILLA", 'location_spawn_chance_en': [], 'location_spawn_chance_kr': [], 'name_en': 'Killa', 'name_kr': '킬라'},
        {'id': "KABAN", 'location_spawn_chance_en': [], 'location_spawn_chance_kr': [], 'name_en': 'Kaban', 'name_kr': '카반'},
        {'id': "TAGILLA", 'location_spawn_chance_en': [], 'location_spawn_chance_kr': [], 'name_en': 'Tagilla', 'name_kr': '타길라'},
        {'id': "ZRYACHIY", 'location_spawn_chance_en': [], 'location_spawn_chance_kr': [], 'name_en': 'Zryachiy', 'name_kr': '지랴키'},
        {'id': "SHTURMAN", 'location_spawn_chance_en': [], 'location_spawn_chance_kr': [], 'name_en': 'Shturman', 'name_kr': '슈트르만'},
        {'id': "SANITAR", 'location_spawn_chance_en': [], 'location_spawn_chance_kr': [], 'name_en': 'Sanitar', 'name_kr': '세니타'},
        {'id': "GLUKHAR", 'location_spawn_chance_en': [], 'location_spawn_chance_kr': [], 'name_en': 'Glukhar', 'name_kr': '글루하'},
        {'id': "KNIGHT", 'location_spawn_chance_en': [], 'location_spawn_chance_kr': [], 'name_en': 'Knight', 'name_kr': '나이트'},
        {'id': "CULTISTS", 'location_spawn_chance_en': [], 'location_spawn_chance_kr': [], 'name_en': 'Cultists', 'name_kr': '컬티스트'},
        {'id': "PARTISAN", 'location_spawn_chance_en': [], 'location_spawn_chance_kr': [], 'name_en': 'Partisan', 'name_kr': '파르티잔'}]

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

    for map_data in map_list:
        map_name_en = map_data["name"]
        map_name_kr = map_kr.get(map_name_en, map_name_en)  # 한국어 이름 매핑

        # ground zero 21은 다른데
        for boss_data in map_data["bosses"]:
            boss_name = boss_data["boss"]["name"]
            spawn_chance = boss_data["spawnChance"] * 100

            for boss in result:
                if boss["name_en"].lower() in boss_name.lower():  # 이름 매칭 (대소문자 무시)
                    # EN 데이터 추가
                    boss["location_spawn_chance_en"].append({
                        "chance": spawn_chance,
                        "location": map_name_en
                    })
                    # KR 데이터 추가
                    boss["location_spawn_chance_kr"].append({
                        "chance": spawn_chance,
                        "location": map_name_kr
                    })

    return result