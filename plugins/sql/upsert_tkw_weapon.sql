INSERT INTO tkw_weapon_info (
    id,
    name,
    short_name,
    image,
    category,
    carliber,
    default_ammo,
    modes_en,
    modes_kr,
    fire_rate,
    ergonomics,
    recoil_vertical,
    recoil_horizontal,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    category = EXCLUDED.category,
    carliber = EXCLUDED.carliber,
    default_ammo = EXCLUDED.default_ammo,
    modes_en = EXCLUDED.modes_en,
    modes_kr = EXCLUDED.modes_kr,
    fire_rate = EXCLUDED.fire_rate,
    ergonomics = EXCLUDED.ergonomics,
    recoil_vertical = EXCLUDED.recoil_vertical,
    recoil_horizontal = EXCLUDED.recoil_horizontal,
    update_time = EXCLUDED.update_time;