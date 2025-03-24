INSERT INTO tkl_hideout_station_require (
    id,
    level_id,
    level,
    name_en,
    update_time
) VALUES (
    %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    level_id = EXCLUDED.level_id,
    level = EXCLUDED.level,
    name_en = EXCLUDED.name_en,
    update_time = EXCLUDED.update_time;
