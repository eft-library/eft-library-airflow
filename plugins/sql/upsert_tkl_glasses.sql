INSERT INTO tkl_glasses (
    id,
    name,
    short_name,
    class_value,
    durability,
    blindness_protection,
    image,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    class_value = EXCLUDED.class_value,
    durability = EXCLUDED.durability,
    blindness_protection = EXCLUDED.blindness_protection,
    image = EXCLUDED.image,
    update_time = EXCLUDED.update_time;
