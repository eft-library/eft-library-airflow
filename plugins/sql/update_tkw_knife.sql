UPDATE tkw_knife_info
    SET
        knife_id= %s,
        knife_name = %s,
        knife_short_name = %s,
        knife_image = %s,
        knife_category = %s,
        knife_slash_damage = %s,
        knife_stab_damage = %s,
        knife_hit_radius = %s,
        knife_update_time = %s
WHERE knife_id = %s;