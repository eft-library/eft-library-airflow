INSERT INTO tkl_loot (
    id,
    name_en,
    name_kr,
    short_name,
    image,
    category,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_kr = EXCLUDED.name_kr,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    category = EXCLUDED.category,
    update_time = EXCLUDED.update_time;
