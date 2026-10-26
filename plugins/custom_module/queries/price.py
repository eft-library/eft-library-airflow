"""SQL for price. Execution and transactions belong to the caller."""


SELECT_PRICE_SEASONS = "SELECT id FROM price_seasons WHERE is_current"


SELECT_ITEMS = """
                select i.id,
                       i.normalized_name,
                       i.name_en,
                       i.name_ko,
                       i.name_ja,
                       i.image,
                       i.category,
                       i.parent_category,
                       i.width,
                       i.height
                from items i
                where i.normalized_name is not null
                  and exists (
                      select 1
                      from item_prices ip
                      where ip.item_id = i.id
                        and (ip.season_id is null or ip.season_id = (select id from price_seasons where is_current))
                  )
                order by i.name_en, i.normalized_name;
                """


SELECT_ITEM_PRICES = """
                select item_id,
                       game_mode,
                       season_id,
                       highest_trader_price,
                       highest_trader_id,
                       flea_market_price,
                       trader_count,
                       has_flea,
                       update_time
                from item_prices
                where season_id is null or season_id = (select id from price_seasons where is_current)
                order by item_id, game_mode;
                """


SELECT_ITEM_PRICE_HISTORY = """
                select iph.item_id,
                       iph.game_mode,
                       iph.season_id,
                       iph.price,
                       iph.price_time
                from item_price_history iph
                join item_prices ip
                  on ip.item_id = iph.item_id
                 and ip.game_mode = iph.game_mode
                 and ip.season_key = iph.season_key
                where iph.season_id is null or iph.season_id = (select id from price_seasons where is_current)
                order by iph.item_id, iph.game_mode, iph.price_time;
                """


SELECT_ITEM_TRADER_PRICES = """
                select itp.id,
                       itp.item_id,
                       itp.game_mode,
                       itp.season_id,
                       itp.trader_id,
                       itp.price,
                       t.normalized_name as trader_normalized_name,
                       t.name_en as trader_name_en,
                       t.name_ko as trader_name_ko,
                       t.name_ja as trader_name_ja,
                       t.image as trader_image
                from item_trader_prices itp
                         left join traders t on itp.trader_id = t.id
                where itp.season_id is null or itp.season_id = (select id from price_seasons where is_current)
                order by itp.item_id, itp.game_mode, itp.price desc;
                """
