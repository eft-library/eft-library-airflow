INSERT INTO search_i18n (value, link, page_value, type, lang, "order")
SELECT a.value,
       a.link,
       a.page_value,
       a.type,
       a.lang,
       a.seq_num
FROM (SELECT *,
             row_number() OVER () AS seq_num
      FROM (SELECT (name ->> 'ko')         AS value,
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
                   'ko' AS lang
            FROM map_group_i18n
            UNION ALL
            SELECT (name ->> 'ko'),
                   '/boss/' || url_mapping,
                   url_mapping,
                   'BOSS',
                   'ko' AS lang
            FROM boss_i18n
            WHERE is_boss
            UNION ALL
            SELECT (name ->> 'ko'),
                   '/quest/detail/' || url_mapping,
                   url_mapping,
                   'QUEST',
                   'ko' AS lang
            FROM quest_i18n
            UNION ALL
            SELECT (name ->> 'ko'),
                   '/quest',
                   id,
                   'TRADER',
                   'ko' AS lang
            FROM npc_i18n
            UNION ALL
            SELECT (name ->> 'ko'),
                   '/item/' || item_i18n.url_mapping,
                   item_i18n.url_mapping,
                   'ITEM',
                   'ko' AS lang
            FROM item_i18n
            UNION ALL
            SELECT (name ->> 'en')         AS value,
                   '/map-of-tarkov/' || id AS link,
                   id                      AS page_value,
                   'MAP_OF_TARKOV'         AS type,
                   'en'                    AS lang
            FROM map_group_i18n
            UNION ALL
            SELECT (name ->> 'en'),
                   '/map/' || id,
                   id,
                   'MAP',
                   'en' AS lang
            FROM map_group_i18n
            UNION ALL
            SELECT (name ->> 'en'),
                   '/boss/' || url_mapping,
                   url_mapping,
                   'BOSS',
                   'en' AS lang
            FROM boss_i18n
            WHERE is_boss
            UNION ALL
            SELECT (name ->> 'en'),
                   '/quest/detail/' || url_mapping,
                   url_mapping,
                   'QUEST',
                   'en' AS lang
            FROM quest_i18n
            UNION ALL
            SELECT (name ->> 'en'),
                   '/quest',
                   id,
                   'TRADER',
                   'en' AS lang
            FROM npc_i18n
            UNION ALL
            SELECT (name ->> 'en'),
                   '/item/' || item_i18n.url_mapping,
                   item_i18n.url_mapping,
                   'ITEM',
                   'en' AS lang
            FROM item_i18n
            UNION ALL
            SELECT (name ->> 'ja')         AS value,
                   '/map-of-tarkov/' || id AS link,
                   id                      AS page_value,
                   'MAP_OF_TARKOV'         AS type,
                   'ja'                    AS lang
            FROM map_group_i18n
            UNION ALL
            SELECT (name ->> 'ja'),
                   '/map/' || id,
                   id,
                   'MAP',
                   'ja' AS lang
            FROM map_group_i18n
            UNION ALL
            SELECT (name ->> 'ja'),
                   '/boss/' || url_mapping,
                   url_mapping,
                   'BOSS',
                   'ja' AS lang
            FROM boss_i18n
            WHERE is_boss
            UNION ALL
            SELECT (name ->> 'ja'),
                   '/quest/detail/' || url_mapping,
                   url_mapping,
                   'QUEST',
                   'ja' AS lang
            FROM quest_i18n
            UNION ALL
            SELECT (name ->> 'ja'),
                   '/quest',
                   id,
                   'TRADER',
                   'ja' AS lang
            FROM npc_i18n
            UNION ALL
            SELECT (name ->> 'ja'),
                   '/item/' || item_i18n.url_mapping,
                   item_i18n.url_mapping,
                   'ITEM',
                   'ja' AS lang
            FROM item_i18n) AS subquery) AS a
ON CONFLICT (value, page_value, lang)
    DO UPDATE SET link    = EXCLUDED.link,
                  type    = EXCLUDED.type,
                  "order" = EXCLUDED."order";