INSERT INTO tkl_hideout_crafts (
    id,
    level_id,
    level,
    width,
    height,
    name_en,
    duration,
    req_item,
    image,
    quantity,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    level_id = EXCLUDED.level_id,
    level = EXCLUDED.level,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    name_en = EXCLUDED.name_en,
    duration = EXCLUDED.duration,
    req_item = EXCLUDED.req_item,
    image = EXCLUDED.image,
    quantity = EXCLUDED.quantity,
    update_time = EXCLUDED.update_time;
