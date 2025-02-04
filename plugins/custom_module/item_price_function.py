
pvp_item_price_graphql = """
{
  items {
    id
    name
    image512pxLink
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
    image512pxLink
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

