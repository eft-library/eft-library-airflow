def generate_trader_graphql(lang: str) -> str:
    return f"""
{{
  traders(lang: {lang}) {{
    id
    name
    imageLink
    barters {{
      level
      requiredItems {{
        item {{
          id
        }}
        quantity
      }}
      rewardItems {{
        item {{
          id
        }}
        quantity
      }}
    }}
  }}
}}
"""


def v3_trader_process(item_en, item_ko, item_ja):
    trader_id = item_en.get("id")
    name_en = item_en.get("name")
    name_ko = item_ko.get("name")
    name_ja = item_ja.get("name")
    image = item_en.get("imageLink")

    return (trader_id, name_en, name_ko, name_ja, image)


def v3_trader_barter_process(trader_en):
    barter_rows = []
    required_rows = []
    reward_rows = []

    trader_id = trader_en.get("id")
    barters = trader_en.get("barters", [])

    if not trader_id:
        return barter_rows, required_rows, reward_rows

    for barter_idx, barter in enumerate(barters):
        trader_level = barter.get("level")
        if trader_level is None:
            continue

        barter_id = f"{trader_id}-barter-{barter_idx}"

        barter_rows.append(
            (
                barter_id,
                trader_id,
                trader_level,
            )
        )

        required_items = barter.get("requiredItems", [])
        for req_idx, req in enumerate(required_items):
            item_id = req.get("item", {}).get("id")
            quantity = req.get("quantity", 0)

            if not item_id:
                continue

            required_id = f"{barter_id}-req-{req_idx}"

            required_rows.append(
                (
                    required_id,
                    barter_id,
                    item_id,
                    quantity,
                )
            )

        reward_items = barter.get("rewardItems", [])
        for reward_idx, reward in enumerate(reward_items):
            item_id = reward.get("item", {}).get("id")
            quantity = reward.get("quantity", 0)

            if not item_id:
                continue

            reward_id = f"{barter_id}-reward-{reward_idx}"

            reward_rows.append(
                (
                    reward_id,
                    barter_id,
                    item_id,
                    quantity,
                )
            )

    return barter_rows, required_rows, reward_rows
