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
