
pvp_item_price_graphql = """
{
  items {
    id
    name
    gridImageLink
    width
    height
    category {
      name
    }
    sellFor {
      priceRUB
      vendor {
        name
      }
    }
    historicalPrices {
      price
      timestamp
    }
  }
}
"""

pve_item_price_graphql = """
{
  items(gameMode: pve) {
    id
    name
    gridImageLink
    width
    height
    sellFor {
      priceRUB
      vendor {
        name
      }
    }
    historicalPrices {
      price
      timestamp
    }
  }
}
"""

