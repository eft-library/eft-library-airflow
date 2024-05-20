INSERT INTO tkw_weapon_info (
    weapon_id, weapon_name, weapon_short_name, weapon_img,
    weapon_category, weapon_carliber, weapon_default_ammo,
    weapon_modes_en, weapon_modes_kr, weapon_fire_rate,
    weapon_ergonomics, weapon_recoil_vertical, weapon_recoil_horizontal, weapon_update_time
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);