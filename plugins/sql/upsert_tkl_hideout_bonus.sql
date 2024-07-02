INSERT INTO tkl_hideout_bonus (
    level_id,
    type,
    name_en,
    value,
    skill_name_en,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT (level_id, "type") DO UPDATE SET
    name_en = EXCLUDED.name_en,
    value = EXCLUDED.value,
    skill_name_en = EXCLUDED.skill_name_en,
    update_time = EXCLUDED.update_time;
