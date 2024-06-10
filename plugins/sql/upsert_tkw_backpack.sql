INSERT INTO tkw_backpack (
    id,
    name,
    short_name,
    weight,
    image,
    grids,
    capacity,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    weight = EXCLUDED.weight,
    image = EXCLUDED.image,
    grids = EXCLUDED.grids,
    capacity = EXCLUDED.capacity,
    update_time = EXCLUDED.update_time;
