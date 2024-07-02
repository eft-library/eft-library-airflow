INSERT INTO tkl_hideout_master (
    id,
    name_en,
    image,
    construction_time,
    level_ids,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    image = EXCLUDED.image,
    construction_time = EXCLUDED.construction_time,
    level_ids = EXCLUDED.level_ids,
    update_time = EXCLUDED.update_time;
