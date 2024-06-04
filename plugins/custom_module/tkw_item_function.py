weapon_graphql = """
{
  items {
    id
    name
    weight
    shortName
    image512pxLink
    category {
      name
      parent {
        name
      }
    }
    properties {
      ... on ItemPropertiesWeapon {
        caliber
        defaultAmmo {
          name
        }
        fireModes
        fireRate
        defaultErgonomics
        defaultRecoilVertical
        defaultRecoilHorizontal
      }
      ... on ItemPropertiesMelee {
        slashDamage
        stabDamage
        hitRadius
      }
      ... on ItemPropertiesGrenade {
        type
        fuse
        minExplosionDistance
        maxExplosionDistance
        fragments
        contusionRadius
      }
      ... on ItemPropertiesHelmet {
        durability
        class
        headZones
        ricochetY
      }
      ... on ItemPropertiesArmor {
        durability
        class
        zones
      } 
      ... on ItemPropertiesChestRig {
        class
        zones
        capacity
      }
    }
  }
}
"""


def check_category(weapon_list, weapon_category):
    """
    category 별 데이터 변경
    """
    if weapon_category == "Gun":
        return [
            item
            for item in weapon_list
            if item["category"]["parent"]["name"] == "Weapon"
            and item["properties"] != {}
        ]
    elif weapon_category == "Gun image":
        return [
            item
            for item in weapon_list
            if item["category"]["parent"]["name"] == "Weapon"
            and item["properties"] == {}
            and (
                "Default" in item["name"]
                or "Lobaev Arms DVL-10 7.62x51 bolt-action sniper rifle Urbana"
                in item["name"]
                or "Colt M4A1 5.56x45 assault rifle Carbine" in item["name"]
                or "Kalashnikov PKP 7.62x54R infantry machine gun Zenit" in item["name"]
            )
        ]
    elif weapon_category == "Headphones":
        return [
            item for item in weapon_list if item["category"]["name"] == weapon_category
        ]
    elif weapon_category == "Headwear":
        return [
            item
            for item in weapon_list
            if item["category"]["name"] == weapon_category
            and item["name"] != "Maska-1SCh bulletproof helmet (Killa Edition) Default"
            and item["name"] != "Ops-Core FAST MT Super High Cut helmet (Black) RAC"
            and item["name"] != "Wilcox Skull Lock head mount PVS-14"
        ]
    elif weapon_category == "Armor":
        return [
            item
            for item in weapon_list
            if item["category"]["name"] == weapon_category and item["properties"] != {}
        ]
    elif weapon_category == "Chest rig":
        return [
            item
            for item in weapon_list
            if item["category"]["name"] == weapon_category and item["properties"] != {}
        ]
    else:
        return [
            item
            for item in weapon_list
            if item["category"]["name"] == weapon_category and item["properties"] != {}
        ]