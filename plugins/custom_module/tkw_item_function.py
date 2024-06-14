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
      ... on ItemPropertiesBackpack {
        grids{width, height}
        capacity
      }
      ... on ItemPropertiesContainer {
        capacity
        grids{width, height}
      }
      ... on ItemPropertiesKey {
        uses
      }
      ... on ItemPropertiesFoodDrink {
        energy
        hydration
        stimEffects{
          delay
          value
          type
          skillName
          duration
        }
      }
    }
  }
  maps {
    name
    locks {
      key {
        name
      }
    }
  }
}
"""


def check_category(item_list, category):
    """
    category 별 데이터 변경
    """
    if category == "Gun":
        return [
            item
            for item in item_list
            if item["category"]["parent"]["name"] == "Weapon"
            and item["properties"] != {}
        ]
    elif category == "Gun image":
        return [
            item
            for item in item_list
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
    elif category == "Headphones":
        return [item for item in item_list if item["category"]["name"] == category]
    elif category == "Headwear":
        return [
            item
            for item in item_list
            if item["category"]["name"] == category
            and item["name"] != "Maska-1SCh bulletproof helmet (Killa Edition) Default"
            and item["name"] != "Ops-Core FAST MT Super High Cut helmet (Black) RAC"
            and item["name"] != "Wilcox Skull Lock head mount PVS-14"
        ]
    elif category == "Food Drink":
        return [
            item
            for item in item_list
            if (
                item["category"]["name"] == "Food"
                or item["category"]["name"] == "Drink"
            )
            and item["properties"] != {}
        ]
    # elif weapon_category == "Armor":
    #     return [
    #         item
    #         for item in item_list
    #         if item["category"]["name"] == weapon_category and item["properties"] != {}
    #     ]
    # elif weapon_category == "Chest rig":
    #     return [
    #         item
    #         for item in item_list
    #         if item["category"]["name"] == weapon_category and item["properties"] != {}
    #     ]
    # elif weapon_category == "Backpack":
    #     return [
    #         item
    #         for item in item_list
    #         if item["category"]["name"] == weapon_category and item["properties"] != {}
    #     ]
    elif category == "Key":
        return [
            item
            for item in item_list
            if item["category"]["parent"]["name"] == "Key" and item["properties"] != {}
        ]
    else:
        return [
            item
            for item in item_list
            if item["category"]["name"] == category and item["properties"] != {}
        ]
