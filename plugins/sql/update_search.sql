INSERT INTO search_i18n (value, link, page_value, type, lang, "order")
SELECT value, link, page_value, type, lang, rn AS "order"
FROM (
    SELECT *,
           row_number() OVER (PARTITION BY value, page_value, lang ORDER BY type) AS rn
    FROM (
        SELECT (name ->> 'ko')         AS value,
               '/map-of-tarkov/' || id AS link,
               id                      AS page_value,
               'MAP_OF_TARKOV'         AS type,
               'ko'                    AS lang
        FROM map_group_i18n
        UNION ALL
        SELECT (name ->> 'ko'),
               '/map/' || id,
               id,
               'MAP',
               'ko'
        FROM map_group_i18n
        UNION ALL
        SELECT (name ->> 'ko'),
               '/boss/' || url_mapping,
               url_mapping,
               'BOSS',
               'ko'
        FROM boss_i18n
        WHERE is_boss
        UNION ALL
        SELECT (name ->> 'ko'),
               '/quest/detail/' || url_mapping,
               url_mapping,
               'QUEST',
               'ko'
        FROM quest_i18n
        UNION ALL
        SELECT (name ->> 'ko'),
               '/quest',
               id,
               'TRADER',
               'ko'
        FROM npc_i18n
        UNION ALL
        SELECT (name ->> 'ko'),
               '/item/' || item_i18n.url_mapping,
               item_i18n.url_mapping,
               'ITEM',
               'ko'
        FROM item_i18n

        UNION ALL
        SELECT (name ->> 'en'),
               '/map-of-tarkov/' || id,
               id,
               'MAP_OF_TARKOV',
               'en'
        FROM map_group_i18n
        UNION ALL
        SELECT (name ->> 'en'),
               '/map/' || id,
               id,
               'MAP',
               'en'
        FROM map_group_i18n
        UNION ALL
        SELECT (name ->> 'en'),
               '/boss/' || url_mapping,
               url_mapping,
               'BOSS',
               'en'
        FROM boss_i18n
        WHERE is_boss
        UNION ALL
        SELECT (name ->> 'en'),
               '/quest/detail/' || url_mapping,
               url_mapping,
               'QUEST',
               'en'
        FROM quest_i18n
        UNION ALL
        SELECT (name ->> 'en'),
               '/quest',
               id,
               'TRADER',
               'en'
        FROM npc_i18n
        UNION ALL
        SELECT (name ->> 'en'),
               '/item/' || item_i18n.url_mapping,
               item_i18n.url_mapping,
               'ITEM',
               'en'
        FROM item_i18n

        UNION ALL
        SELECT (name ->> 'ja'),
               '/map-of-tarkov/' || id,
               id,
               'MAP_OF_TARKOV',
               'ja'
        FROM map_group_i18n
        UNION ALL
        SELECT (name ->> 'ja'),
               '/map/' || id,
               id,
               'MAP',
               'ja'
        FROM map_group_i18n
        UNION ALL
        SELECT (name ->> 'ja'),
               '/boss/' || url_mapping,
               url_mapping,
               'BOSS',
               'ja'
        FROM boss_i18n
        WHERE is_boss
        UNION ALL
        SELECT (name ->> 'ja'),
               '/quest/detail/' || url_mapping,
               url_mapping,
               'QUEST',
               'ja'
        FROM quest_i18n
        UNION ALL
        SELECT (name ->> 'ja'),
               '/quest',
               id,
               'TRADER',
               'ja'
        FROM npc_i18n
        UNION ALL
        SELECT (name ->> 'ja'),
               '/item/' || item_i18n.url_mapping,
               item_i18n.url_mapping,
               'ITEM',
               'ja'
        FROM item_i18n
    ) AS base
) AS deduplicated
WHERE rn = 1
ON CONFLICT (value, page_value, lang)
    DO UPDATE SET link    = EXCLUDED.link,
                  type    = EXCLUDED.type,
                  "order" = EXCLUDED."order";
