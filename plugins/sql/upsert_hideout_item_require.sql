INSERT INTO hideout_item_require_i18n (
    id,
    level_id,
    name,
    quantity,
    "count",
    image,
    item_id,
    found_in_raid,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    level_id = EXCLUDED.level_id,
    name = EXCLUDED.name,
    quantity = EXCLUDED.quantity,
    "count" = EXCLUDED.count,
    image = EXCLUDED.image,
    item_id = EXCLUDED.item_id,
    found_in_raid = EXCLUDED.found_in_raid,
    update_time = EXCLUDED.update_time;
