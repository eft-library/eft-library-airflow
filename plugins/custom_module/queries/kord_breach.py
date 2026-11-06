"""SQL for canonical-ID KORD BREACH metadata maintenance."""
UPSERT_MODIFIERS = """
INSERT INTO kord_breach_modifier
 (id, modifier_category, name_en, name_ko, name_ja, effect_en, effect_ko, effect_ja,
  score, icon_url, sort_order)
VALUES %s
ON CONFLICT (id) DO UPDATE SET
 name_en=excluded.name_en,
 name_ko=coalesce(excluded.name_ko, kord_breach_modifier.name_ko),
 name_ja=coalesce(excluded.name_ja, kord_breach_modifier.name_ja),
 effect_en=excluded.effect_en,
 effect_ko=coalesce(excluded.effect_ko, kord_breach_modifier.effect_ko),
 effect_ja=coalesce(excluded.effect_ja, kord_breach_modifier.effect_ja),
 score=excluded.score, icon_url=excluded.icon_url, update_time=now()
"""

INSERT_CONFLICTS = """
INSERT INTO kord_breach_modifier_conflict (modifier_id, conflict_modifier_id, reason)
VALUES %s
"""

RECALCULATE_SCORES = """
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
"""
