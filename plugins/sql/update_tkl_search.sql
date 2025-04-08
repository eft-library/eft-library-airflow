UPDATE tkl_search
SET
    value = a.value,
    link = a.link,
    page_value = a.page_value,
    type = a.type,
    "order" = a.seq_num
FROM (
         SELECT
             *,
             row_number() OVER () AS seq_num
         FROM (
                  SELECT '타르코프 지도 : ' || name_kr AS value, '/map-of-tarkov/' || id AS link, id AS page_value, 'MAP_OF_TARKOV' AS type
                  FROM tkl_map_parent
                  UNION ALL
                  SELECT '대화형 지도 : ' || name_kr, '/map/' || id, id, 'MAP'
                  FROM tkl_map_parent
                  UNION ALL
                  SELECT '보스 : ' || tkl_boss.name_kr, '/boss/' || id, id, 'BOSS'
                  FROM tkl_boss
                  UNION ALL
                  SELECT '퀘스트 : ' || name_kr, '/quest/detail/' || url_mapping, url_mapping, 'QUEST'
                  FROM tkl_quest
                  UNION ALL
                  SELECT '퀘스트 : ' || name_en, '/quest/detail/' || url_mapping, url_mapping, 'QUEST'
                  FROM tkl_quest
                  UNION ALL
                  SELECT '상인 : ' || tkl_npc.name_kr, '/quest', id, 'TRADER'
                  FROM tkl_npc
--                   UNION ALL
--                   SELECT '무기 : ' || name, '/weapon?id=' || id, id, 'WEAPON'
--                   FROM tkl_weapon
--                   UNION ALL
--                   SELECT '무기 : ' || name, '/weapon?id=' || id, id, 'WEAPON'
--                   FROM tkl_throwable
--                   UNION ALL
--                   SELECT '무기 : ' || name, '/weapon?id=' || id, id, 'WEAPON'
--                   FROM tkl_knife
--                   UNION ALL
--                   SELECT '탄약 : ' || name, '/ammo?id=' || id, id, 'AMMO'
--                   FROM tkl_ammo
--                   UNION ALL
--                   SELECT '방탄모 : ' || name, '/head-wear?id=' || id, id, 'HEADWEAR'
--                   FROM tkl_headwear
--                   UNION ALL
--                   SELECT '전술 조끼 : ' || name, '/rig?id=' || id, id, 'RIG'
--                   FROM tkl_rig
--                   UNION ALL
--                   SELECT '방탄 조끼 : ' || name, '/armor-vest?id=' || id, id, 'ARMOR_VEST'
--                   FROM tkl_armor_vest
--                   UNION ALL
--                   SELECT '헤드셋 : ' || name, '/headset?id=' || id, id, 'HEADSET'
--                   FROM tkl_headset
--                   UNION ALL
--                   SELECT '가방 : ' || name, '/backpack?id=' || id, id, 'BACKPACK'
--                   FROM tkl_backpack
--                   UNION ALL
--                   SELECT '의료품 : ' || COALESCE(name_kr, name_en), '/medical?id=' || id, id, 'MEDICAL'
--                   FROM tkl_medical
--                   UNION ALL
--                   SELECT '컨테이너 : ' || COALESCE(name_kr, name_en), '/container?id=' || id, id, 'CONTAINER'
--                   FROM tkl_container
--                   UNION ALL
--                   SELECT '열쇠 : ' || name, '/key?id=' || id, id, 'KEY'
--                   FROM tkl_key
--                   UNION ALL
--                   SELECT '식량 : ' || COALESCE(name_kr, name_en), '/provisions?id=' || id, id, 'PROVISIONS'
--                   FROM tkl_provisions
--                   UNION ALL
--                   SELECT '전리품 : ' || COALESCE(name_kr, name_en), '/loot?id=' || id, id, 'LOOT'
--                   FROM tkl_loot
--                   UNION ALL
--                   SELECT '얼굴 커버 : ' || name, '/face-cover?id=' || id, id, 'FACE_COVER'
--                   FROM tkl_face_cover
--                   UNION ALL
--                   SELECT '완장 : ' || name, '/arm-band?id=' || id, id, 'ARM_BAND'
--                   FROM tkl_arm_band
--                   UNION ALL
--                   SELECT '안경 : ' || name, '/glasses?id=' || id, id, 'GLASSES'
--                   FROM tkl_glasses
              ) AS subquery
     ) AS a
WHERE tkl_search.value = a.value
  AND tkl_search.page_value = a.page_value