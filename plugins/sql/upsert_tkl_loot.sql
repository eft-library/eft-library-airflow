INSERT INTO tkl_loot (
    id,
    name,
    short_name,
    image,
    category,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    category = EXCLUDED.category,
    update_time = EXCLUDED.update_time;
