def generate_pvp_item_price_graphql(lang: str) -> str:
    return f"""
{{
  items(lang: {lang}, gameMode: pvp) {{
    id
    name
    gridImageLink
    width
    height
    category {{
      name
    }}
    sellFor {{
      priceRUB
      vendor {{
        name
      }}
    }}
    historicalPrices {{
      price
      timestamp
    }}
  }}
}}
"""


def generate_pve_item_price_graphql(lang: str) -> str:
    return f"""
{{
  items(lang: {lang}, gameMode: pve) {{
    id
    name
    gridImageLink
    width
    height
    category {{
      name
    }}
    sellFor {{
      priceRUB
      vendor {{
        name
      }}
    }}
    historicalPrices {{
      price
      timestamp
    }}
  }}
}}
"""
