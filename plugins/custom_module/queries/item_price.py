"""SQL for item price. Execution and transactions belong to the caller."""


SELECT_TRADERS = "select id, name_en from traders"


ITEM_PRICE_SQL = """
            insert into item_prices (
                item_id,
                game_mode,
                season_id,
                highest_trader_price,
                highest_trader_id,
                flea_market_price,
                trader_count,
                has_flea
            )
            values %s
            on conflict (item_id, game_mode, season_key) do update
            set
                highest_trader_price = excluded.highest_trader_price,
                highest_trader_id = excluded.highest_trader_id,
                flea_market_price = excluded.flea_market_price,
                trader_count = excluded.trader_count,
                has_flea = excluded.has_flea,
                update_time = now()
        """


TRADER_PRICE_SQL = """
            insert into item_trader_prices (
                id,
                item_id,
                game_mode,
                season_id,
                trader_id,
                price
            )
            values %s
            on conflict (item_id, game_mode, season_key, trader_id) do update
            set
                item_id = excluded.item_id,
                game_mode = excluded.game_mode,
                trader_id = excluded.trader_id,
                price = excluded.price
        """


HISTORY_SQL = """
            insert into item_price_history (
                item_id,
                price,
                game_mode,
                season_id,
                price_time
            )
            values %s
            on conflict (item_id, game_mode, season_key, price_time) do update
            set
                price = excluded.price
        """


LOCK_PRICE_SEASONS = "LOCK TABLE price_seasons IN EXCLUSIVE MODE"


UPDATE_PRICE_SEASONS = "UPDATE price_seasons SET is_current = false WHERE is_current"


INSERT_PRICE_SEASONS = """INSERT INTO price_seasons (id, name, starts_at, ends_at, is_current)
                       VALUES (%s, %s, %s, %s, true)
                       ON CONFLICT (id) DO UPDATE SET name = excluded.name,
                           starts_at = excluded.starts_at, ends_at = excluded.ends_at,
                           is_current = true, update_time = now()"""


def build_delete_current_prices(table):
    return (f"DELETE FROM {table} WHERE "
                        "(game_mode IN ('pvp', 'pve') AND season_id IS NULL) OR "
                        "(game_mode = 'pvp-season' AND season_id = %s)"
    )


DELETE_ITEM_PRICE_HISTORY = ("DELETE FROM item_price_history WHERE game_mode IN ('pvp', 'pve') "
                    "AND season_id IS NULL AND price_time < now() - interval '14 days'"
)
