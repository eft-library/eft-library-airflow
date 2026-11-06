import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
from custom_module.kord_breach import normalize_season, persist_modifiers, fetch_modifiers, load_mapping


class KordBreachTests(unittest.TestCase):
    def setUp(self):
        self.mapping = {'season_id': 's', 'modifiers': [
            {'source_id': 'g', 'legacy_id': 'global', 'category': 'global', 'sort_order': 1},
            {'source_id': 'p', 'legacy_id': 'perk', 'category': 'negative', 'sort_order': 2},
            {'source_id': 'q', 'legacy_id': 'other', 'category': 'positive', 'sort_order': 3}]}
        self.payload = {'id': 's', 'perks': {'common': [
            {'id': 'g', 'name': 'Global', 'description': 'Common effect', 'points': None,
             'imageLink': 'https://example.com/g.webp', 'exclusiveToPerks': []}], 'personal': [
            {'id': 'p', 'name': 'Perk', 'description': 'Effect', 'points': 4,
             'imageLink': 'https://example.com/p.webp', 'exclusiveToPerks': ['q']},
            {'id': 'q', 'name': 'Other', 'description': 'Other effect', 'points': -2,
             'imageLink': 'https://example.com/q.webp', 'exclusiveToPerks': []}]}}
        self.localized = {lang: copy.deepcopy(self.payload) for lang in ('en', 'ko', 'ja')}

    def test_fields_points_and_symmetric_conflicts(self):
        rows, conflicts = normalize_season(self.localized, self.mapping)
        self.assertEqual(rows[0][8], 0)
        self.assertEqual(rows[1][1], 'negative')
        self.assertEqual(rows[1][8], 4)
        self.assertEqual(conflicts, [('p', 'q'), ('q', 'p')])
        self.assertEqual(len(rows[0]), 11)

    def test_missing_translations_not_saved_as_keys(self):
        self.localized['ko']['perks']['personal'][0].update(name='p name', description='p description')
        rows, _ = normalize_season(self.localized, self.mapping)
        self.assertIsNone(rows[1][3])
        self.assertIsNone(rows[1][6])
        self.localized['en']['perks']['personal'][0]['name'] = 'p name'
        with self.assertRaisesRegex(ValueError, 'English'):
            normalize_season(self.localized, self.mapping)

    def test_incomplete_or_new_source_rejected(self):
        self.localized['en']['perks']['personal'].pop()
        with self.assertRaises(ValueError):
            normalize_season(self.localized, self.mapping)

    def test_language_metadata_drift_rejected(self):
        self.localized['ja']['perks']['personal'][0]['points'] = 5
        with self.assertRaisesRegex(ValueError, 'changed'):
            normalize_season(self.localized, self.mapping)

    def test_unknown_conflict_and_duplicate_rejected(self):
        self.localized['en']['perks']['personal'][0]['exclusiveToPerks'] = ['missing']
        with self.assertRaisesRegex(ValueError, 'unknown'):
            normalize_season(self.localized, self.mapping)
        self.setUp()
        self.localized['en']['perks']['personal'].append(copy.deepcopy(self.payload['perks']['personal'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            normalize_season(self.localized, self.mapping)

    def test_season_rollover_rejected(self):
        with patch('custom_module.kord_breach.get_json_data', side_effect=[self.payload] * 3 + [{**self.payload, 'id': 'next'}]):
            with self.assertRaisesRegex(ValueError, 'Season changed'):
                fetch_modifiers(self.mapping)

    def test_legacy_ids_stop_before_writes(self):
        cur, bulk = MagicMock(), MagicMock()
        cur.fetchall.return_value = [('perk',)]
        rows, edges = normalize_season(self.localized, self.mapping)
        with self.assertRaisesRegex(ValueError, 'migration'):
            persist_modifiers(cur, rows, edges, self.mapping, bulk)
        bulk.assert_not_called()

    def test_reasons_retained_and_scores_recalculated(self):
        cur, bulk = MagicMock(), MagicMock()
        cur.fetchall.side_effect = [[('g',), ('p',), ('q',)], [('p',)], [('p', 'q', 'curated reason')]]
        rows, edges = normalize_season(self.localized, self.mapping)
        persist_modifiers(cur, rows, edges, self.mapping, bulk)
        self.assertEqual(bulk.call_args_list[1].args[2], [('p', 'q', 'curated reason'), ('q', 'p', None)])
        self.assertIn('IS DISTINCT FROM', cur.execute.call_args.args[0])

    def test_reviewed_mapping_unique(self):
        mapping = load_mapping()
        self.assertEqual(len(mapping['modifiers']), 40)
        self.assertEqual(len({r['source_id'] for r in mapping['modifiers']}), 40)
        self.assertEqual(len({r['legacy_id'] for r in mapping['modifiers']}), 40)
