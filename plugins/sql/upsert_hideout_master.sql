INSERT INTO hideout_master_i18n (
    id,
    name,
    level_ids,
    update_time
) VALUES (
    %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    level_ids = EXCLUDED.level_ids,
    update_time = EXCLUDED.update_time;
