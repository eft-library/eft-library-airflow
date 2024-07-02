INSERT INTO tkl_hideout_trader_require (
    id,
    level_id,
    name_en,
    value,
    require_type,
    compare,
    image,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    level_id = EXCLUDED.level_id,
    name_en = EXCLUDED.name_en,
    value = EXCLUDED.value,
    require_type = EXCLUDED.require_type,
    compare = EXCLUDED.compare,
    image = EXCLUDED.image,
    update_time = EXCLUDED.update_time;
