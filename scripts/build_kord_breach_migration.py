"""Build the reviewed, rerunnable ID-only migration. Never connects to a database."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'plugins'))
from custom_module.queries.kord_breach import RECALCULATE_SCORES


def build_sql(mapping):
    def literal(value):
        return "'" + value.replace("'", "''") + "'"
    values = ',\n'.join('(' + ', '.join(literal(row[key]) for key in ('legacy_id', 'source_id', 'name_en')) + ')'
                        for row in mapping['modifiers'])
    return """-- Generated from plugins/custom_module/kord_breach_mapping.json.
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
""" + values + """;
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
""" + RECALCULATE_SCORES + """;
SELECT 'canonical_modifiers' AS check_name, count(*) AS row_count
FROM kord_breach_modifier m JOIN kord_id_mapping x ON m.id=x.source_id;
COMMIT;
"""


if __name__ == '__main__':
    mapping = json.loads((ROOT / 'plugins/custom_module/kord_breach_mapping.json').read_text())
    path = ROOT / 'sql/migrations/20261106_kord_breach_source_ids.sql'
    path.write_text(build_sql(mapping))
    print(path)
