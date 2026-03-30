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
    props = item_en.get("properties", {})
    return (
        item_en.get("id"),
        props.get("ergoPenalty"),
        props.get("turnPenalty"),
        props.get("speedPenalty"),
        props.get("distanceModifier"),
    )

# weapon_items 테이블 row 변환
def v3_weapon_items_row(item_en):
  props = item_en.get("properties", {})
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
    props.get("defaultAmmo", {}).get("id"),
    "Single fire" in fire_modes,
    "Full auto" in fire_modes,
    "Burst fire" in fire_modes,
    "Double action" in fire_modes,
    "Double tap" in fire_modes,
    "Semi-automatic" in fire_modes,
  )

# weapon_allowed_ammo 테이블 row 변환
def v3_weapon_allowed_ammo_rows(item_en):
  props = item_en.get("properties", {})
  allowed = props.get("allowedAmmo", [])
  return [
    (item_en.get("id"), ammo["id"]) for ammo in allowed if "id" in ammo
  ]

# ammo_items 테이블 row 변환
def v3_ammo_items_row(item_en):
  props = item_en.get("properties", {})
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
  props = item_en.get("properties", {})
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
  props = item_en.get("properties", {})
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
  props = item_en.get("properties", {})
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
  props = item_en.get("properties", {})
  # armor/helmet/glasses 등
  if not ("class" in props or "durability" in props):
    return None
  # zone 정보
  zones = props.get("zones") or props.get("headZones") or []
  zone_map = {
    'HeadTop': 'is_head_top',
    'HeadNape': 'is_head_nape',
    'Ears': 'is_head_ears',
    'Face': 'is_head_face',
    'Jaws': 'is_head_jaws',
    'Eyes': 'is_head_eyes',
    'Throat': 'is_thorax_throat',
    'Neck': 'is_thorax_neck',
    'Thorax': 'is_thorax',
    'UpperBack': 'is_upper_back',
    'Stomach': 'is_stomach',
    'LeftSide': 'is_left_side',
    'RightSide': 'is_right_side',
    'LowerBack': 'is_lower_back',
    'Groin': 'is_groin',
    'Buttocks': 'is_buttocks',
    'LeftShoulder': 'is_left_shoulder',
    'RightShoulder': 'is_right_shoulder',
    'FrontPlate': 'is_front_plate',
    'BackPlate': 'is_back_plate',
    'LeftPlate': 'is_left_plate',
    'RightPlate': 'is_right_plate',
    'SidePlate': 'is_side_plate',
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
    props.get("material", {}).get("name") if isinstance(props.get("material"), dict) else props.get("material"),
    props.get("ricochetY"),
    props.get("deafening"),
    props.get("blindnessProtection"),
    *[zone_flags[k] for k in zone_map.values()]
  )

# consumable_items, consumable_cures, consumable_stim_effects row 변환
def v3_consumable_items_and_effects(item_en):
  props = item_en.get("properties", {})
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
  cure_rows = [
    (item_en.get("id"), cure) for cure in cures
  ]
  stim_effects = props.get("stimEffects", [])
  stim_rows = [
    (
      item_en.get("id"), idx,
      eff.get("type"), eff.get("value"), eff.get("delay"), eff.get("duration"), eff.get("skillName")
    )
    for idx, eff in enumerate(stim_effects)
  ]
  return item_row, cure_rows, stim_rows

# usage_items 테이블 row 변환
def v3_usage_items_row(item_en):
  props = item_en.get("properties", {})
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
