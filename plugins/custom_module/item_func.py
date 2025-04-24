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
          name
          normalizedName
          gridImageLink
        }}
        caliber
        defaultAmmo {{
          name
          normalizedName
          gridImageLink
        }}
        fireModes
        fireRate
        defaultErgonomics
        defaultRecoilVertical
        defaultRecoilHorizontal
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
  maps(lang: {lang}) {{
    name
    locks {{
      key {{
        id
        name
      }}
    }}
  }}
}}
"""


def check_category(item_list, category):
    if category == "Gun":
        return [
            item for item in item_list if item["category"]["parent"]["name"] == "Weapon"
        ]
    elif category == "Provisions":
        return [
            item
            for item in item_list
            if (
                item["category"]["name"] == "Food"
                or item["category"]["name"] == "Drink"
            )
        ]
    elif category == "Key" or category == "Meds":
        return [
            item for item in item_list if item["category"]["parent"]["name"] == category
        ]
    elif category == "Loot":
        return [
            item
            for item in item_list
            if (
                item["category"]["parent"]["name"] == "Barter item"
                or item["category"]["parent"]["name"] == "Special item"
                or item["category"]["parent"]["name"] == "Lubricant"
                or item["category"]["name"] == "Info"
            )
        ]
    else:
        return [item for item in item_list if item["category"]["name"] == category]
