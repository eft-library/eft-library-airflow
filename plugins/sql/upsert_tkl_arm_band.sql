INSERT INTO tkl_arm_band (
    id,
    name,
    short_name,
    weight,
    image,
    width,
    height,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    weight = EXCLUDED.weight,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    update_time = EXCLUDED.update_time;
