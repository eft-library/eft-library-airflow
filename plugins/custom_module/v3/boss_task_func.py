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

    rows = []

    for eq in equipment_list:
        item = eq.get("item")
        if not item:
            continue

        item_id = item.get("id")
        quantity = eq.get("quantity", 1)

        if item_id:
            rows.append((boss_id, item_id, quantity))

    return rows
