INSERT INTO roadmap_node (id)
SELECT id
FROM quest_i18n
ON CONFLICT (id) DO NOTHING;
