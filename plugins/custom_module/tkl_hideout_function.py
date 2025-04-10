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
          id
          name
          gridImageLink
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
          id
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
          id
          name
          width
          height
          gridImageLink
        }
        quantity
      }
      duration
      requiredItems {
        item {
          name
          gridImageLink
          width
          height
        }
        quantity
      }
    }
  }
}
"""