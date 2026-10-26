"""SQL for live map static point. Execution and transactions belong to the caller."""


SELECT_MAPS = """
                    select id,
                           normalized_name,
                           name_en
                    from maps
                    where is_use is true;
                    """


SELECT_LIVE_MAP_FLOORS = """
                    select id,
                           map_id,
                           floor_no,
                           min_y,
                           max_y,
                           sort_order
                    from live_map_floors
                    order by map_id, sort_order, floor_no;
                    """


SELECT_LIVE_MAP_FLOOR_ZONES = """
                    select id,
                           floor_id,
                           map_id,
                           area_x_min,
                           area_x_max,
                           area_z_min,
                           area_z_max,
                           override_min_y,
                           override_max_y,
                           sort_order
                    from live_map_floor_zones
                    order by map_id, sort_order nulls last, id;
                    """


SELECT_ITEMS = """
                    select id,
                           normalized_name,
                           name_en,
                           name_ko,
                           name_ja,
                           image
                    from items;
                    """


SELECT_BOSSES = """
                    select id,
                           normalized_name,
                           name_en,
                           name_ko,
                           name_ja,
                           image
                    from bosses;
                    """


SELECT_LIVE_MAP_STATIC_POINTS = """
                    select id,
                           map_id,
                           category,
                           name_en,
                           x,
                           z,
                           metadata
                    from live_map_static_points
                    where category in (
                        'boss_spawn',
                        'black_div_spawn',
                        'cultist_spawn',
                        'goons_spawn',
                        'raider_spawn',
                        'rogue_spawn'
                    );
                    """


INSERT_LIVE_MAP_STATIC_POINTS = """
                    INSERT INTO live_map_static_points (
                        id,
                        map_id,
                        floor_id,
                        category,
                        name_en,
                        name_ko,
                        name_ja,
                        description_en,
                        description_ko,
                        description_ja,
                        image,
                        x,
                        z,
                        metadata,
                        sort_order,
                        is_use
                    )
                    VALUES %s
                    ON CONFLICT (id) DO NOTHING
                """


COUNT_STATIC_POINTS_WITH_METADATA = """
                        select count(*)
                        from live_map_static_points
                        where id = any(%s)
                          and metadata is not null;
                        """
