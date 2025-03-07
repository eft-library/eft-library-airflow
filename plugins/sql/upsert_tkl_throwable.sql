INSERT INTO tkl_throwable (
    id,
    name,
    short_name,
    image,
    category,
    fuse,
    min_explosion_distance,
    max_explosion_distance,
    fragments,
    width,
    height,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    category = EXCLUDED.category,
    fuse = EXCLUDED.fuse,
    min_explosion_distance = EXCLUDED.min_explosion_distance,
    max_explosion_distance = EXCLUDED.max_explosion_distance,
    fragments = EXCLUDED.fragments,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    update_time = EXCLUDED.update_time;
