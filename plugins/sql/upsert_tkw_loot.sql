INSERT INTO tkw_loot (
    id,
    name,
    short_name,
    image,
    notes,
    category,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    notes = EXCLUDED.notes,
    category = EXCLUDED.category,
    update_time = EXCLUDED.update_time;
