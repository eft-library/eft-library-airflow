INSERT INTO tkw_weapon_info (
    weapon_id,
    weapon_name,
    weapon_short_name,
    weapon_img,
    weapon_category,
    weapon_carliber,
    weapon_default_ammo,
    weapon_modes_en,
    weapon_modes_kr,
    weapon_fire_rate,
    weapon_ergonomics,
    weapon_recoil_vertical,
    weapon_recoil_horizontal,
    weapon_update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (weapon_id) DO UPDATE SET
    weapon_name = EXCLUDED.weapon_name,
    weapon_short_name = EXCLUDED.weapon_short_name,
    weapon_img = EXCLUDED.weapon_img,
    weapon_category = EXCLUDED.weapon_category,
    weapon_carliber = EXCLUDED.weapon_carliber,
    weapon_default_ammo = EXCLUDED.weapon_default_ammo,
    weapon_modes_en = EXCLUDED.weapon_modes_en,
    weapon_modes_kr = EXCLUDED.weapon_modes_kr,
    weapon_fire_rate = EXCLUDED.weapon_fire_rate,
    weapon_ergonomics = EXCLUDED.weapon_ergonomics,
    weapon_recoil_vertical = EXCLUDED.weapon_recoil_vertical,
    weapon_recoil_horizontal = EXCLUDED.weapon_recoil_horizontal,
    weapon_update_time = EXCLUDED.weapon_update_time;