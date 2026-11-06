-- Generated from plugins/custom_module/kord_breach_mapping.json.
-- Back up all four KORD BREACH tables before executing. Metadata sync is a separate DAG.
-- Run with psql -v ON_ERROR_STOP=1 -f this_file.sql against platform_db.
BEGIN;
SET LOCAL lock_timeout = '10s';
SET LOCAL statement_timeout = '60s';
LOCK TABLE kord_breach_modifier, kord_breach_modifier_conflict,
 user_kord_breach_preset, user_kord_breach_preset_modifier IN SHARE ROW EXCLUSIVE MODE;
CREATE TEMP TABLE kord_id_mapping (
 legacy_id text PRIMARY KEY, source_id text UNIQUE NOT NULL, name_en text NOT NULL
) ON COMMIT DROP;
INSERT INTO kord_id_mapping VALUES
('no-insurance', '69c41a19cd28c936320a7523', 'No Insurance'),
('handyman', '69c41a86383fc5c9ad03f3d5', 'Handyman'),
('seasoned-pmcs', '69c41adf883efd5e3b09ccae', 'Seasoned PMCs'),
('armor-shortage', '69ce5d9296f3b267fa08f137', 'Armor Shortage'),
('black-division', '69ce5e104e0a1c7ca20781c9', 'Black Division'),
('no-fir-for-hideout', '69ce5eb3e4b79de94a0d78c8', 'No FIR for Hideout'),
('hemophilia', '69c3cd003ffdba4e68086bd7', 'Hemophilia'),
('osteoporosis', '69c3cddcfb79911cf20022d6', 'Osteoporosis'),
('well-that-hurt', '69c3d036042c81ad9209eeae', 'Well That Hurt!'),
('incompetent', '69c3d21749d7d7c520026425', 'Incompetent'),
('polydipsia', '69c3d2acfe3c5632e4045fe8', 'Polydipsia'),
('chronic-fatigue-syndrome', '69c3d35feaf97663fb0bb367', 'Chronic Fatigue Syndrome'),
('personality-vacuum', '69c3d43030f896ebef0ed357', 'Personality Vacuum'),
('dr-jekyll', '69c3d4e949d7d7c52002642a', 'Dr. Jekyll'),
('allergic', '69c3d6a9af28f094100fe128', 'Allergic'),
('no-flea-market', '69c3da8fc0e4deb02605f3c9', 'No Flea Market'),
('marathon-runner', '69c3e8d8af28f094100fe130', 'Marathon Runner'),
('bushborne', '69c405a9d7a7b2ca660e0c56', 'Bushborne'),
('juice-time', '69c406731d8aec4a2b0551bd', 'Juice Time'),
('street-tax', '69c40cb782362c4aff041510', 'Street Tax'),
('the-tarkov-shooter', '69c40e131f8903ce7a06984c', 'The Tarkov Shooter'),
('diet', '69c40f9f9b5263783d0fe51d', 'Diet'),
('thrombophilia', '69c4116a383fc5c9ad03f3d1', 'Thrombophilia'),
('hypodipsia', '69c411d8883efd5e3b09ccab', 'Hypodipsia'),
('polyphagia', '69c412519b5263783d0fe520', 'Polyphagia'),
('sturdy-bones', '69c41632d7a7b2ca660e0c59', 'Sturdy Bones'),
('third-leg', '69ce62886e199f4bbe0ab19b', 'Third Leg'),
('kappa-protocol', '69ce64fe6e199f4bbe0ab1a1', 'Kappa Protocol'),
('prodigy', '6a578102e7737aa469066518', 'PRODIGY'),
('lucky', '6a5789f713792e2c7c0d2a5b', 'LUCKY'),
('unlucky', '6a578ac032cea863f505beed', 'UNLUCKY'),
('exhaustion', '69c3ce913ffdba4e68086bdb', 'Exhaustion'),
('safecracker', '69c405332f253132020be099', 'Safecracker'),
('sailors-nostalgia', '69c40ae21d8aec4a2b0551c2', 'Sailor''s Nostalgia'),
('youth', '69c40c0f5e9ce5a8970f6be9', 'Youth'),
('hercules', '69c410831f8903ce7a06984f', 'Hercules'),
('sprinter', '69c41111cd28c936320a7520', 'Sprinter'),
('average', '69ce64064e0a1c7ca20781d3', 'Average'),
('underdog', '6a578b8c5372fb646802e5fa', 'Underdog'),
('broken-secure-container', '69c3da13eaf97663fb0bb36d', 'Broken Secure Container');
DO $$
BEGIN
 IF EXISTS (
  SELECT 1 FROM kord_breach_modifier m
  WHERE NOT EXISTS (SELECT 1 FROM kord_id_mapping x WHERE m.id IN (x.legacy_id, x.source_id))
 ) THEN RAISE EXCEPTION 'Unknown modifier IDs: review mapping before migration'; END IF;
 IF EXISTS (
  SELECT 1 FROM kord_id_mapping x
  LEFT JOIN kord_breach_modifier m ON m.id IN (x.legacy_id, x.source_id)
  GROUP BY x.legacy_id HAVING count(m.id) <> 1
 ) THEN RAISE EXCEPTION 'Missing modifier or legacy/canonical collision'; END IF;
 IF EXISTS (
  SELECT 1 FROM kord_breach_modifier m JOIN kord_id_mapping x ON m.id=x.legacy_id
  WHERE lower(trim(m.name_en)) <> lower(trim(x.name_en))
 ) THEN RAISE EXCEPTION 'Legacy ID/name mismatch'; END IF;
 IF EXISTS (
  SELECT 1 FROM user_kord_breach_preset_modifier p
  WHERE NOT EXISTS (SELECT 1 FROM kord_breach_modifier m WHERE m.id=p.modifier_id)
 ) OR EXISTS (
  SELECT 1 FROM kord_breach_modifier_conflict c
  WHERE NOT EXISTS (SELECT 1 FROM kord_breach_modifier m WHERE m.id=c.modifier_id)
     OR NOT EXISTS (SELECT 1 FROM kord_breach_modifier m WHERE m.id=c.conflict_modifier_id)
 ) THEN RAISE EXCEPTION 'Orphan modifier reference: review before migration'; END IF;
END $$;
UPDATE kord_breach_modifier m SET id=x.source_id, update_time=now()
FROM kord_id_mapping x WHERE m.id=x.legacy_id;
UPDATE user_kord_breach_preset_modifier p SET modifier_id=x.source_id
FROM kord_id_mapping x WHERE p.modifier_id=x.legacy_id;
UPDATE kord_breach_modifier_conflict c
SET modifier_id=coalesce((SELECT x.source_id FROM kord_id_mapping x WHERE x.legacy_id=c.modifier_id), c.modifier_id),
 conflict_modifier_id=coalesce((SELECT x.source_id FROM kord_id_mapping x WHERE x.legacy_id=c.conflict_modifier_id), c.conflict_modifier_id),
 update_time=now()
WHERE EXISTS (SELECT 1 FROM kord_id_mapping x WHERE x.legacy_id IN (c.modifier_id, c.conflict_modifier_id));

UPDATE user_kord_breach_preset p
SET total_score = totals.score, update_time=now()
FROM (
 SELECT p0.email, p0.slot_no, coalesce(sum(m.score), 0)::integer AS score
 FROM user_kord_breach_preset p0
 LEFT JOIN user_kord_breach_preset_modifier pm
 ON pm.email=p0.email AND pm.slot_no=p0.slot_no
 LEFT JOIN kord_breach_modifier m ON m.id=pm.modifier_id
 GROUP BY p0.email, p0.slot_no
) totals
WHERE p.email=totals.email AND p.slot_no=totals.slot_no
 AND p.total_score IS DISTINCT FROM totals.score
;
SELECT 'canonical_modifiers' AS check_name, count(*) AS row_count
FROM kord_breach_modifier m JOIN kord_id_mapping x ON m.id=x.source_id;
COMMIT;
