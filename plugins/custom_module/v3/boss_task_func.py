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
      }}
      quantity
    }}
  }}
}}
"""


def generate_boss_spawn_graphql() -> str:
    return f"""
{{
  maps {{
    id
    bosses {{
      spawnChance
      boss {{
        id
      }}
    }}
  }}
}}
"""


def v3_boss_process(item_en, item_ko, item_ja):
    boss_id = item_en.get("id")
    name_en = item_en.get("name")
    name_ko = item_ko.get("name")
    name_ja = item_ja.get("name")
    normalized_name = item_en.get("normalizedName")
    image = item_en.get("imagePortraitLink")

    health_list = item_en.get("health", [])
    health_map = {
        h["bodyPart"]: h["max"]
        for h in health_list
        if h.get("bodyPart") and h.get("max") is not None
    }

    head_hp = health_map.get("head", 0)
    thorax_hp = health_map.get("thorax", 0)
    stomach_hp = health_map.get("stomach", 0)
    left_arm_hp = health_map.get("left arm", 0)
    right_arm_hp = health_map.get("right arm", 0)
    left_leg_hp = health_map.get("left leg", 0)
    right_leg_hp = health_map.get("right leg", 0)
    health_total = sum(health_map.values())

    return (
        boss_id,
        name_en,
        name_ko,
        name_ja,
        image,
        normalized_name,
        health_total,
        head_hp,
        thorax_hp,
        stomach_hp,
        left_arm_hp,
        right_arm_hp,
        left_leg_hp,
        right_leg_hp,
    )


def v3_boss_item_process(item_en):
    boss_id = item_en.get("id")
    equipment_list = item_en.get("equipment", [])

    dedup_map = {}

    # 중복으로 와서 dedupe 추가 - 짜증 ㅜㅜ
    for eq in equipment_list:
        item = eq.get("item")
        if not item:
            continue

        item_id = item.get("id")
        if not item_id:
            continue

        quantity = eq.get("quantity", eq.get("count", 1)) or 1

        key = (boss_id, item_id)

        if key not in dedup_map:
            dedup_map[key] = quantity
        else:
            dedup_map[key] = max(dedup_map[key], quantity)

    return [
        (boss_id, item_id, quantity)
        for (boss_id, item_id), quantity in dedup_map.items()
    ]


def v3_boss_spawn_process(map_item):
    map_id = map_item.get("id")
    boss_list = map_item.get("bosses", [])

    dedup_map = {}

    for boss_info in boss_list:
        boss = boss_info.get("boss")
        if not boss:
            continue

        boss_id = boss.get("id")
        if not boss_id or not map_id:
            continue

        spawn_chance = boss_info.get("spawnChance", 0)

        key = (boss_id, map_id)

        if key not in dedup_map:
            dedup_map[key] = spawn_chance
        else:
            dedup_map[key] = max(dedup_map[key], spawn_chance)

    return [
        (boss_id, map_id, spawn_chance)
        for (boss_id, map_id), spawn_chance in dedup_map.items()
    ]
