import re
from collections import defaultdict


def generate_item_graphql(lang: str) -> str:
    return f"""
{{
  items(lang: {lang}) {{
    id
    name
    normalizedName
    weight
    gridImageLink
    width
    height
    category {{
      name
      parent {{
        name
      }}
    }}
    properties {{
      ... on ItemPropertiesWeapon {{
        allowedAmmo {{
          id
        }}
        caliber
        defaultAmmo {{
          id
        }}
        fireModes
        fireRate
        ergonomics
        recoilHorizontal
        recoilVertical
      }}
      ... on ItemPropertiesMelee {{
        slashDamage
        stabDamage
        hitRadius
      }}
      ... on ItemPropertiesGrenade {{
        type
        fuse
        minExplosionDistance
        maxExplosionDistance
        fragments
        contusionRadius
      }}
      ... on ItemPropertiesHelmet {{
        class
        deafening
        turnPenalty
        ergoPenalty
        speedPenalty
        headZones
        ricochetY
        durability
        material {{
          name
        }}
      }}
      ... on ItemPropertiesHeadphone {{
        distanceModifier
      }}
      ... on ItemPropertiesArmor {{
        class
        durability
        turnPenalty
        ergoPenalty
        speedPenalty
        zones
        material {{
          name
        }}
      }}
      ... on ItemPropertiesChestRig {{
        class
        durability
        turnPenalty
        ergoPenalty
        speedPenalty
        zones
        capacity
        material {{
          name
        }}
      }}
      ... on ItemPropertiesBackpack {{
        turnPenalty
        ergoPenalty
        speedPenalty
        capacity
        grids {{
          width
          height
        }}
      }}
      ... on ItemPropertiesContainer {{
        capacity
        grids {{
          width
          height
        }}
      }}
      ... on ItemPropertiesKey {{
        uses
      }}
      ... on ItemPropertiesFoodDrink {{
        energy
        hydration
        stimEffects {{
          delay
          value
          type
          skillName
          duration
        }}
        units
      }}
      ... on ItemPropertiesMedKit {{
        cures
        useTime
        hitpoints
      }}
      ... on ItemPropertiesMedicalItem {{
        cures
        useTime
        uses
      }}
      ... on ItemPropertiesPainkiller {{
        cures
        uses
        useTime
        energyImpact
        hydrationImpact
        painkillerDuration
      }}
      ... on ItemPropertiesStim {{
        stimEffects {{
          duration
          skillName
          type
          delay
          value
          chance
        }}
      }}
      ... on ItemPropertiesAmmo {{
        damage
        penetrationPower
        armorDamage
        accuracyModifier
        recoilModifier
        lightBleedModifier
        heavyBleedModifier
      }}
      ... on ItemPropertiesGlasses {{
        class
        durability
        blindnessProtection
        material {{
          name
        }}
      }}
    }}
  }}
}}
"""


# 이거 어디서 쓴거지
"""
  maps(lang: {lang}) {{
    name
    locks {{
      key {{
        id
        name
      }}
    }}
  }}
"""


# item_penalties 테이블 row 변환
def v3_item_penalties_row(item_en):
    if not item_en:
        return (None, None, None, None, None)
    props = item_en.get("properties")
    if not isinstance(props, dict):
        props = {}
    return (
        item_en.get("id"),
        props.get("ergoPenalty"),
        props.get("turnPenalty"),
        props.get("speedPenalty"),
        props.get("distanceModifier"),
    )


# weapon_items 테이블 row 변환
def v3_weapon_items_row(item_en):
    if not item_en:
        return None
    props = item_en.get("properties")
    if not isinstance(props, dict):
        props = {}
    if not ("caliber" in props or "fireRate" in props):
        return None
    fire_modes = props.get("fireModes", [])
    return (
        item_en.get("id"),
        props.get("caliber"),
        props.get("fireRate"),
        props.get("ergonomics"),
        props.get("recoilHorizontal"),
        props.get("recoilVertical"),
        (
            props.get("defaultAmmo", {}).get("id")
            if isinstance(props.get("defaultAmmo"), dict)
            else None
        ),
        "Single fire" in fire_modes,
        "Full auto" in fire_modes,
        "Burst fire" in fire_modes,
        "Double action" in fire_modes,
        "Double tap" in fire_modes,
        "Semi-automatic" in fire_modes,
    )


# weapon_allowed_ammo 테이블 row 변환
def v3_weapon_allowed_ammo_rows(item_en):
    if not item_en:
        return []
    props = item_en.get("properties")
    if not isinstance(props, dict):
        props = {}
    allowed = props.get("allowedAmmo", [])
    return [(item_en.get("id"), ammo["id"]) for ammo in allowed if "id" in ammo]


# ammo_items 테이블 row 변환
def v3_ammo_items_row(item_en):
    if not item_en:
        return None
    props = item_en.get("properties")
    if not isinstance(props, dict):
        props = {}
    if not ("damage" in props or "penetrationPower" in props):
        return None
    return (
        item_en.get("id"),
        props.get("damage"),
        props.get("armorDamage"),
        props.get("penetrationPower"),
        props.get("recoilModifier"),
        props.get("accuracyModifier"),
        props.get("heavyBleedModifier"),
        props.get("lightBleedModifier"),
    )


# melee_items 테이블 row 변환
def v3_melee_items_row(item_en):
    if not item_en:
        return None
    props = item_en.get("properties")
    if not isinstance(props, dict):
        props = {}
    if not ("slashDamage" in props or "stabDamage" in props):
        return None
    return (
        item_en.get("id"),
        props.get("hitRadius"),
        props.get("slashDamage"),
        props.get("stabDamage"),
    )


# throwable_items 테이블 row 변환
def v3_throwable_items_row(item_en):
    if not item_en:
        return None
    props = item_en.get("properties")
    if not isinstance(props, dict):
        props = {}
    if not ("type" in props or "fuse" in props):
        return None
    return (
        item_en.get("id"),
        props.get("type"),
        props.get("fuse"),
        props.get("fragments"),
        props.get("contusionRadius"),
        props.get("minExplosionDistance"),
        props.get("maxExplosionDistance"),
    )


# storage_items, storage_grids 테이블 row 변환
def v3_storage_items_and_grids(item_en):
    if not item_en:
        return None, []
    props = item_en.get("properties")
    if not isinstance(props, dict):
        props = {}
    # storage_type 구분
    storage_type = None
    if "capacity" in props and "grids" in props:
        storage_type = "container"
    elif "capacity" in props:
        storage_type = "backpack"
    if not storage_type:
        return None, []
    storage_row = (
        item_en.get("id"),
        storage_type,
        props.get("capacity"),
    )
    grids = props.get("grids", [])
    grid_rows = [
        (item_en.get("id"), idx, grid.get("width"), grid.get("height"))
        for idx, grid in enumerate(grids)
    ]
    return storage_row, grid_rows


# protection_items 테이블 row 변환
def v3_protection_items_row(item_en):
    if not item_en:
        return None
    props = item_en.get("properties")
    if not isinstance(props, dict):
        props = {}
    # armor/helmet/glasses 등
    if not ("class" in props or "durability" in props):
        return None
    # zone 정보
    zones = props.get("zones") or props.get("headZones") or []
    zone_map = {
        "HeadTop": "is_head_top",
        "HeadNape": "is_head_nape",
        "Ears": "is_head_ears",
        "Face": "is_head_face",
        "Jaws": "is_head_jaws",
        "Eyes": "is_head_eyes",
        "Throat": "is_thorax_throat",
        "Neck": "is_thorax_neck",
        "Thorax": "is_thorax",
        "UpperBack": "is_upper_back",
        "Stomach": "is_stomach",
        "LeftSide": "is_left_side",
        "RightSide": "is_right_side",
        "LowerBack": "is_lower_back",
        "Groin": "is_groin",
        "Buttocks": "is_buttocks",
        "LeftShoulder": "is_left_shoulder",
        "RightShoulder": "is_right_shoulder",
        "FrontPlate": "is_front_plate",
        "BackPlate": "is_back_plate",
        "LeftPlate": "is_left_plate",
        "RightPlate": "is_right_plate",
        "SidePlate": "is_side_plate",
    }
    zone_flags = {k: False for k in zone_map.values()}
    for z in zones:
        if z in zone_map:
            zone_flags[zone_map[z]] = True
    return (
        item_en.get("id"),
        props.get("type") or props.get("protectionType"),
        props.get("class"),
        props.get("durability"),
        (
            props.get("material", {}).get("name")
            if isinstance(props.get("material"), dict)
            else props.get("material")
        ),
        props.get("ricochetY"),
        props.get("deafening"),
        props.get("blindnessProtection"),
        *[zone_flags[k] for k in zone_map.values()],
    )


# consumable_items, consumable_cures, consumable_stim_effects row 변환
def v3_consumable_items_and_effects(item_en):
    if not item_en:
        return None, [], []
    props = item_en.get("properties")
    if not isinstance(props, dict):
        props = {}
    # consumable_type 구분
    ctype = None
    if "energy" in props and "hydration" in props:
        ctype = "fooddrink"
    elif "hitpoints" in props:
        ctype = "medkit"
    elif "painkillerDuration" in props:
        ctype = "painkiller"
    elif "stimEffects" in props:
        ctype = "stim"
    if not ctype:
        return None, [], []
    item_row = (
        item_en.get("id"),
        ctype,
        props.get("energy"),
        props.get("hydration"),
        props.get("units"),
        props.get("useTime"),
        props.get("hitpoints"),
        props.get("painkillerDuration"),
        props.get("energyImpact"),
        props.get("hydrationImpact"),
    )
    cures = props.get("cures", [])
    cure_rows = [(item_en.get("id"), cure) for cure in cures]
    stim_effects = props.get("stimEffects", [])
    stim_rows = [
        (
            item_en.get("id"),
            idx,
            eff.get("type"),
            eff.get("value"),
            eff.get("delay"),
            eff.get("duration"),
            eff.get("skillName"),
        )
        for idx, eff in enumerate(stim_effects)
    ]
    return item_row, cure_rows, stim_rows


# usage_items 테이블 row 변환
def v3_usage_items_row(item_en):
    if not item_en:
        return None
    props = item_en.get("properties")
    if not isinstance(props, dict):
        props = {}
    if "uses" not in props:
        return None
    return (
        item_en.get("id"),
        props.get("uses"),
    )


# item 데이터 가공 함수: 언어별 데이터를 id로 매칭해 DB row로 변환
def v3_item_row_process(item_en, item_ko, item_ja):
    # category 정보 추출
    parent_category = item_en.get("category", {}).get("parent", {}).get("name")
    category = item_en.get("category", {}).get("name")
    return (
        item_en.get("id"),
        parent_category,
        category,
        item_en.get("name"),
        item_ko.get("name"),
        item_ja.get("name"),
        item_en.get("normalizedName"),
        item_en.get("weight"),
        item_en.get("width"),
        item_en.get("height"),
        item_en.get("gridImageLink"),
    )


def assign_unique_normalized_names(item_rows, existing_normalized_names_by_id):
    incoming_ids = {row[0] for row in item_rows}
    used_names = {
        normalized_name
        for item_id, normalized_name in existing_normalized_names_by_id.items()
        if item_id not in incoming_ids and normalized_name
    }
    existing_for_incoming = {
        item_id: normalized_name
        for item_id, normalized_name in existing_normalized_names_by_id.items()
        if item_id in incoming_ids and normalized_name
    }

    assigned_names_by_id = {}
    pending_rows_by_base = defaultdict(list)

    for row in sorted(item_rows, key=lambda r: ((r[6] or ""), r[0])):
        item_id = row[0]
        base_name = row[6]
        existing_name = existing_for_incoming.get(item_id)

        if _is_same_slug_family(base_name, existing_name) and existing_name not in used_names:
            assigned_names_by_id[item_id] = existing_name
            used_names.add(existing_name)
            continue

        pending_rows_by_base[base_name].append(row)

    unique_rows = []
    for row in item_rows:
        item_id = row[0]
        base_name = row[6]

        if item_id not in assigned_names_by_id:
            assigned_names_by_id[item_id] = _next_available_slug(base_name, used_names)

        unique_rows.append((*row[:6], assigned_names_by_id[item_id], *row[7:]))

    return unique_rows


def _is_same_slug_family(base_name, candidate_name):
    if not base_name or not candidate_name:
        return False

    return candidate_name == base_name or bool(
        re.fullmatch(rf"{re.escape(base_name)}-\d+", candidate_name)
    )


def _next_available_slug(base_name, used_names):
    if not base_name:
        return None

    if base_name not in used_names:
        used_names.add(base_name)
        return base_name

    suffix = 1
    while True:
        candidate = f"{base_name}-{suffix}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        suffix += 1


def get_efficiency(name):
    efficiency = {
        "7.62x25mm TT LRNPC": [5, 0, 0, 0, 0, 0],
        "7.62x25mm TT LRN": [5, 0, 0, 0, 0, 0],
        "7.62x25mm TT FMJ43": [6, 1, 0, 0, 0, 0],
        "7.62x25mm TT AKBS": [6, 2, 0, 0, 0, 0],
        "7.62x25mm TT P gl": [6, 3, 0, 0, 0, 0],
        "7.62x25mm TT PT gzh": [6, 4, 0, 0, 0, 0],
        "7.62x25mm TT Pst gzh": [6, 6, 4, 1, 0, 0],
        "9x18mm PM SP8 gzh": [0, 0, 0, 0, 0, 0],
        "9x18mm PM SP7 gzh": [0, 0, 0, 0, 0, 0],
        "9x18mm PM PSV": [0, 0, 0, 0, 0, 0],
        "9x18mm PM P gzh": [2, 0, 0, 0, 0, 0],
        "9x18mm PM PSO gzh": [2, 0, 0, 0, 0, 0],
        "9x18mm PM PS gs PPO": [3, 0, 0, 0, 0, 0],
        "9x18mm PM PRS gs": [3, 0, 0, 0, 0, 0],
        "9x18mm PM PPe gzh": [4, 0, 0, 0, 0, 0],
        "9x18mm PM PPT gzh": [5, 1, 0, 0, 0, 0],
        "9x18mm PM Pst gzh": [6, 1, 0, 0, 0, 0],
        "9x18mm PM RG028 gzh": [6, 2, 0, 0, 0, 0],
        "9x18mm PM BZhT gzh": [6, 5, 1, 0, 0, 0],
        "9x18mm PMM PstM gzh": [6, 6, 4, 0, 0, 0],
        "9x18mm PM PBM gzh": [6, 6, 5, 1, 0, 0],
        "9x19mm RIP": [0, 0, 0, 0, 0, 0],
        "9x19mm QuakeMaker": [6, 1, 0, 0, 0, 0],
        "9x19mm PSO gzh": [6, 2, 0, 0, 0, 0],
        "9x19mm Luger CCI": [6, 2, 0, 0, 0, 0],
        "9x19mm Green Tracer": [6, 3, 1, 0, 0, 0],
        "9x19mm FMJ M882": [6, 5, 2, 0, 0, 0],
        "9x19mm Pst gzh": [6, 6, 2, 0, 0, 0],
        "9x19mm AP 6.3": [6, 6, 6, 4, 2, 1],
        "9x19mm PBP gzh": [6, 6, 6, 5, 4, 3],
        "9x21mm PE gzh": [6, 2, 0, 0, 0, 0],
        "9x21mm P gzh": [6, 3, 0, 0, 0, 0],
        "9x21mm PS gzh": [6, 6, 3, 1, 0, 0],
        "9x21mm 7U4": [6, 6, 5, 3, 1, 0],
        "9x21mm BT gzh": [6, 6, 6, 4, 3, 1],
        '9x21mm 7N42 "Zubilo"': [6, 6, 6, 5, 4, 2],
        ".357 Magnum SP": [6, 1, 0, 0, 0, 0],
        ".357 Magnum HP": [6, 3, 0, 0, 0, 0],
        ".357 Magnum JHP": [6, 6, 2, 0, 0, 0],
        ".357 Magnum FMJ": [6, 6, 6, 2, 1, 0],
        ".45 ACP RIP": [1, 0, 0, 0, 0, 0],
        ".45 ACP Hydra-Shok": [6, 3, 0, 0, 0, 0],
        ".45 ACP Lasermatch FMJ": [6, 5, 1, 0, 0, 0],
        ".45 ACP Match FMJ": [6, 6, 3, 1, 0, 0],
        ".45 ACP AP": [6, 6, 6, 5, 4, 2],
        "4.6x30mm Action SX": [6, 5, 1, 0, 0, 0],
        "4.6x30mm Subsonic SX": [6, 6, 3, 0, 0, 0],
        "4.6x30mm JSP SX": [6, 6, 6, 4, 2, 1],
        "4.6x30mm FMJ SX": [6, 6, 6, 6, 4, 3],
        "4.6x30mm AP SX": [6, 6, 6, 6, 6, 5],
        "5.7x28mm R37.F": [4, 0, 0, 0, 0, 0],
        "5.7x28mm R37.X": [6, 1, 0, 0, 0, 0],
        "5.7x28mm SS198LF": [6, 4, 1, 0, 0, 0],
        "5.7x28mm SS197SR": [6, 6, 4, 1, 0, 0],
        "5.7x28mm SB193": [6, 6, 5, 2, 1, 0],
        "5.7x28mm L191": [6, 6, 6, 3, 2, 2],
        "5.7x28mm SS190": [6, 6, 6, 5, 4, 3],
        "5.45x39mm HP": [5, 0, 0, 0, 0, 0],
        "5.45x39mm PRS gs": [6, 1, 0, 0, 0, 0],
        "5.45x39mm SP": [6, 2, 0, 0, 0, 0],
        "5.45x39mm US gs": [6, 5, 1, 0, 0, 0],
        "5.45x39mm T gs": [6, 6, 1, 0, 0, 0],
        "5.45x39mm FMJ": [6, 6, 3, 2, 0, 0],
        "5.45x39mm PS gs": [6, 6, 5, 3, 1, 0],
        "5.45x39mm PP gs": [6, 6, 6, 4, 3, 1],
        "5.45x39mm BT gs": [6, 6, 6, 5, 3, 2],
        "5.45x39mm 7N40": [6, 6, 6, 6, 4, 3],
        "5.45x39mm BP gs": [6, 6, 6, 6, 5, 4],
        "5.45x39mm BS gs": [6, 6, 6, 6, 6, 5],
        '5.45x39mm PPBS gs "Igolnik"': [6, 6, 6, 6, 6, 6],
        "5.56x45mm Warmageddon": [1, 0, 0, 0, 0, 0],
        "5.56x45mm HP": [4, 0, 0, 0, 0, 0],
        "5.56x45mm MK 255 Mod 0 (RRLP)": [6, 1, 0, 0, 0, 0],
        "5.56x45mm M856": [6, 5, 1, 0, 0, 0],
        "5.56x45mm FMJ": [6, 6, 4, 1, 0, 0],
        "5.56x45mm M855": [6, 6, 5, 3, 2, 0],
        "5.56x45mm MK 318 Mod 0 (SOST)": [6, 6, 6, 4, 2, 1],
        "5.56x45mm M856A1": [6, 6, 6, 5, 3, 2],
        "5.56x45mm M855A1": [6, 6, 6, 6, 5, 4],
        "5.56x45mm M995": [6, 6, 6, 6, 6, 5],
        "5.56x45mm SSA AP": [6, 6, 6, 6, 6, 5],
        "6.8x51mm SIG FMJ": [6, 6, 6, 5, 4, 2],
        "6.8x51mm SIG Hybrid": [6, 6, 6, 6, 5, 5],
        ".300 Whisper": [6, 4, 2, 1, 0, 0],
        ".300 Blackout V-Max": [6, 6, 4, 3, 1, 0],
        ".300 Blackout BCP FMJ": [6, 6, 6, 3, 2, 0],
        ".300 Blackout M62 Tracer": [6, 6, 6, 5, 4, 2],
        ".300 Blackout CBJ": [6, 6, 6, 6, 5, 3],
        ".300 Blackout AP": [6, 6, 6, 6, 5, 4],
        "7.62x39mm HP": [6, 4, 1, 0, 0, 0],
        "7.62x39mm SP": [6, 6, 2, 0, 0, 0],
        "7.62x39mm FMJ": [6, 6, 4, 1, 0, 0],
        "7.62x39mm US gzh": [6, 6, 5, 3, 1, 0],
        "7.62x39mm T-45M1 gzh": [6, 6, 6, 3, 1, 0],
        "7.62x39mm PS gzh": [6, 6, 6, 5, 3, 2],
        "7.62x39mm PP gzh": [6, 6, 6, 6, 4, 3],
        "7.62x39mm BP gzh": [6, 6, 6, 6, 5, 4],
        "7.62x39mm MAI AP": [6, 6, 6, 6, 6, 5],
        "7.62x51mm Ultra Nosler": [6, 4, 0, 0, 0, 0],
        "7.62x51mm TCW SP": [6, 6, 6, 3, 2, 0],
        "7.62x51mm BCP FMJ": [6, 6, 6, 4, 3, 2],
        "7.62x51mm M80": [6, 6, 6, 6, 5, 4],
        "7.62x51mm M62 Tracer": [6, 6, 6, 6, 5, 5],
        "7.62x51mm M61": [6, 6, 6, 6, 6, 6],
        "7.62x51mm M993": [6, 6, 6, 6, 6, 6],
        "7.62x54mm R HP BT": [6, 6, 3, 1, 0, 0],
        "7.62x54mm R SP BT": [6, 6, 5, 4, 2, 1],
        "7.62x54mm R FMJ": [6, 6, 6, 5, 3, 2],
        "7.62x54mm R T-46M gzh": [6, 6, 6, 6, 4, 3],
        "7.62x54mm R LPS gzh": [6, 6, 6, 6, 4, 3],
        "7.62x54mm R PS gzh": [6, 6, 6, 6, 5, 5],
        "7.62x54mm R BT gzh": [6, 6, 6, 6, 6, 5],
        "7.62x54mm R SNB gzh": [6, 6, 6, 6, 6, 6],
        "7.62x54mm R BS gs": [6, 6, 6, 6, 6, 6],
        ".338 Lapua Magnum TAC-X": [6, 5, 3, 1, 0, 0],
        ".338 Lapua Magnum UCW": [6, 6, 6, 5, 4, 2],
        ".338 Lapua Magnum FMJ": [6, 6, 6, 6, 5, 5],
        ".338 Lapua Magnum AP": [6, 6, 6, 6, 6, 6],
        "9x39mm FMJ": [6, 5, 2, 0, 0, 0],
        "9x39mm SP-5 gs": [6, 6, 5, 2, 1, 0],
        "9x39mm SPP gs": [6, 6, 6, 5, 3, 2],
        "9x39mm PAB-9 gs": [6, 6, 6, 6, 5, 4],
        "9x39mm SP-6 gs": [6, 6, 6, 6, 5, 5],
        "9x39mm BP gs": [6, 6, 6, 6, 6, 5],
        ".366 TKM Geksa": [6, 3, 0, 0, 0, 0],
        ".366 TKM FMJ": [6, 6, 4, 1, 0, 0],
        ".366 TKM EKO": [6, 6, 6, 3, 1, 0],
        ".366 TKM AP-M": [6, 6, 6, 6, 5, 4],
        "12.7x55mm PS12A": [6, 0, 0, 0, 0, 0],
        "12.7x55mm PS12": [6, 6, 5, 2, 1, 0],
        "12.7x55mm PS12B": [6, 6, 6, 6, 5, 4],
        "12/70 5.25mm buckshot": [3, 3, 3, 3, 3, 3],
        "12/70 8.5mm Magnum buckshot": [3, 3, 3, 3, 3, 3],
        "12/70 6.5mm Express buckshot": [3, 3, 3, 3, 3, 3],
        "12/70 7mm buckshot": [3, 3, 3, 3, 3, 3],
        "12/70 Piranha": [6, 6, 5, 4, 4, 4],
        "12/70 flechette": [6, 6, 6, 5, 5, 5],
        "12/70 RIP": [0, 0, 0, 0, 0, 0],
        "12/70 SuperFormance HP slug": [0, 0, 0, 0, 0, 0],
        "12/70 Grizzly 40 slug": [6, 2, 0, 0, 0, 0],
        "12/70 Copper Sabot Premier HP slug": [6, 3, 1, 0, 0, 0],
        "12/70 lead slug": [6, 4, 1, 0, 0, 0],
        '12/70 "Poleva-3" slug': [6, 5, 1, 0, 0, 0],
        "12/70 Dual Sabot slug": [6, 5, 2, 0, 0, 0],
        "12/70 FTX Custom Lite slug": [6, 6, 2, 0, 0, 0],
        '12/70 "Poleva-6u" slug': [6, 6, 2, 0, 0, 0],
        "12/70 makeshift .50 BMG slug": [6, 6, 5, 3, 1, 0],
        "12/70 AP-20 armor-piercing slug": [6, 6, 6, 5, 4, 3],
        "20/70 5.6mm buckshot": [3, 3, 3, 3, 3, 3],
        "20/70 6.2mm buckshot": [3, 3, 3, 3, 3, 3],
        "20/70 7.5mm buckshot": [3, 3, 3, 3, 3, 3],
        "20/70 7.3mm buckshot": [3, 3, 3, 3, 3, 3],
        "20/70 Devastator slug": [1, 0, 0, 0, 0, 0],
        '20/70 "Poleva-3" slug': [6, 2, 0, 0, 0, 0],
        "20/70 Star slug": [6, 5, 1, 0, 0, 0],
        '20/70 "Poleva-6u" slug': [6, 5, 1, 0, 0, 0],
        "23x75mm Zvezda flashbang round": [0, 0, 0, 0, 0, 0],
        "23x75mm Shrapnel-25 buckshot": [6, 4, 3, 3, 3, 3],
        "23x75mm Shrapnel-10 buckshot": [6, 4, 3, 3, 3, 3],
        "23x75mm Barrikada slug": [6, 6, 6, 6, 4, 4],
        "40x46mm M576 (MP-APERS) grenade": [5, 3, 3, 3, 3, 3],
        "30x29mm VOG-30 E": [0, 0, 0, 0, 0, 0],
        "12.7x108mm BZT-44M": [6, 6, 6, 6, 6, 6],
        "12.7x108mm B-32": [6, 6, 6, 6, 6, 6],
        "20x1mm disk": [0, 0, 0, 0, 0, 0],
        "40x46mm M406 (HE) grenade": [5, 3, 3, 3, 3, 3],
        "40x46mm M441 (HE) grenade": [5, 3, 3, 3, 3, 3],
        "40x46mm M381 (HE) grenade": [5, 3, 3, 3, 3, 3],
        "40x46mm M386 (HE) grenade": [5, 3, 3, 3, 3, 3],
        "26x75mm flare cartridge (Green)": [0, 0, 0, 0, 0, 0],
        "26x75mm flare cartridge (Red)": [0, 0, 0, 0, 0, 0],
        "26x75mm flare cartridge (White)": [0, 0, 0, 0, 0, 0],
        "26x75mm flare cartridge (Yellow)": [0, 0, 0, 0, 0, 0],
        "40mm VOG-25 grenade": [0, 0, 0, 0, 0, 0],
        "26x75mm flare cartridge (Acid Green)": [0, 0, 0, 0, 0, 0],
        "40x46mm M433 (HEDP) grenade": [5, 3, 3, 3, 3, 3],
        "Signal flare (Blue)": [0, 0, 0, 0, 0, 0],
        "Signal flare (New Year)": [0, 0, 0, 0, 0, 0],
        ".50 AE JHP": [6, 1, 0, 0, 0, 0],
        "20/70 Poleva-3 slug": [6, 2, 0, 0, 0, 0],
        "12/70 Poleva-3 slug": [6, 5, 1, 0, 0, 0],
        "20/70 Poleva-6u slug": [6, 5, 1, 0, 0, 0],
        "12/70 Poleva-6u slug": [6, 6, 2, 0, 0, 0],
        "20/70 flechette": [6, 6, 5, 4, 4, 4],
        "20/70 Dangerous Game Slug": [6, 6, 5, 3, 1, 0],
        ".50 AE Hawk JSP": [6, 6, 4, 1, 0, 0],
        "20/70 TSS Armor Piercing Slug": [6, 6, 6, 3, 1, 0],
        ".50 AE Copper Solid": [6, 6, 6, 5, 3, 2],
        "9x21mm 7N42 Zubilo": [6, 6, 6, 5, 4, 2],
        ".50 AE FMJ": [6, 6, 6, 6, 4, 3],
        "7.62x51mm M80A1": [6, 6, 6, 6, 6, 6],
        "5.45x39mm PPBS gs Igolnik": [6, 6, 6, 6, 6, 6],
        ".50 BMG HP": [6, 6, 6, 4, 3, 1],
        ".50 BMG M21": [6, 6, 6, 6, 5, 4],
        ".50 BMG M33": [6, 6, 6, 6, 6, 5],
        ".50 BMG M903 SLAP": [6, 6, 6, 6, 6, 6],
    }

    if name in efficiency:
        return efficiency[name]
    return []
