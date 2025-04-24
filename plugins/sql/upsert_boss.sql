INSERT INTO boss_i18n (
    id,
    name,
    image,
    item_info,
    url_mapping,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    image = EXCLUDED.image,
    item_info = EXCLUDED.item_info,
    url_mapping = EXCLUDED.url_mapping,
    update_time = EXCLUDED.update_time;
