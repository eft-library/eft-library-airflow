INSERT INTO tkl_key (
    id,
    name,
    short_name,
    image,
    uses,
    use_map_en,
    use_map_kr,
    map_value,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    uses = EXCLUDED.uses,
    use_map_en = EXCLUDED.use_map_en,
    use_map_kr = EXCLUDED.use_map_kr,
    map_value = EXCLUDED.map_value,
    update_time = EXCLUDED.update_time;
