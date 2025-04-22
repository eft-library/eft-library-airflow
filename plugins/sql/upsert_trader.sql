INSERT INTO npc_i18n (id, name, image, barter_info, update_time)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    image = EXCLUDED.image,
    barter_info = EXCLUDED.barter_info,
    update_time = EXCLUDED.update_time;