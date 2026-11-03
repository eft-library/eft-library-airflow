"""SQL for mode-scoped trader offers. Caller owns the transaction."""

UPSERT_SEASON = """
INSERT INTO price_seasons (id, name, starts_at, ends_at, is_current)
VALUES (%s, %s, %s, %s, false)
ON CONFLICT (id) DO UPDATE SET name=excluded.name,
 starts_at=excluded.starts_at, ends_at=excluded.ends_at, update_time=now()
"""

UPSERT_OFFERS = """
INSERT INTO trader_offers
 (id, source_offer_id, trader_id, trader_level, offer_type, game_mode, season_id,
  buy_limit, raw_buy_limit, is_unlimited, sort_order)
VALUES %s
ON CONFLICT (source_offer_id, game_mode, season_key) DO UPDATE SET
 trader_id=excluded.trader_id, trader_level=excluded.trader_level,
 offer_type=excluded.offer_type, buy_limit=excluded.buy_limit,
 raw_buy_limit=excluded.raw_buy_limit, is_unlimited=excluded.is_unlimited,
 sort_order=excluded.sort_order, is_use=true, collected_at=now(), update_time=now()
"""

DEACTIVATE_MISSING = """
UPDATE trader_offers SET is_use=false, update_time=now()
WHERE game_mode=%s AND season_id IS NOT DISTINCT FROM %s
 AND NOT (id = ANY(%s)) AND is_use
"""

UPSERT_RESTOCKS = """
INSERT INTO trader_restock_state (trader_id, game_mode, season_id, next_restock_at)
VALUES %s
ON CONFLICT (trader_id, game_mode, season_key) DO UPDATE SET
 next_restock_at=excluded.next_restock_at, collected_at=now(), update_time=now()
"""
