INSERT INTO hideout_trader_require_i18n (
    id,
    level_id,
    name,
    value,
    image,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    level_id = EXCLUDED.level_id,
    name = EXCLUDED.name,
    value = EXCLUDED.value,
    image = EXCLUDED.image,
    update_time = EXCLUDED.update_time;
