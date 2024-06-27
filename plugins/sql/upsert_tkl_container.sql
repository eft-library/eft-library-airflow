INSERT INTO tkl_container (
    id,
    name,
    short_name,
    image,
    grids,
    capacity,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    grids = EXCLUDED.grids,
    capacity = EXCLUDED.capacity,
    update_time = EXCLUDED.update_time;
