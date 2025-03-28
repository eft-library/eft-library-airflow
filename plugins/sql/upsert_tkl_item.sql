INSERT INTO tkl_item (
    id,
    name_en,
    category,
    info,
    image,
    image_width,
    image_height,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    category = EXCLUDED.category,
    info = EXCLUDED.info,
    image = EXCLUDED.image,
    image_width = EXCLUDED.image_width,
    image_height = EXCLUDED.image_height,
    update_time = EXCLUDED.update_time;
