INSERT INTO tkw_knife_info (
    knife_id,
    knife_name,
    knife_short_name,
    knife_image,
    knife_category,
    knife_slash_damage,
    knife_stab_damage,
    knife_hit_radius,
    knife_update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (knife_id) DO UPDATE SET
    knife_name = EXCLUDED.knife_name,
    knife_short_name = EXCLUDED.knife_short_name,
    knife_image = EXCLUDED.knife_image,
    knife_category = EXCLUDED.knife_category,
    knife_slash_damage = EXCLUDED.knife_slash_damage,
    knife_stab_damage = EXCLUDED.knife_stab_damage,
    knife_hit_radius = EXCLUDED.knife_hit_radius,
    knife_update_time = EXCLUDED.knife_update_time;
