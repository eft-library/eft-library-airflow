INSERT INTO tkl_npc (id, name_en, image, barter_info, update_time)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    image = EXCLUDED.image,
    barter_info = EXCLUDED.barter_info,
    update_time = EXCLUDED.update_time;