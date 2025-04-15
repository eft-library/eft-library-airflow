INSERT INTO tkl_search (value, link, page_value, type, "order")
SELECT
    a.value,
    a.link,
    a.page_value,
    a.type,
    a.seq_num
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
                  UNION ALL
                  SELECT '무기 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'WEAPON'
                  FROM tkl_item
                  WHERE category in ('Gun', 'Knife', 'Throwable')
                  UNION ALL
                  SELECT '탄약 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'AMMO'
                  FROM tkl_item
                  WHERE category = 'Ammo'
                  UNION ALL
                  SELECT '방탄모 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'HEADWEAR'
                  FROM tkl_item
                  WHERE category = 'Headwear'
                  UNION ALL
                  SELECT '전술 조끼 : ' || COALESCE(name_kr, name_en), '/item/'|| tkl_item.url_mapping, tkl_item.url_mapping, 'RIG'
                  FROM tkl_item
                  WHERE category = 'Rig'
                  UNION ALL
                  SELECT '방탄 조끼 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'ARMOR_VEST'
                  FROM tkl_item
                  WHERE category = 'ArmorVest'
                  UNION ALL
                  SELECT '헤드셋 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'HEADSET'
                  FROM tkl_item
                  WHERE category = 'Headset'
                  UNION ALL
                  SELECT '가방 : ' || COALESCE(name_kr, name_en), '/item/'|| tkl_item.url_mapping, tkl_item.url_mapping, 'BACKPACK'
                  FROM tkl_item
                  WHERE category = 'Backpack'
                  UNION ALL
                  SELECT '의료품 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'MEDICAL'
                  FROM tkl_item
                  WHERE category = 'Medical'
                  UNION ALL
                  SELECT '컨테이너 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'CONTAINER'
                  FROM tkl_item
                  WHERE category = 'Container'
                  UNION ALL
                  SELECT '열쇠 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'KEY'
                  FROM tkl_item
                  WHERE category = 'Key'
                  UNION ALL
                  SELECT '식량 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'PROVISIONS'
                  FROM tkl_item
                  WHERE category = 'Provisions'
                  UNION ALL
                  SELECT '전리품 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'LOOT'
                  FROM tkl_item
                  WHERE category = 'Loot'
                  UNION ALL
                  SELECT '얼굴 커버 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'FACE_COVER'
                  FROM tkl_item
                  WHERE category = 'FaceCover'
                  UNION ALL
                  SELECT '완장 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'ARM_BAND'
                  FROM tkl_item
                  WHERE category = 'Armband'
                  UNION ALL
                  SELECT '안경 : ' || COALESCE(name_kr, name_en), '/item/' || tkl_item.url_mapping, tkl_item.url_mapping, 'GLASSES'
                  FROM tkl_item
                  WHERE category = 'Glasses'
              ) AS subquery
     ) AS a
ON CONFLICT (value, page_value)
DO UPDATE SET
    link = EXCLUDED.link,
    type = EXCLUDED.type,
    "order" = EXCLUDED."order";