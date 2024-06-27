INSERT INTO tkl_head_wear (
    id,
    name,
    short_name,
    class_value,
    areas_en,
    areas_kr,
    durability,
    ricochet_chance,
    weight,
    image,
    ricochet_str_en,
    ricochet_str_kr,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    class_value = EXCLUDED.class_value,
    areas_en = EXCLUDED.areas_en,
    areas_kr = EXCLUDED.areas_kr,
    durability = EXCLUDED.durability,
    ricochet_chance = EXCLUDED.ricochet_chance,
    weight = EXCLUDED.weight,
    image = EXCLUDED.image,
    ricochet_str_en = EXCLUDED.ricochet_str_en,
    ricochet_str_kr = EXCLUDED.ricochet_str_kr,
    update_time = EXCLUDED.update_time;
