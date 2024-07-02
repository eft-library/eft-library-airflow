INSERT INTO tkl_hideout_item_require (
    id,
    level_id,
    name_en,
    quantity,
    "count",
    image,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    level_id = EXCLUDED.level_id,
    name_en = EXCLUDED.name_en,
    quantity = EXCLUDED.quantity,
    "count" = EXCLUDED.count,
    image = EXCLUDED.image,
    update_time = EXCLUDED.update_time;
