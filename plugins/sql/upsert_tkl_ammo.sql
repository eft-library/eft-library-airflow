INSERT INTO tkl_ammo (
    id,
    name,
    short_name,
--     category,
--     round,
    damage,
    penetration_power,
    armor_damage,
    accuracy_modifier,
    recoil_modifier,
    light_bleed_modifier,
    heavy_bleed_modifier,
--     efficiency,
    image,
    width,
    height,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
--     category = EXCLUDED.category,
--     round = EXCLUDED.round,
    damage = EXCLUDED.damage,
    penetration_power = EXCLUDED.penetration_power,
    armor_damage = EXCLUDED.armor_damage,
    accuracy_modifier = EXCLUDED.accuracy_modifier,
    recoil_modifier = EXCLUDED.recoil_modifier,
    light_bleed_modifier = EXCLUDED.light_bleed_modifier,
    heavy_bleed_modifier = EXCLUDED.heavy_bleed_modifier,
--     efficiency = EXCLUDED.efficiency,
    image = EXCLUDED.image,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    update_time = EXCLUDED.update_time;
