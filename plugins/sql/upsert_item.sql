INSERT INTO item_i18n (
    id,
    name,
    category,
    info,
    image,
    image_width,
    image_height,
    url_mapping,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    info = EXCLUDED.info,
    image = EXCLUDED.image,
    image_width = EXCLUDED.image_width,
    image_height = EXCLUDED.image_height,
    url_mapping = EXCLUDED.url_mapping,
    update_time = EXCLUDED.update_time;
