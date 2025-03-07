INSERT INTO tkl_container (
    id,
    name_en,
    short_name,
    image,
    grids,
    capacity,
    width,
    height,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    grids = EXCLUDED.grids,
    capacity = EXCLUDED.capacity,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    update_time = EXCLUDED.update_time;
