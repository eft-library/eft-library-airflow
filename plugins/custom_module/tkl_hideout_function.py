hideout_graphql = """
{
  hideoutStations {
    id
    name
    levels {
      id
      itemRequirements {
        id
        item {
          name
        }
        quantity
        count
      }
      skillRequirements {
        id
        name
        level
        skill {
          id
          name
        }
      }
      traderRequirements {
        id
        requirementType
        value
        trader {
          name
        }
        compareMethod
      }
      stationLevelRequirements {
        id
        level
        station {
          name
        }
      }
      id
      level
      bonuses {
        type
        name
        value
        passive
        slotItems {
          name
        }
        skillName
        production
      }
      constructionTime
    }
    imageLink
    crafts {
      id
      station {
        id
      }
      level
      rewardItems {
        item {
          name
        }
      }
    }
  }
}
"""