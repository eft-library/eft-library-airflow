INSERT INTO hideout_level_i18n (
    id,
    level,
    construction_time,
    update_time
) VALUES (
    %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    level = EXCLUDED.level,
    construction_time = EXCLUDED.construction_time,
    update_time = EXCLUDED.update_time;
