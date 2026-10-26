"""SQL for prestige. Execution and transactions belong to the caller."""


INSERT_PRESTIGE_LEVELS = """
            insert into prestige_levels (
                id, prestige_level, name_key, name_en, name_ko, name_ja,
                icon_link, image_link, is_use, sort_order
            ) values %s
            on conflict (id) do update set
                prestige_level = excluded.prestige_level,
                name_key = excluded.name_key,
                name_en = excluded.name_en,
                name_ko = excluded.name_ko,
                name_ja = excluded.name_ja,
                icon_link = excluded.icon_link,
                image_link = excluded.image_link,
                is_use = excluded.is_use,
                sort_order = excluded.sort_order,
                update_time = now()
        """


INSERT_PRESTIGE_CONDITIONS = """
            insert into prestige_conditions (
                id, prestige_id, condition_type, description_key,
                description_en, description_ko, description_ja, count,
                is_optional, player_level, task_id, station_id, station_level,
                skill_name, skill_level, dog_tag_level, max_durability,
                min_durability, found_in_raid, sort_order
            ) values %s
            on conflict (id) do update set
                prestige_id = excluded.prestige_id,
                condition_type = excluded.condition_type,
                description_key = excluded.description_key,
                description_en = excluded.description_en,
                description_ko = excluded.description_ko,
                description_ja = excluded.description_ja,
                count = excluded.count,
                is_optional = excluded.is_optional,
                player_level = excluded.player_level,
                task_id = excluded.task_id,
                station_id = excluded.station_id,
                station_level = excluded.station_level,
                skill_name = excluded.skill_name,
                skill_level = excluded.skill_level,
                dog_tag_level = excluded.dog_tag_level,
                max_durability = excluded.max_durability,
                min_durability = excluded.min_durability,
                found_in_raid = excluded.found_in_raid,
                sort_order = excluded.sort_order,
                update_time = now()
        """


INSERT_PRESTIGE_CONDITION_ITEMS = """
            insert into prestige_condition_items (condition_id, item_id, sort_order)
            values %s on conflict (condition_id, item_id) do update set
                sort_order = excluded.sort_order
        """


INSERT_PRESTIGE_CONDITION_STATUSES = """
            insert into prestige_condition_statuses (condition_id, status, sort_order)
            values %s on conflict (condition_id, status) do update set
                sort_order = excluded.sort_order
        """


INSERT_PRESTIGE_CONDITION_MAPS = """
            insert into prestige_condition_maps (condition_id, map_id, sort_order)
            values %s on conflict (condition_id, map_id) do update set
                sort_order = excluded.sort_order
        """


INSERT_PRESTIGE_REWARD_ITEMS = """
            insert into prestige_reward_items (
                prestige_id, item_id, quantity, attributes, sort_order
            ) values %s on conflict (prestige_id, item_id) do update set
                quantity = excluded.quantity,
                attributes = excluded.attributes,
                sort_order = excluded.sort_order
        """


INSERT_PRESTIGE_REWARD_SKILLS = """
            insert into prestige_reward_skills (
                prestige_id, skill_name, skill_level, sort_order
            ) values %s on conflict (prestige_id, skill_name) do update set
                skill_level = excluded.skill_level,
                sort_order = excluded.sort_order
        """


INSERT_CUSTOMIZATIONS = """
            insert into customizations (
                id, name_key, name_en, name_ko,
                name_ja, image_link, customization_type,
                customization_type_name_key, customization_type_name_en,
                customization_type_name_ko, customization_type_name_ja
            ) values %s on conflict (id) do update set
                name_key = excluded.name_key,
                name_en = excluded.name_en,
                name_ko = excluded.name_ko,
                name_ja = excluded.name_ja,
                image_link = excluded.image_link,
                customization_type = excluded.customization_type,
                customization_type_name_key = excluded.customization_type_name_key,
                customization_type_name_en = excluded.customization_type_name_en,
                customization_type_name_ko = excluded.customization_type_name_ko,
                customization_type_name_ja = excluded.customization_type_name_ja,
                update_time = now()
        """


INSERT_CUSTOMIZATION_ITEMS = """
            insert into customization_items (
                customization_id, item_id, sort_order
            ) values %s on conflict (customization_id, item_id) do update set
                sort_order = excluded.sort_order
        """


INSERT_PRESTIGE_REWARD_CUSTOMIZATIONS = """
            insert into prestige_reward_customizations (
                prestige_id, customization_id, sort_order
            ) values %s on conflict (prestige_id, customization_id) do update set
                sort_order = excluded.sort_order
        """


INSERT_PRESTIGE_TRANSFER_SETTINGS = """
            insert into prestige_transfer_settings (
                id, prestige_id, setting_type, name_key, name_en, name_ko,
                name_ja, skill_type, transfer_rate, grid_width, grid_height,
                sort_order
            ) values %s on conflict (id) do update set
                prestige_id = excluded.prestige_id,
                setting_type = excluded.setting_type,
                name_key = excluded.name_key,
                name_en = excluded.name_en,
                name_ko = excluded.name_ko,
                name_ja = excluded.name_ja,
                skill_type = excluded.skill_type,
                transfer_rate = excluded.transfer_rate,
                grid_width = excluded.grid_width,
                grid_height = excluded.grid_height,
                sort_order = excluded.sort_order,
                update_time = now()
        """


INSERT_PRESTIGE_TRANSFER_FILTER_VALUES = """
            insert into prestige_transfer_filter_values (
                transfer_setting_id, filter_type, value_id, sort_order
            ) values %s
            on conflict (transfer_setting_id, filter_type, value_id) do update set
                sort_order = excluded.sort_order
        """
