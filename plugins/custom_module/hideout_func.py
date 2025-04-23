def generate_hideout_stations_graphql(lang: str) -> str:
    return f"""
{{
  hideoutStations(lang: {lang}) {{
    id
    name
    levels {{
      id
      itemRequirements {{
        id
        item {{
          id
          name
          gridImageLink
        }}
        quantity
        count
      }}
      skillRequirements {{
        id
        name
        level
        skill {{
          id
          name
        }}
      }}
      traderRequirements {{
        id
        requirementType
        value
        trader {{
          name
          imageLink
        }}
        compareMethod
      }}
      stationLevelRequirements {{
        id
        level
        station {{
          id
          name
          imageLink
        }}
      }}
      level
      bonuses {{
        type
        name
        value
        skillName
      }}
      constructionTime
    }}
    imageLink
    crafts {{
      id
      station {{
        id
      }}
      level
      rewardItems {{
        item {{
          id
          name
          width
          height
          gridImageLink
        }}
        quantity
      }}
      duration
      requiredItems {{
        item {{
          id
          name
          gridImageLink
          width
          height
        }}
        quantity
      }}
    }}
  }}
}}
"""
