INSERT INTO tkw_medical (
    id,
    name_en,
    name_kr,
    short_name,
    cures_en,
    cures_kr,
    category,
    buff,
    debuff,
    use_time,
    uses,
    energy_impact,
    hydration_impact,
    painkiller_duration,
    image,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_kr = EXCLUDED.name_kr,
    short_name = EXCLUDED.short_name,
    cures_en = EXCLUDED.cures_en,
    cures_kr = EXCLUDED.cures_kr,
    category = EXCLUDED.category,
    buff = EXCLUDED.buff,
    debuff = EXCLUDED.debuff,
    use_time = EXCLUDED.use_time,
    uses = EXCLUDED.uses,
    energy_impact = EXCLUDED.energy_impact,
    hydration_impact = EXCLUDED.hydration_impact,
    painkiller_duration = EXCLUDED.painkiller_duration,
    image = EXCLUDED.image,
    update_time = EXCLUDED.update_time;
