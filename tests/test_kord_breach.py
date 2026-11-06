import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
from custom_module.kord_breach import normalize_season, persist_modifiers, get_season_snapshot, normalize_snapshot


class KordBreachTests(unittest.TestCase):
    def setUp(self):
        self.payload = {'id': 's', 'perks': {'common': [
            {'id': 'g', 'name': 'Global', 'description': 'Common effect', 'points': None,
             'imageLink': 'https://example.com/g.webp', 'exclusiveToPerks': []}], 'personal': [
            {'id': 'p', 'name': 'Perk', 'description': 'Effect', 'points': 4,
             'imageLink': 'https://example.com/p.webp', 'exclusiveToPerks': ['q']},
            {'id': 'q', 'name': 'Other', 'description': 'Other effect', 'points': -2,
             'imageLink': 'https://example.com/q.webp', 'exclusiveToPerks': []}]}}
        self.localized = {lang: copy.deepcopy(self.payload) for lang in ('en', 'ko', 'ja')}

    def test_fields_points_source_order_and_symmetric_conflicts(self):
        rows, conflicts = normalize_season(self.localized)
        self.assertEqual([(r[0], r[1], r[8], r[10]) for r in rows],
                         [('g', 'global', 0, 1), ('p', 'negative', 4, 2), ('q', 'positive', -2, 3)])
        self.assertEqual(conflicts, [('p', 'q'), ('q', 'p')])

    def test_new_source_item_is_registered_without_mapping(self):
        new = {**self.payload['perks']['personal'][1], 'id': 'new-perk', 'name': 'New perk'}
        for payload in self.localized.values():
            payload['perks']['personal'].append(copy.deepcopy(new))
        rows, _ = normalize_season(self.localized)
        self.assertEqual(rows[-1][0], 'new-perk')
        self.assertEqual(rows[-1][1], 'positive')
        cur, bulk = MagicMock(), MagicMock()
        cur.fetchall.return_value = []
        persist_modifiers(cur, rows, [], bulk)
        self.assertIn(rows[-1], bulk.call_args_list[0].args[2])

    def test_source_removal_is_allowed_and_missing_ids_are_deactivated(self):
        for payload in self.localized.values():
            payload['perks']['personal'].pop()
            payload['perks']['personal'][0]['exclusiveToPerks'] = []
        rows, conflicts = normalize_season(self.localized)
        self.assertEqual([r[0] for r in rows], ['g', 'p'])
        cur, bulk = MagicMock(), MagicMock()
        cur.fetchall.return_value = []
        persist_modifiers(cur, rows, conflicts, bulk)
        deactivation = next(c for c in cur.execute.call_args_list if 'is_active=false' in c.args[0])
        self.assertEqual(deactivation.args[1], (['g', 'p'],))
        self.assertTrue(all('DELETE FROM kord_breach_modifier ' not in c.args[0] for c in cur.execute.call_args_list))

    def test_missing_translations_not_saved_as_keys(self):
        self.localized['ko']['perks']['personal'][0].update(name='p name', description='p description')
        rows, _ = normalize_season(self.localized)
        self.assertIsNone(rows[1][3])
        self.assertIsNone(rows[1][6])
        self.localized['en']['perks']['personal'][0]['name'] = 'p name'
        with self.assertRaisesRegex(ValueError, 'English'):
            normalize_season(self.localized)

    def test_new_season_is_accepted_between_runs(self):
        for payload in self.localized.values():
            payload['id'] = 'next-season'
        self.assertEqual(len(normalize_season(self.localized)[0]), 3)

    def test_language_metadata_drift_rejected(self):
        self.localized['ja']['perks']['personal'][0]['points'] = 5
        with self.assertRaisesRegex(ValueError, 'changed'):
            normalize_season(self.localized)

    def test_unknown_conflict_and_duplicate_rejected(self):
        self.localized['en']['perks']['personal'][0]['exclusiveToPerks'] = ['missing']
        with self.assertRaisesRegex(ValueError, 'unknown'):
            normalize_season(self.localized)
        self.setUp()
        self.localized['en']['perks']['personal'].append(copy.deepcopy(self.payload['perks']['personal'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            normalize_season(self.localized)

    def test_mid_collection_rollover_retries_instead_of_mixing_seasons(self):
        with patch('custom_module.kord_breach.get_json_data', side_effect=[self.payload] * 3 + [{**self.payload, 'id': 'next'}]):
            with self.assertRaisesRegex(ValueError, 'Season changed'):
                normalize_snapshot(get_season_snapshot())

    def test_reasons_retained_and_scores_recalculated(self):
        cur, bulk = MagicMock(), MagicMock()
        cur.fetchall.return_value = [('p', 'q', 'curated reason')]
        rows, edges = normalize_season(self.localized)
        persist_modifiers(cur, rows, edges, bulk)
        self.assertEqual(bulk.call_args_list[1].args[2], [('p', 'q', 'curated reason'), ('q', 'p', None)])
        self.assertIn('IS DISTINCT FROM', cur.execute.call_args.args[0])
        self.assertTrue(all('user_kord_breach_preset_modifier' not in c.args[0] or c.args[0].startswith('LOCK') or 'UPDATE user_kord_breach_preset p' in c.args[0] for c in cur.execute.call_args_list))

    def test_empty_snapshot_cannot_disable_everything(self):
        for payload in self.localized.values():
            payload['perks'] = {'common': [], 'personal': []}
        with self.assertRaisesRegex(ValueError, 'Empty'):
            normalize_season(self.localized)
        bulk = MagicMock()
        with self.assertRaises(ValueError):
            persist_modifiers(MagicMock(), [], [], bulk)
        bulk.assert_not_called()

    def test_single_group_can_be_empty_when_source_has_other_perks(self):
        for payload in self.localized.values():
            payload['perks']['common'] = []
        rows, _ = normalize_season(self.localized)
        self.assertEqual([r[0] for r in rows], ['p', 'q'])
