INSERT INTO hideout_bonus_i18n (
    level_id,
    type,
    name,
    value,
    skill_name,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT (level_id, "type") DO UPDATE SET
    name = EXCLUDED.name,
    value = EXCLUDED.value,
    skill_name = EXCLUDED.skill_name,
    update_time = EXCLUDED.update_time;
