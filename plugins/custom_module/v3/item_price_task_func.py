from datetime import datetime


FLEA_MARKET_VENDOR_NAME = "Flea Market"


def generate_pvp_item_price_graphql(lang: str) -> str:
    return f"""
{{
  items(lang: {lang}) {{
    id
    category {{
      name
      parent {{
        name
      }}
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
    category {{
      name
      parent {{
        name
      }}
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


def v3_item_price_row(item_en, game_mode, trader_name_map):
    if not item_en:
        return None

    item_id = item_en.get("id")
    sell_for = item_en.get("sellFor") or []
    if not sell_for:
        return None
    highest_trader_price = None
    highest_trader_id = None
    flea_market_price = None
    trader_count = 0
    has_flea = False

    for sell in sell_for:
        vendor = sell.get("vendor") or {}
        vendor_name = vendor.get("name")
        price = sell.get("priceRUB")

        if price is None:
            continue

        if vendor_name == FLEA_MARKET_VENDOR_NAME:
            has_flea = True
            flea_market_price = price
            continue

        trader_id = trader_name_map.get(vendor_name)
        if not trader_id:
            print(
                f"[item_price] Missing trader mapping for vendor='{vendor_name}' item_id='{item_id}'"
            )
            continue

        trader_count += 1
        if highest_trader_price is None or price > highest_trader_price:
            highest_trader_price = price
            highest_trader_id = trader_id

    return (
        item_id,
        game_mode,
        highest_trader_price,
        highest_trader_id,
        flea_market_price,
        trader_count,
        has_flea,
    )


def v3_item_trader_price_rows(item_en, game_mode, trader_name_map):
    if not item_en:
        return []

    item_id = item_en.get("id")
    sell_for = item_en.get("sellFor") or []
    if not sell_for:
        return []
    rows = []

    for sell in sell_for:
        vendor = sell.get("vendor") or {}
        vendor_name = vendor.get("name")
        price = sell.get("priceRUB")

        if vendor_name == FLEA_MARKET_VENDOR_NAME or price is None:
            continue

        trader_id = trader_name_map.get(vendor_name)
        if not trader_id:
            print(
                f"[item_price] Skip trader row. Missing trader mapping for vendor='{vendor_name}' item_id='{item_id}'"
            )
            continue

        row_id = f"{game_mode}:{item_id}:{trader_id}"
        rows.append((row_id, item_id, game_mode, trader_id, price))

    return rows


def v3_item_price_history_rows(item_en, game_mode):
    if not item_en:
        return []

    item_id = item_en.get("id")
    sell_for = item_en.get("sellFor") or []
    if not sell_for:
        return []
    rows = []

    for price_info in item_en.get("historicalPrices") or []:
        price = price_info.get("price")
        timestamp = price_info.get("timestamp")

        if price is None or timestamp is None:
            continue

        try:
            price_time = datetime.utcfromtimestamp(int(timestamp) / 1000)
        except (TypeError, ValueError):
            continue

        rows.append((item_id, price, game_mode, price_time))

    return rows
