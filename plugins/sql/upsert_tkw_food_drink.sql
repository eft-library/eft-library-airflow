INSERT INTO tkw_food_drink (
    id,
    name_en,
    name_kr,
    short_name,
    category,
    energy,
    hydration,
    stim_effects,
    image,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_kr = EXCLUDED.name_kr,
    short_name = EXCLUDED.short_name,
    category = EXCLUDED.category,
    energy = EXCLUDED.energy,
    hydration = EXCLUDED.hydration,
    stim_effects = EXCLUDED.stim_effects,
    image = EXCLUDED.image,
    update_time = EXCLUDED.update_time;
