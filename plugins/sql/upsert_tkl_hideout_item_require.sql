INSERT INTO tkl_hideout_item_require (
    id,
    level_id,
    name_en,
    quantity,
    "count",
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    level_id = EXCLUDED.level_id,
    name_en = EXCLUDED.name_en,
    quantity = EXCLUDED.quantity,
    "count" = EXCLUDED.count,
    update_time = EXCLUDED.update_time;
