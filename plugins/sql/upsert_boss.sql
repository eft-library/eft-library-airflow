INSERT INTO boss_i18n (
    id,
    name,
    image,
    item_info,
    update_time
) VALUES (
    %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    image = EXCLUDED.image,
    item_info = EXCLUDED.item_info,
    update_time = EXCLUDED.update_time;
