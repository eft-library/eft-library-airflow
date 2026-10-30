"""SQL for item. Execution and transactions belong to the caller."""


SELECT_ITEMS = "select id, normalized_name from items where normalized_name is not null"


TRUNCATE_ITEM_PENALTIES = """
                truncate table
                    item_penalties,
                    weapon_items,
                    weapon_allowed_ammo,
                    ammo_items,
                    melee_items,
                    throwable_items,
                    storage_items,
                    storage_grids,
                    protection_items,
                    consumable_items,
                    consumable_cures,
                    consumable_stim_effects,
                    usage_items,
                    ammo_efficiency
                restart identity cascade;
            """


INSERT_ITEMS = """
                insert into items (
                    id, parent_category, category, name_en, name_ko, name_ja, normalized_name, weight, width, height, image
                ) values %s
                on conflict (id) do update set
                    parent_category=excluded.parent_category,
                    category=excluded.category,
                    name_en=excluded.name_en,
                    name_ko=COALESCE(NULLIF(excluded.name_ko, ''), items.name_ko),
                    name_ja=COALESCE(NULLIF(excluded.name_ja, ''), items.name_ja),
                    normalized_name=excluded.normalized_name,
                    weight=excluded.weight,
                    width=excluded.width,
                    height=excluded.height,
                    image=excluded.image,
                    update_time=now()
                """


INSERT_AMMO_EFFICIENCY = """
                    insert into ammo_efficiency (
                        ammo_item_id, value_1, value_2, value_3, value_4, value_5, value_6
                    ) values %s
                    on conflict (ammo_item_id) do update set
                        value_1=excluded.value_1,
                        value_2=excluded.value_2,
                        value_3=excluded.value_3,
                        value_4=excluded.value_4,
                        value_5=excluded.value_5,
                        value_6=excluded.value_6
                    """


INSERT_ITEM_PENALTIES = """
                    insert into item_penalties (
                        item_id, ergonomics_penalty, turn_speed_penalty, movement_speed_penalty, distance_modifier
                    ) values %s
                    on conflict (item_id) do update set
                        ergonomics_penalty=excluded.ergonomics_penalty,
                        turn_speed_penalty=excluded.turn_speed_penalty,
                        movement_speed_penalty=excluded.movement_speed_penalty,
                        distance_modifier=excluded.distance_modifier
                """


INSERT_WEAPON_ITEMS = """
                    insert into weapon_items (
                        item_id, caliber, fire_rate, ergonomics, recoil_horizontal, recoil_vertical, default_ammo_item_id,
                        is_single_fire, is_full_auto, is_burst_fire, is_double_action, is_double_tap, is_semi_auto
                    ) values %s
                    on conflict (item_id) do update set
                        caliber=excluded.caliber,
                        fire_rate=excluded.fire_rate,
                        ergonomics=excluded.ergonomics,
                        recoil_horizontal=excluded.recoil_horizontal,
                        recoil_vertical=excluded.recoil_vertical,
                        default_ammo_item_id=excluded.default_ammo_item_id,
                        is_single_fire=excluded.is_single_fire,
                        is_full_auto=excluded.is_full_auto,
                        is_burst_fire=excluded.is_burst_fire,
                        is_double_action=excluded.is_double_action,
                        is_double_tap=excluded.is_double_tap,
                        is_semi_auto=excluded.is_semi_auto
                """


INSERT_WEAPON_ALLOWED_AMMO = """
                    insert into weapon_allowed_ammo (
                        item_id, ammo_item_id
                    ) values %s
                    on conflict (item_id, ammo_item_id) do nothing
                """


INSERT_AMMO_ITEMS = """
                    insert into ammo_items (
                        item_id, damage, armor_damage, penetration_power, recoil_modifier, accuracy_modifier, heavy_bleed_modifier, light_bleed_modifier
                    ) values %s
                    on conflict (item_id) do update set
                        damage=excluded.damage,
                        armor_damage=excluded.armor_damage,
                        penetration_power=excluded.penetration_power,
                        recoil_modifier=excluded.recoil_modifier,
                        accuracy_modifier=excluded.accuracy_modifier,
                        heavy_bleed_modifier=excluded.heavy_bleed_modifier,
                        light_bleed_modifier=excluded.light_bleed_modifier
                """


INSERT_MELEE_ITEMS = """
                    insert into melee_items (
                        item_id, hit_radius, slash_damage, stab_damage
                    ) values %s
                    on conflict (item_id) do update set
                        hit_radius=excluded.hit_radius,
                        slash_damage=excluded.slash_damage,
                        stab_damage=excluded.stab_damage
                """


INSERT_THROWABLE_ITEMS = """
                    insert into throwable_items (
                        item_id, throwable_type, fuse, fragments, contusion_radius, min_explosion_distance, max_explosion_distance
                    ) values %s
                    on conflict (item_id) do update set
                        throwable_type=excluded.throwable_type,
                        fuse=excluded.fuse,
                        fragments=excluded.fragments,
                        contusion_radius=excluded.contusion_radius,
                        min_explosion_distance=excluded.min_explosion_distance,
                        max_explosion_distance=excluded.max_explosion_distance
                """


INSERT_STORAGE_ITEMS = """
                    insert into storage_items (
                        item_id, storage_type, capacity
                    ) values %s
                    on conflict (item_id) do update set
                        storage_type=excluded.storage_type,
                        capacity=excluded.capacity
                """


INSERT_STORAGE_GRIDS = """
                    insert into storage_grids (
                        item_id, grid_index, width, height
                    ) values %s
                    on conflict (item_id, grid_index) do update set
                        width=excluded.width,
                        height=excluded.height
                """


INSERT_PROTECTION_ITEMS = """
                    insert into protection_items (
                        item_id, protection_type, armor_class, durability, material, ricochet_y, deafening, blindness_protection,
                        is_head_top, is_head_nape, is_head_ears, is_head_face, is_head_jaws, is_head_eyes, is_thorax_throat, is_thorax_neck, is_thorax, is_upper_back, is_stomach, is_left_side, is_right_side, is_lower_back, is_groin, is_buttocks, is_left_shoulder, is_right_shoulder, is_front_plate, is_back_plate, is_left_plate, is_right_plate, is_side_plate
                    ) values %s
                    on conflict (item_id) do update set
                        protection_type=excluded.protection_type,
                        armor_class=excluded.armor_class,
                        durability=excluded.durability,
                        material=excluded.material,
                        ricochet_y=excluded.ricochet_y,
                        deafening=excluded.deafening,
                        blindness_protection=excluded.blindness_protection,
                        is_head_top=excluded.is_head_top,
                        is_head_nape=excluded.is_head_nape,
                        is_head_ears=excluded.is_head_ears,
                        is_head_face=excluded.is_head_face,
                        is_head_jaws=excluded.is_head_jaws,
                        is_head_eyes=excluded.is_head_eyes,
                        is_thorax_throat=excluded.is_thorax_throat,
                        is_thorax_neck=excluded.is_thorax_neck,
                        is_thorax=excluded.is_thorax,
                        is_upper_back=excluded.is_upper_back,
                        is_stomach=excluded.is_stomach,
                        is_left_side=excluded.is_left_side,
                        is_right_side=excluded.is_right_side,
                        is_lower_back=excluded.is_lower_back,
                        is_groin=excluded.is_groin,
                        is_buttocks=excluded.is_buttocks,
                        is_left_shoulder=excluded.is_left_shoulder,
                        is_right_shoulder=excluded.is_right_shoulder,
                        is_front_plate=excluded.is_front_plate,
                        is_back_plate=excluded.is_back_plate,
                        is_left_plate=excluded.is_left_plate,
                        is_right_plate=excluded.is_right_plate,
                        is_side_plate=excluded.is_side_plate
                """


INSERT_CONSUMABLE_ITEMS = """
                    insert into consumable_items (
                        item_id, consumable_type, energy, hydration, units, use_time, hitpoints, painkiller_duration, energy_impact, hydration_impact
                    ) values %s
                    on conflict (item_id) do update set
                        consumable_type=excluded.consumable_type,
                        energy=excluded.energy,
                        hydration=excluded.hydration,
                        units=excluded.units,
                        use_time=excluded.use_time,
                        hitpoints=excluded.hitpoints,
                        painkiller_duration=excluded.painkiller_duration,
                        energy_impact=excluded.energy_impact,
                        hydration_impact=excluded.hydration_impact
                """


INSERT_CONSUMABLE_CURES = """
                    insert into consumable_cures (
                        item_id, cure
                    ) values %s
                    on conflict (item_id, cure) do nothing
                """


INSERT_CONSUMABLE_STIM_EFFECTS = """
                    insert into consumable_stim_effects (
                        item_id, effect_index, effect_type, value, delay, duration, skill_name
                    ) values %s
                    on conflict (item_id, effect_index) do update set
                        effect_type=excluded.effect_type,
                        value=excluded.value,
                        delay=excluded.delay,
                        duration=excluded.duration,
                        skill_name=excluded.skill_name
                """


INSERT_USAGE_ITEMS = """
                    insert into usage_items (
                        item_id, max_uses
                    ) values %s
                    on conflict (item_id) do update set
                        max_uses=excluded.max_uses
                """


SELECT_STATIC_ITEM_TARGETS = """
                select normalized_name
                from items
                where normalized_name is not null
                order by name_en, normalized_name;
                """


INITIAL_INSERT_ITEMS = """
                insert into items (
                    id, parent_category, category, name_en, name_ko, name_ja, normalized_name, weight, width, height, image
                ) values %s
                on conflict (id) do update set
                    parent_category=excluded.parent_category,
                    category=excluded.category,
                    name_en=excluded.name_en,
                    name_ko=excluded.name_ko,
                    name_ja=excluded.name_ja,
                    normalized_name=excluded.normalized_name,
                    weight=excluded.weight,
                    width=excluded.width,
                    height=excluded.height,
                    image=excluded.image,
                    update_time=now()
                """
