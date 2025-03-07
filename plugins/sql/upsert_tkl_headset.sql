INSERT INTO tkl_headset (
    id,
    name,
    short_name,
    image,
    width,
    height,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    update_time = EXCLUDED.update_time;
