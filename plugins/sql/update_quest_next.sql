UPDATE quest_i18n tq
SET task_next = a.result
FROM (SELECT jsonb_agg(result_json) AS result, task_id
      FROM (SELECT jsonb_build_object(
                           'task', jsonb_build_object(
                      'id', parent_id,
                      'name_en', name_en,
                      'name_ko', name_ko,
                      'name_ja', name_ja,
                      'normalizedName', normalizedName
                                   )
                   ) AS result_json,
                   task_id
            FROM (SELECT (jsonb_array_elements(task_requirements) -> 'task' ->> 'id') AS task_id,
                         id                                                           AS parent_id,
                         name ->> 'en'                                                as name_en,
                         name ->> 'ko'                                                as name_ko,
                         name ->> 'ja'                                                as name_ja,
                         url_mapping                                                  as normalizedName
                  FROM quest_i18n) AS d
            GROUP BY task_id, parent_id, name_en, name_ko, name_ja, normalizedName) AS e
      GROUP BY task_id) AS a
WHERE tq.id = a.task_id;
