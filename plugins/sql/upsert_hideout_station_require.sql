INSERT INTO hideout_station_require_i18n (
    id,
    level_id,
    level,
    name,
    station_master_id,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    level_id = EXCLUDED.level_id,
    level = EXCLUDED.level,
    name = EXCLUDED.name,
    station_master_id = EXCLUDED.station_master_id,
    update_time = EXCLUDED.update_time;
