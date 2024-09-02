INSERT INTO tkl_loot (
    id,
    name_en,
    image,
    category,
    update_time
) VALUES (
    %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    image = EXCLUDED.image,
    category = EXCLUDED.category,
    update_time = EXCLUDED.update_time;
