INSERT INTO tkl_loot (
    id,
    name_en,
    name_kr,
    short_name,
    image,
    category_en,
    category_kr,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_kr = EXCLUDED.name_kr,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    category_en = EXCLUDED.category_en,
    category_kr = EXCLUDED.category_kr,
    update_time = EXCLUDED.update_time;
