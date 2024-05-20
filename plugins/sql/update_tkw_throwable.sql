UPDATE tkw_throwable_info
    SET
        throwable_id = %s,
        throwable_name = %s,
        throwable_short_name = %s,
        throwable_image = %s,
        throwable_category = %s,
        throwable_fuse = %s,
        throwable_min_explosion_distance = %s,
        throwable_max_explosion_distance = %s,
        throwable_fragments = %s,
        throwable_update_time = %s
WHERE throwable_id = %s;