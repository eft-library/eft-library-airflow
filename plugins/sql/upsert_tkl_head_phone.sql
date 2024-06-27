INSERT INTO tkl_head_phone (
    id,
    name,
    short_name,
    image,
    update_time
) VALUES (
    %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    update_time = EXCLUDED.update_time;
