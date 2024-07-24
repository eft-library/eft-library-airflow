INSERT INTO tkl_arm_band (
    id,
    name,
    short_name,
    weight,
    image,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    image = EXCLUDED.image,
    weight = EXCLUDEC.weight
    update_time = EXCLUDED.update_time;
