"""SQL for hideout. Execution and transactions belong to the caller."""


SELECT_HIDEOUT_MASTER = "select id, normalized_name, name_en, name_ko, name_ja from hideout_master"


SELECT_HIDEOUT_LEVELS = """
                        select hl.id, hl.master_id,
                               hl.master_id, hl.hideout_level, hl.construction_time
                        from hideout_levels hl
                    """


SELECT_HIDEOUT_SKILL_REQUIRE = """
                        select r.id, hl.master_id,
                               r.hideout_level_id, r.require_level, r.name_en
                        from hideout_skill_require r
                        join hideout_levels hl on hl.id = r.hideout_level_id
                    """


SELECT_HIDEOUT_TRADER_REQUIRE = """
                        select r.id, hl.master_id,
                               r.hideout_level_id, r.trader_id, r.trader_level
                        from hideout_trader_require r
                        join hideout_levels hl on hl.id = r.hideout_level_id
                    """


SELECT_HIDEOUT_STATION_REQUIRE = """
                        select r.id, hl.master_id,
                               r.hideout_level_id, r.require_master_id, r.station_level
                        from hideout_station_require r
                        join hideout_levels hl on hl.id = r.hideout_level_id
                    """


SELECT_HIDEOUT_ITEM_REQUIRE = """
                        select r.id, hl.master_id,
                               r.hideout_level_id, r.item_id, r.quantity, r.in_raid
                        from hideout_item_require r
                        join hideout_levels hl on hl.id = r.hideout_level_id
                    """


SELECT_HIDEOUT_CRAFTS = """
                        select c.id, hl.master_id,
                               c.hideout_level_id, c.reward_item_id, c.duration, c.reward_quantity
                        from hideout_crafts c
                        join hideout_levels hl on hl.id = c.hideout_level_id
                    """


SELECT_HIDEOUT_CRAFT_REQUIRE_ITEMS = """
                        select r.id, hl.master_id,
                               r.craft_id, r.item_id, r.quantity
                        from hideout_craft_require_items r
                        join hideout_crafts c on c.id = r.craft_id
                        join hideout_levels hl on hl.id = c.hideout_level_id
                    """


SELECT_HIDEOUT_BONUS = """
                        select b.id, hl.master_id,
                               b.hideout_level_id, b.bonus_type, b.name_en,
                               b.skill_name_en, b.bonus_value
                        from hideout_bonus b
                        join hideout_levels hl on hl.id = b.hideout_level_id
                    """


SELECT_ITEMS = "select id, name_en from items"


SELECT_TRADERS = "select id, name_en from traders"


MASTER_SQL = """
            insert into hideout_master (
                id,
                normalized_name,
                name_en,
                name_ko,
                name_ja
            )
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                normalized_name = EXCLUDED.normalized_name,
                name_en = EXCLUDED.name_en
        """


LEVEL_SQL = """
            insert into hideout_levels (id, master_id, hideout_level, construction_time)
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                master_id = EXCLUDED.master_id,
                hideout_level = EXCLUDED.hideout_level,
                construction_time = EXCLUDED.construction_time
        """


SKILL_REQUIRE_SQL = """
            insert into hideout_skill_require (
                id,
                hideout_level_id,
                require_level,
                name_en,
                name_ko,
                name_ja
            )
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                hideout_level_id = EXCLUDED.hideout_level_id,
                require_level = EXCLUDED.require_level,
                name_en = EXCLUDED.name_en
        """


TRADER_REQUIRE_SQL = """
            insert into hideout_trader_require (id, hideout_level_id, trader_id, trader_level)
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                hideout_level_id = EXCLUDED.hideout_level_id,
                trader_id = EXCLUDED.trader_id,
                trader_level = EXCLUDED.trader_level
        """


STATION_REQUIRE_SQL = """
            insert into hideout_station_require (id, hideout_level_id, require_master_id, station_level)
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                hideout_level_id = EXCLUDED.hideout_level_id,
                require_master_id = EXCLUDED.require_master_id,
                station_level = EXCLUDED.station_level
        """


ITEM_REQUIRE_SQL = """
            insert into hideout_item_require (id, hideout_level_id, item_id, quantity, in_raid)
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                hideout_level_id = EXCLUDED.hideout_level_id,
                item_id = EXCLUDED.item_id,
                quantity = EXCLUDED.quantity,
                in_raid = EXCLUDED.in_raid
        """


CRAFT_SQL = """
            insert into hideout_crafts (
                id,
                hideout_level_id,
                reward_item_id,
                duration,
                reward_quantity
            )
            values %s
            on conflict (id) do update
            set
                hideout_level_id = excluded.hideout_level_id,
                reward_item_id = excluded.reward_item_id,
                duration = excluded.duration,
                reward_quantity = excluded.reward_quantity
        """


CRAFT_REQUIRE_ITEM_SQL = """
            insert into hideout_craft_require_items (
                id,
                craft_id,
                item_id,
                quantity
            )
            values %s
            on conflict (id) do update
            set
                craft_id = excluded.craft_id,
                item_id = excluded.item_id,
                quantity = excluded.quantity
        """


BONUS_SQL = """
            insert into hideout_bonus (
                id,
                hideout_level_id,
                bonus_type,
                name_en,
                name_ko,
                name_ja,
                skill_name_en,
                skill_name_ko,
                skill_name_ja,
                bonus_value
            )
            values %s
            on conflict (id) do update
            set
                hideout_level_id = excluded.hideout_level_id,
                bonus_type = excluded.bonus_type,
                name_en = excluded.name_en,
                skill_name_en = excluded.skill_name_en,
                bonus_value = excluded.bonus_value
        """


SELECT_SKILL_REQUIRE_TRANSLATIONS = """
                    select id, name_ko, name_ja
                    from hideout_skill_require
                    """


SELECT_BONUS_TRANSLATIONS = """
                    select id, name_ko, name_ja, skill_name_ko, skill_name_ja
                    from hideout_bonus
                    """


TRUNCATE_HIDEOUT_LEVELS = """
                    truncate table
                        hideout_levels,
                        hideout_skill_require,
                        hideout_trader_require,
                        hideout_station_require,
                        hideout_item_require,
                        hideout_crafts,
                        hideout_craft_require_items,
                        hideout_bonus
                    restart identity cascade;
                """


SELECT_STATIC_HIDEOUT_TARGETS = """
                select normalized_name
                from hideout_master
                where normalized_name is not null
                order by name_en, normalized_name;
                """


INITIAL_MASTER_SQL = """
            insert into hideout_master (
                id,
                normalized_name,
                name_en,
                name_ko,
                name_ja
            )
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                normalized_name = EXCLUDED.normalized_name,
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja
        """


INITIAL_SKILL_REQUIRE_SQL = """
            insert into hideout_skill_require (
                id,
                hideout_level_id,
                require_level,
                name_en,
                name_ko,
                name_ja
            )
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                hideout_level_id = EXCLUDED.hideout_level_id,
                require_level = EXCLUDED.require_level,
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja
        """


INITIAL_BONUS_SQL = """
            insert into hideout_bonus (
                id,
                hideout_level_id,
                bonus_type,
                name_en,
                name_ko,
                name_ja,
                skill_name_en,
                skill_name_ko,
                skill_name_ja,
                bonus_value
            )
            values %s
            on conflict (id) do update
            set
                hideout_level_id = excluded.hideout_level_id,
                bonus_type = excluded.bonus_type,
                name_en = excluded.name_en,
                name_ko = excluded.name_ko,
                name_ja = excluded.name_ja,
                skill_name_en = excluded.skill_name_en,
                skill_name_ko = excluded.skill_name_ko,
                skill_name_ja = excluded.skill_name_ja,
                bonus_value = excluded.bonus_value
        """
