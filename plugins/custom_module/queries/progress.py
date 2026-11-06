"""SQL for type-scoped progress checklists; user selections are separate."""
PRIMARY_KEY_COLUMNS = """
SELECT array_agg(a.attname::text ORDER BY keys.ordinality)
FROM pg_index i
CROSS JOIN LATERAL unnest(i.indkey) WITH ORDINALITY AS keys(attnum, ordinality)
JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=keys.attnum
WHERE i.indrelid='progress_item'::regclass AND i.indisprimary
"""

UPSERT_ITEMS = """
INSERT INTO progress_item (id, progress_type) VALUES %s
ON CONFLICT (id, progress_type) DO UPDATE SET update_time=now()
"""

DELETE_OBSOLETE_ITEMS = """
DELETE FROM progress_item WHERE progress_type=%s AND NOT (id = ANY(%s))
"""
