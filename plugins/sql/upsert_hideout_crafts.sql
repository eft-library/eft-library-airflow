INSERT INTO hideout_crafts_i18n (
    id,
    level_id,
    level,
    width,
    height,
    name,
    duration,
    req_item,
    image,
    quantity,
    reward_item_id,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    level_id = EXCLUDED.level_id,
    level = EXCLUDED.level,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    name = EXCLUDED.name,
    duration = EXCLUDED.duration,
    req_item = EXCLUDED.req_item,
    image = EXCLUDED.image,
    quantity = EXCLUDED.quantity,
    reward_item_id = EXCLUDED.reward_item_id,
    update_time = EXCLUDED.update_time;
