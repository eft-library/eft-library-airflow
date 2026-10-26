"""SQL for live map point. Execution and transactions belong to the caller."""


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


INSERT_LIVE_MAP_POINTS = """
                        INSERT INTO live_map_points (
                            id,
                            quest_id,
                            objective_id,
                            map_id,
                            floor_id,
                            x,
                            z
                        )
                        VALUES %s
                        ON CONFLICT (id) DO NOTHING
                        """


INSERT_LIVE_MAP_POINT_DETAILS = """
                        INSERT INTO live_map_point_details (
                            id,
                            point_id,
                            description_en,
                            description_ko,
                            description_ja,
                            image,
                            sort_order
                        )
                        VALUES %s
                        ON CONFLICT (id) DO NOTHING
                        """
