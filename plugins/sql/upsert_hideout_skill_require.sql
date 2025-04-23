INSERT INTO hideout_skill_require_i18n (
    id,
    level_id,
    level,
    name,
    update_time
) VALUES (
    %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    level_id = EXCLUDED.level_id,
    level = EXCLUDED.level,
    name = EXCLUDED.name,
    update_time = EXCLUDED.update_time;
