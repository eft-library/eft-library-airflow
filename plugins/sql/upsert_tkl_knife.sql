INSERT INTO tkl_knife (
    id,
    name,
    short_name,
    image,
    category,
    slash_damage,
    stab_damage,
    hit_radius,
    width,
    height,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    category = EXCLUDED.category,
    slash_damage = EXCLUDED.slash_damage,
    stab_damage = EXCLUDED.stab_damage,
    hit_radius = EXCLUDED.hit_radius,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    update_time = EXCLUDED.update_time;
