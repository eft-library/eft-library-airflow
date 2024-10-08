INSERT INTO tkl_rig (
    id,
    name,
    short_name,
    weight,
    image,
    class_value,
    areas_en,
    areas_kr,
--     durability,
    capacity,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    weight = EXCLUDED.weight,
    image = EXCLUDED.image,
    class_value = EXCLUDED.class_value,
    areas_en = EXCLUDED.areas_en,
    areas_kr = EXCLUDED.areas_kr,
--     durability = EXCLUDED.durability,
    capacity = EXCLUDED.capacity,
    update_time = EXCLUDED.update_time;
