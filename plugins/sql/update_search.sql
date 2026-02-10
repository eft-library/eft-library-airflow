INSERT INTO search_i18n (value, link, page_value, type, lang, "order", update_time)
SELECT value,
       link,
       page_value,
       type,
       lang,
       rn AS "order",
       NOW() AS update_time
FROM (
    SELECT value,
           link,
           page_value,
           type,
           lang,
           ROW_NUMBER() OVER (ORDER BY lang, type, value) AS rn, -- 전체 순번
           ROW_NUMBER() OVER (PARTITION BY value, page_value, lang ORDER BY type) AS dup_rn -- 중복 제거용
    FROM (
        SELECT '타르코프 지도: ' || (name ->> 'ko') AS value,
               '/map-of-tarkov/' || id              AS link,
               id                                   AS page_value,
               'MAP_OF_TARKOV'                      AS type,
               'ko'                                 AS lang
        FROM map_group_i18n
        UNION ALL
        SELECT '대화형 지도: ' || (name ->> 'ko'),
               '/map/' || id,
               id,
               'MAP',
               'ko'
        FROM map_group_i18n
        UNION ALL
        SELECT '보스: ' || (name ->> 'ko'),
               '/boss/' || url_mapping,
               url_mapping,
               'BOSS',
               'ko'
        FROM boss_i18n
        WHERE is_boss
        UNION ALL
        SELECT '퀘스트: ' || (name ->> 'ko'),
               '/quest/detail/' || url_mapping,
               url_mapping,
               'QUEST',
               'ko'
        FROM quest_i18n
        UNION ALL
        SELECT '상인: ' || (name ->> 'ko'),
               '/quest/' || id,
               id,
               'TRADER',
               'ko'
        FROM npc_i18n
        UNION ALL
        SELECT '아이템: ' || (name ->> 'ko'),
               '/item/info/' || item_i18n.url_mapping,
               item_i18n.url_mapping,
               'ITEM',
               'ko'
        FROM item_i18n

        UNION ALL
        SELECT 'Tarkov Maps: ' || (name ->> 'en'),
               '/map-of-tarkov/' || id,
               id,
               'MAP_OF_TARKOV',
               'en'
        FROM map_group_i18n
        UNION ALL
        SELECT 'Interactive Maps: ' || (name ->> 'en'),
               '/map/' || id,
               id,
               'MAP',
               'en'
        FROM map_group_i18n
        UNION ALL
        SELECT 'Boss: ' || (name ->> 'en'),
               '/boss/' || url_mapping,
               url_mapping,
               'BOSS',
               'en'
        FROM boss_i18n
        WHERE is_boss
        UNION ALL
        SELECT 'Quests: ' || (name ->> 'en'),
               '/quest/detail/' || url_mapping,
               url_mapping,
               'QUEST',
               'en'
        FROM quest_i18n
        UNION ALL
        SELECT 'Trader: ' || (name ->> 'en'),
               '/quest/' || id,
               id,
               'TRADER',
               'en'
        FROM npc_i18n
        UNION ALL
        SELECT 'Item: ' || (name ->> 'en'),
               '/item/' || item_i18n.url_mapping,
               item_i18n.url_mapping,
               'ITEM',
               'en'
        FROM item_i18n

        UNION ALL
        SELECT 'Tarkov マップ: ' || (name ->> 'ja'),
               '/map-of-tarkov/' || id,
               id,
               'MAP_OF_TARKOV',
               'ja'
        FROM map_group_i18n
        UNION ALL
        SELECT 'インタラクティブ マップ: ' || (name ->> 'ja'),
               '/map/' || id,
               id,
               'MAP',
               'ja'
        FROM map_group_i18n
        UNION ALL
        SELECT 'ボス: ' || (name ->> 'ja'),
               '/boss/' || url_mapping,
               url_mapping,
               'BOSS',
               'ja'
        FROM boss_i18n
        WHERE is_boss
        UNION ALL
        SELECT 'クエスト: ' || (name ->> 'ja'),
               '/quest/detail/' || url_mapping,
               url_mapping,
               'QUEST',
               'ja'
        FROM quest_i18n
        UNION ALL
        SELECT '商人: ' || (name ->> 'ja'),
               '/quest/' || id,
               id,
               'TRADER',
               'ja'
        FROM npc_i18n
        UNION ALL
        SELECT 'アイテム: ' || (name ->> 'ja'),
               '/item/' || item_i18n.url_mapping,
               item_i18n.url_mapping,
               'ITEM',
               'ja'
        FROM item_i18n
    ) AS base
) AS numbered
WHERE dup_rn = 1 -- 중복 제거
ORDER BY rn
ON CONFLICT (value, page_value, lang)
DO UPDATE SET
    link        = EXCLUDED.link,
    type        = EXCLUDED.type,
    "order"     = EXCLUDED."order",
    update_time = NOW();