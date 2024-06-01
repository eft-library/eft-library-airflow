INSERT INTO tkw_throwable_info (
    throwable_id,
    throwable_name,
    throwable_short_name,
    throwable_image,
    throwable_category,
    throwable_fuse,
    throwable_min_explosion_distance,
    throwable_max_explosion_distance,
    throwable_fragments,
    throwable_update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (throwable_id) DO UPDATE SET
    throwable_name = EXCLUDED.throwable_name,
    throwable_short_name = EXCLUDED.throwable_short_name,
    throwable_image = EXCLUDED.throwable_image,
    throwable_category = EXCLUDED.throwable_category,
    throwable_fuse = EXCLUDED.throwable_fuse,
    throwable_min_explosion_distance = EXCLUDED.throwable_min_explosion_distance,
    throwable_max_explosion_distance = EXCLUDED.throwable_max_explosion_distance,
    throwable_fragments = EXCLUDED.throwable_fragments,
    throwable_update_time = EXCLUDED.throwable_update_time;
