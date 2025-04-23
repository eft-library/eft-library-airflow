WITH ranked_items AS (
    SELECT
        id,
        base_url,
        CASE
            WHEN rn = 1 THEN base_url
            ELSE base_url || '-' || (rn - 1)
        END AS final_url
    FROM (
        SELECT
            id,
            trim(both '-' from regexp_replace(lower(name->>'en'), '[^a-z0-9]+', '-', 'g')) AS base_url,
            ROW_NUMBER() OVER (PARTITION BY
                trim(both '-' from regexp_replace(lower(name->>'en'), '[^a-z0-9]+', '-', 'g'))
                ORDER BY id
            ) AS rn
        FROM item_i18n
    ) AS sub
)
UPDATE item_i18n
SET url_mapping = ranked_items.final_url
FROM ranked_items
WHERE item_i18n.id = ranked_items.id;
