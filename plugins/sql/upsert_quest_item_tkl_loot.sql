INSERT INTO tkl_loot (
    id,
    name_en,
    image,
    category,
    width,
    height,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    image = EXCLUDED.image,
    category = EXCLUDED.category,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    update_time = EXCLUDED.update_time;
