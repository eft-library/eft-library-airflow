"""SQL for trader. Execution and transactions belong to the caller."""


SELECT_TRADERS = """
                    select id, name_en, name_ko, name_ja, image, normalized_name
                    from traders
                    """


SELECT_TRADER_BARTERS = "select id, trader_id, trader_level from trader_barters"


SELECT_BARTER_REQUIRED_ITEMS = """
                        select r.id, b.trader_id, r.barter_id, r.item_id, r.quantity
                        from barter_required_items r
                        join trader_barters b on b.id = r.barter_id
                    """


SELECT_BARTER_REWARD_ITEMS = """
                        select r.id, b.trader_id, r.barter_id, r.item_id, r.quantity
                        from barter_reward_items r
                        join trader_barters b on b.id = r.barter_id
                    """


SELECT_ITEMS = "select id, name_en from items"


TRADER_SQL = """
            insert into traders (id, name_en, name_ko, name_ja, image, normalized_name)
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                name_en = EXCLUDED.name_en,
                image = EXCLUDED.image,
                normalized_name = EXCLUDED.normalized_name,
                update_time = now()
        """


BARTER_SQL = """
            insert into trader_barters (
                id,
                trader_id,
                trader_level
            )
            values %s
            on conflict (id) do update
            set
                trader_id = excluded.trader_id,
                trader_level = excluded.trader_level
        """


BARTER_REQUIRED_SQL = """
            insert into barter_required_items (
                id,
                barter_id,
                item_id,
                quantity
            )
            values %s
            on conflict (id) do update
            set
                barter_id = excluded.barter_id,
                item_id = excluded.item_id,
                quantity = excluded.quantity
        """


BARTER_REWARD_SQL = """
            insert into barter_reward_items (
                id,
                barter_id,
                item_id,
                quantity
            )
            values %s
            on conflict (id) do update
            set
                barter_id = excluded.barter_id,
                item_id = excluded.item_id,
                quantity = excluded.quantity
        """


TRUNCATE_TRADER_BARTERS = """
                    truncate table
                        trader_barters,
                        barter_required_items,
                        barter_reward_items
                    restart identity cascade;
                """


INITIAL_TRADER_SQL = """
            insert into traders (id, name_en, name_ko, name_ja, image, normalized_name)
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja,
                image = EXCLUDED.image,
                normalized_name = EXCLUDED.normalized_name,
                update_time = now()
        """
