UPDATE tkw_weapon_info
    SET
        weapon_id = %s,
        weapon_name = %s,
        weapon_short_name = %s,
        weapon_img = %s,
        weapon_category = %s,
        weapon_carliber = %s,
        weapon_default_ammo = %s,
        weapon_modes_en = %s,
        weapon_modes_kr = %s,
        weapon_fire_rate = %s,
        weapon_ergonomics = %s,
        weapon_recoil_vertical = %s,
        weapon_recoil_horizontal = %s,
        weapon_update_time = %s
    WHERE weapon_id = %s
;