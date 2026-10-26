"""SQL for boss. Execution and transactions belong to the caller."""


SELECT_BOSSES = """
                    select id, name_en, name_ko, name_ja, image, normalized_name,
                           health_total, head_hp, thorax_hp, stomach_hp,
                           left_arm_hp, right_arm_hp, left_leg_hp, right_leg_hp
                    from bosses
                    """


SELECT_BOSS_SPAWN = "select boss_id, map_id, spawn_chance from boss_spawn"


SELECT_MAPS = "select id, name_en from maps"


BOSS_SQL = """
            insert into bosses (
                id, name_en, name_ko, name_ja, image, normalized_name,
                health_total, head_hp, thorax_hp, stomach_hp,
                left_arm_hp, right_arm_hp, left_leg_hp, right_leg_hp
            )
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                name_en = EXCLUDED.name_en,
                image = EXCLUDED.image,
                normalized_name = EXCLUDED.normalized_name,
                health_total = EXCLUDED.health_total,
                head_hp = EXCLUDED.head_hp,
                thorax_hp = EXCLUDED.thorax_hp,
                stomach_hp = EXCLUDED.stomach_hp,
                left_arm_hp = EXCLUDED.left_arm_hp,
                right_arm_hp = EXCLUDED.right_arm_hp,
                left_leg_hp = EXCLUDED.left_leg_hp,
                right_leg_hp = EXCLUDED.right_leg_hp,
                update_time = now()
        """


BOSS_ITEM_SQL = """
            insert into boss_item (boss_id, item_id, quantity)
            values %s
            ON CONFLICT (boss_id, item_id) DO UPDATE
            SET quantity = EXCLUDED.quantity
        """


TRUNCATE_BOSS_ITEM = """
                    truncate table
                        boss_item
                    restart identity cascade;
                """


INSERT_BOSS_SPAWN = """
            insert into boss_spawn (boss_id, map_id, spawn_chance)
            values %s
            ON CONFLICT (boss_id, map_id) DO UPDATE
            SET spawn_chance = EXCLUDED.spawn_chance
        """


TRUNCATE_BOSS_SPAWN = """
                    truncate table
                        boss_spawn
                    restart identity cascade;
                    """


SELECT_STATIC_BOSS_TARGETS = """
                select normalized_name
                from bosses
                where normalized_name is not null
                order by name_en, normalized_name;
                """


INITIAL_BOSS_SQL = """
            insert into bosses (
                id, name_en, name_ko, name_ja, image, normalized_name,
                health_total, head_hp, thorax_hp, stomach_hp,
                left_arm_hp, right_arm_hp, left_leg_hp, right_leg_hp
            )
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja,
                image = EXCLUDED.image,
                normalized_name = EXCLUDED.normalized_name,
                health_total = EXCLUDED.health_total,
                head_hp = EXCLUDED.head_hp,
                thorax_hp = EXCLUDED.thorax_hp,
                stomach_hp = EXCLUDED.stomach_hp,
                left_arm_hp = EXCLUDED.left_arm_hp,
                right_arm_hp = EXCLUDED.right_arm_hp,
                left_leg_hp = EXCLUDED.left_leg_hp,
                right_leg_hp = EXCLUDED.right_leg_hp,
                update_time = now()
        """
