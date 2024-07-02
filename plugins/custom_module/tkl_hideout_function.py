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
          image512pxLink
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
          imageLink
        }
        compareMethod
      }
      stationLevelRequirements {
        id
        level
        station {
          name
          imageLink
        }
      }
      id
      level
      bonuses {
        type
        name
        value
        skillName
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