"""SQL for quest. Execution and transactions belong to the caller."""


SELECT_QUESTS = """
                    select id, normalized_name, name_en, name_ko, name_ja,
                           trader_id, experience, delay_max, delay_min,
                           kappa_required, min_player_level, wiki_url
                    from quests
                    """


SELECT_QUEST_OBJECTIVES = """
                    select objective_id, quest_id, type, description_en,
                           description_ko, description_ja,
                           count, found_in_raid, optional, sort_order
                    from quest_objectives
                    """


SELECT_QUEST_OBJECTIVE_ITEMS = "select objective_id, item_id, item_type from quest_objective_items"


SELECT_QUEST_OBJECTIVE_REQUIRED_KEYS = "select objective_id, key_id from quest_objective_required_keys"


SELECT_QUEST_OBJECTIVE_MAPS = "select objective_id, map_id from quest_objective_maps"


SELECT_QUEST_RELATIONS = """
                    select quest_id, related_quest_id, relation_type
                    from quest_relations
                    where relation_type = 'require'
                    """


SELECT_QUEST_FINISH_REWARD_SKILLS = """
                        select quest_id, name_en, skill_level
                        from quest_finish_reward_skills
                    """


SELECT_QUEST_FINISH_REWARD_TRADER_STANDING = """
                        select quest_id, trader_id, standing
                        from quest_finish_reward_trader_standing
                    """


SELECT_QUEST_FINISH_REWARD_OFFER_UNLOCK = """
                        select quest_id, offer_id, trader_id, item_id, level
                        from quest_finish_reward_offer_unlock
                    """


SELECT_QUEST_FINISH_REWARD_ITEMS = """
                        select quest_id, item_id, quantity
                        from quest_finish_reward_items
                    """


SELECT_QUEST_FINISH_REWARD_CRAFT_UNLOCKS = """
                        select quest_id, craft_id, station_level
                        from quest_finish_reward_craft_unlocks
                    """


SELECT_ITEMS = "select id, name_en from items"


SELECT_MAPS = "select id, name_en from maps"


SELECT_TRADERS = "select id, name_en from traders"


QUEST_SQL = """
            INSERT INTO quests (
                id,
                normalized_name,
                name_en,
                name_ko,
                name_ja,
                trader_id,
                experience,
                delay_max,
                delay_min,
                kappa_required,
                min_player_level,
                wiki_url,
                is_use
            )
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                normalized_name = EXCLUDED.normalized_name,
                name_en = EXCLUDED.name_en,
                name_ko = COALESCE(EXCLUDED.name_ko, quests.name_ko),
                name_ja = COALESCE(EXCLUDED.name_ja, quests.name_ja),
                trader_id = EXCLUDED.trader_id,
                experience = EXCLUDED.experience,
                delay_max = EXCLUDED.delay_max,
                delay_min = EXCLUDED.delay_min,
                kappa_required = EXCLUDED.kappa_required,
                min_player_level = EXCLUDED.min_player_level,
                wiki_url = EXCLUDED.wiki_url,
                update_time = now()
        """


OBJECTIVE_SQL = """
            INSERT INTO quest_objectives (
                objective_id,
                quest_id,
                type,
                description_en,
                description_ko,
                description_ja,
                count,
                found_in_raid,
                optional,
                sort_order,
                is_use
            )
            VALUES %s
            ON CONFLICT (objective_id, quest_id) DO UPDATE
            SET
                type = EXCLUDED.type,
                description_en = EXCLUDED.description_en,
                count = EXCLUDED.count,
                found_in_raid = EXCLUDED.found_in_raid,
                optional = EXCLUDED.optional,
                sort_order = EXCLUDED.sort_order,
                update_time = now()
        """


OBJECTIVE_ITEM_SQL = """
            INSERT INTO quest_objective_items (
                objective_id,
                item_id,
                item_type
            )
            VALUES %s
            ON CONFLICT (objective_id, item_id, item_type) DO NOTHING
        """


OBJECTIVE_REQUIRED_KEY_SQL = """
            INSERT INTO quest_objective_required_keys (
                objective_id,
                key_id
            )
            VALUES %s
            ON CONFLICT (objective_id, key_id) DO NOTHING
        """


OBJECTIVE_MAP_SQL = """
            INSERT INTO quest_objective_maps (
                objective_id,
                map_id
            )
            VALUES %s
            ON CONFLICT (objective_id, map_id) DO NOTHING
        """


RELATION_SQL = """
            INSERT INTO quest_relations (
                quest_id,
                related_quest_id,
                relation_type
            )
            VALUES %s
            ON CONFLICT (quest_id, related_quest_id, relation_type) DO NOTHING
        """


SKILL_REWARD_SQL = """
            INSERT INTO quest_finish_reward_skills (
                quest_id,
                name_en,
                name_ko,
                name_ja,
                skill_level
            )
            VALUES %s
        """


STANDING_REWARD_SQL = """
            INSERT INTO quest_finish_reward_trader_standing (
                quest_id,
                trader_id,
                standing
            )
            VALUES %s
        """


OFFER_REWARD_SQL = """
            INSERT INTO quest_finish_reward_offer_unlock (
                quest_id,
                offer_id,
                trader_id,
                item_id,
                level
            )
            VALUES %s
        """


FINISH_REWARD_ITEM_SQL = """
            INSERT INTO quest_finish_reward_items (
                quest_id,
                item_id,
                quantity
            )
            VALUES %s
        """


FINISH_REWARD_CRAFT_UNLOCK_SQL = """
            INSERT INTO quest_finish_reward_craft_unlocks (
                quest_id,
                craft_id,
                station_level
            )
            VALUES %s
        """


CUSTOMIZATION_SQL = """
            INSERT INTO customizations (
                id, name_key, name_en, name_ko, name_ja, image_link,
                customization_type, customization_type_name_key,
                customization_type_name_en, customization_type_name_ko,
                customization_type_name_ja
            ) VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                name_key = EXCLUDED.name_key,
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja,
                image_link = EXCLUDED.image_link,
                customization_type = EXCLUDED.customization_type,
                customization_type_name_key = EXCLUDED.customization_type_name_key,
                customization_type_name_en = EXCLUDED.customization_type_name_en,
                customization_type_name_ko = EXCLUDED.customization_type_name_ko,
                customization_type_name_ja = EXCLUDED.customization_type_name_ja,
                update_time = now()
        """


CUSTOMIZATION_ITEM_SQL = """
            INSERT INTO customization_items (
                customization_id, item_id, sort_order
            ) VALUES %s
            ON CONFLICT (customization_id, item_id) DO UPDATE SET
                sort_order = EXCLUDED.sort_order
        """


QUEST_REWARD_CUSTOMIZATION_SQL = """
            INSERT INTO quest_reward_customizations (
                quest_id, customization_id, reward_type, sort_order
            ) VALUES %s
            ON CONFLICT (quest_id, customization_id, reward_type) DO UPDATE SET
                sort_order = EXCLUDED.sort_order,
                update_time = now()
        """


SELECT_SKILL_REWARD_TRANSLATIONS = """
                    select quest_id, name_en, skill_level, name_ko, name_ja
                    from quest_finish_reward_skills
                    """


TRUNCATE_QUEST_OBJECTIVE_ITEMS = """
                    truncate table
                        quest_objective_items,
                        quest_objective_required_keys,
                        quest_objective_maps,
                        quest_relations,
                        quest_finish_reward_skills,
                        quest_finish_reward_trader_standing,
                        quest_finish_reward_offer_unlock,
                        quest_finish_reward_items,
                        quest_finish_reward_craft_unlocks
                    restart identity cascade;
                """


INSERT_QUEST_RELATIONS = """
                    insert into quest_relations (
                        quest_id,
                        related_quest_id,
                        relation_type,
                        sort_order
                    )
                    select
                        related_quest_id as quest_id,
                        quest_id as related_quest_id,
                        'next' as relation_type,
                        sort_order
                    from quest_relations
                    where relation_type = 'require'
                    on conflict (quest_id, related_quest_id, relation_type) do nothing
                    """


INSERT_ROADMAP_NODE = """
                    insert into roadmap_node (
                        id,
                        total_x_coordinate,
                        total_y_coordinate,
                        single_x_coordinate,
                        single_y_coordinate,
                        total_kappa_x_coordinate,
                        total_kappa_y_coordinate,
                        single_kappa_x_coordinate,
                        single_kappa_y_coordinate
                    )
                    select
                        q.id,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    from quests q
                    where q.is_use is true
                    on conflict (id) do nothing
                    """


SELECT_STATIC_QUEST_TARGETS = """
                select normalized_name
                from quests
                where is_use is true
                  and normalized_name is not null
                order by sort_order, name_en, normalized_name;
                """


SELECT_STATIC_TRADER_TARGETS = """
                select normalized_name
                from traders
                where normalized_name is not null
                order by name_en, normalized_name;
                """


INITIAL_QUEST_SQL = """
            INSERT INTO quests (
                id,
                normalized_name,
                name_en,
                name_ko,
                name_ja,
                trader_id,
                experience,
                delay_max,
                delay_min,
                kappa_required,
                min_player_level,
                wiki_url,
                is_use
            )
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                normalized_name = EXCLUDED.normalized_name,
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja,
                trader_id = EXCLUDED.trader_id,
                experience = EXCLUDED.experience,
                delay_max = EXCLUDED.delay_max,
                delay_min = EXCLUDED.delay_min,
                kappa_required = EXCLUDED.kappa_required,
                min_player_level = EXCLUDED.min_player_level,
                wiki_url = EXCLUDED.wiki_url,
                update_time = now()
        """


INITIAL_OBJECTIVE_SQL = """
            INSERT INTO quest_objectives (
                objective_id,
                quest_id,
                type,
                description_en,
                description_ko,
                description_ja,
                count,
                found_in_raid,
                optional,
                sort_order,
                is_use
            )
            VALUES %s
            ON CONFLICT (objective_id, quest_id) DO UPDATE
            SET
                type = EXCLUDED.type,
                description_en = EXCLUDED.description_en,
                description_ko = EXCLUDED.description_ko,
                description_ja = EXCLUDED.description_ja,
                count = EXCLUDED.count,
                found_in_raid = EXCLUDED.found_in_raid,
                optional = EXCLUDED.optional,
                sort_order = EXCLUDED.sort_order,
                update_time = now()
        """
