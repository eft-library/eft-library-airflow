def generate_quest_graphql(lang: str) -> str:
    return f"""
{{
  tasks(lang: {lang}) {{
    id
    name
    kappaRequired
    minPlayerLevel
    normalizedName
    experience
    availableDelaySecondsMin
    availableDelaySecondsMax
    wikiLink
    trader {{
      id
    }}
    taskRequirements {{
      task {{
        id
      }}
    }}
    objectives {{
      id
      type
      description
      ... on TaskObjectiveShoot {{
        count
      }}
      ... on TaskObjectiveQuestItem {{
        questItem {{
          id
        }}
        count
      }}
      ... on TaskObjectiveItem {{
        items {{
          id
        }}
        count
        foundInRaid
      }}
    }}
    finishRewards {{
      items {{
        item {{
          id
        }}
        quantity
      }}
      skillLevelReward{{
        name
        level
      }}
      traderStanding {{
        standing
        trader {{
          id
        }}
      }}
      offerUnlock {{
        trader {{
          id
        }}
        item {{
          id
        }}
        level
      }}
      craftUnlock {{
        station {{
          id
        }}
        level
        rewardItems {{
          item {{
            id
          }}
          quantity
        }}
      }}
    }}
  }}
}}
"""


def v3_quest_process(item_en, item_ko, item_ja):
    quest_id = item_en.get("id")
    normalized_name = item_en.get("normalizedName")
    name_en = item_en.get("name")
    name_ko = item_ko.get("name")
    name_ja = item_ja.get("name")
    trader_id = item_en["trader"].get("id")
    experience = item_en.get("experience")
    delay_max = item_en.get("delay_max")
    delay_min = item_en.get("delay_min")
    kappa_required = item_en.get("kappa_required")
    min_player_level = item_en.get("min_player_level")
    wiki_url = item_en.get("wiki_url")

    return (
        quest_id,
        normalized_name,
        name_en,
        name_ko,
        name_ja,
        trader_id,
        experience,
        delay_max,
        delay_min,
        kappa_required,
        min_player_level,
        wiki_url,
    )
