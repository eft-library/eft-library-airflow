INSERT INTO tkw_knife (
    id,
    name,
    short_name,
    image,
    category,
    slash_damage,
    stab_damage,
    hit_radius,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    category = EXCLUDED.category,
    slash_damage = EXCLUDED.slash_damage,
    stab_damage = EXCLUDED.stab_damage,
    hit_radius = EXCLUDED.hit_radius,
    update_time = EXCLUDED.update_time;
