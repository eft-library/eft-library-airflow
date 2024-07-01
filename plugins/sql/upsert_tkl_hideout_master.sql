INSERT INTO tkl_hideout_master (
    id,
    name_en,
    name_kr,
    image,
    construction_time,
    level_ids,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_kr = EXCLUDED.name_kr,
    construction_time = EXCLUDED.construction_time,
    image = EXCLUDED.image,
    level_ids = EXCLUDED.level_ids,
    update_time = EXCLUDED.update_time;
