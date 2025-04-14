UPDATE tkl_api_quest
SET url_mapping = trim(both '-' from regexp_replace(lower(name_en), '[^a-z0-9]+', '-', 'g'))
WHERE name_en IS NOT NULL;