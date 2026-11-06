import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
from custom_module.progress_items import (
    normalize_progress_items, persist_progress_items, COLLECTOR_TASK_ID, REBIRTH_TASK_ID,
)


class ProgressItemTests(unittest.TestCase):
    def setUp(self):
        self.data = {'tasks': {
            COLLECTOR_TASK_ID: {'id': COLLECTOR_TASK_ID, 'objectives': [
                {'type': 'giveItem', 'items': ['shared', 'kappa'], 'count': 1, 'optional': False},
                {'type': 'giveItem', 'items': ['optional'], 'count': 1, 'optional': True},
                {'type': 'findItem', 'items': ['find-only'], 'count': 1}]},
            REBIRTH_TASK_ID: {'id': REBIRTH_TASK_ID, 'objectives': [
                {'type': 'giveItem', 'items': ['shared', 'figure-a', 'figure-b'], 'count': 1},
                {'type': 'giveItem', 'items': ['figure-a'], 'count': 2}]}},
            'prestige': [{'prestigeLevel': 1, 'conditions': [
                {'type': 'taskStatus', 'task': REBIRTH_TASK_ID, 'status': ['complete']},
                {'type': 'haveItem', 'items': ['rubles'], 'count': 10000000}]}]}

    def test_candidate_union_deduplication_and_scopes(self):
        groups = normalize_progress_items(self.data)
        self.assertEqual(groups, {'Kappa': ['kappa', 'shared'], 'Rebirth': ['figure-a', 'figure-b', 'shared']})
        # The same item must remain in both checklists. Money and optional/find-only goals are excluded.
        self.assertNotIn('rubles', groups['Rebirth'])

    def test_tasks_array_also_supported(self):
        self.data['tasks'] = list(self.data['tasks'].values())
        self.assertEqual(len(normalize_progress_items(self.data)['Kappa']), 2)

    def test_missing_source_or_changed_prestige_rejected(self):
        cases = []
        source = copy.deepcopy(self.data)
        source['tasks'].pop(COLLECTOR_TASK_ID)
        cases.append(source)
        source = copy.deepcopy(self.data)
        source['prestige'][0]['conditions'][0]['task'] = 'different-task'
        cases.append(source)
        source = copy.deepcopy(self.data)
        source['tasks'][REBIRTH_TASK_ID]['objectives'] = []
        cases.append(source)
        for source in cases:
            with self.assertRaises(ValueError):
                normalize_progress_items(source)

    def test_incomplete_objective_rejected_instead_of_silent_deletion(self):
        for value in [[], [None], [''], 'not-a-list']:
            self.data['tasks'][REBIRTH_TASK_ID]['objectives'][0]['items'] = value
            with self.assertRaises(ValueError):
                normalize_progress_items(self.data)

    def test_duplicate_quest_ids_rejected(self):
        self.data['tasks'] = list(self.data['tasks'].values()) * 2
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            normalize_progress_items(self.data)

    def test_legacy_primary_key_blocks_writes(self):
        cursor, bulk = MagicMock(), MagicMock()
        cursor.fetchone.return_value = (['id'],)
        with self.assertRaisesRegex(ValueError, 'migration'):
            persist_progress_items(cursor, normalize_progress_items(self.data), bulk)
        bulk.assert_not_called()

    def test_missing_items_blocks_writes(self):
        cursor, bulk = MagicMock(), MagicMock()
        cursor.fetchone.return_value = (['id', 'progress_type'],)
        cursor.fetchall.return_value = [('shared',)]
        with self.assertRaisesRegex(ValueError, 'missing'):
            persist_progress_items(cursor, normalize_progress_items(self.data), bulk)
        bulk.assert_not_called()

    def test_delete_is_type_scoped_and_user_progress_is_never_written(self):
        groups = normalize_progress_items(self.data)
        cursor, bulk = MagicMock(), MagicMock()
        cursor.fetchone.return_value = (['id', 'progress_type'],)
        cursor.fetchall.return_value = [(i,) for i in {'shared', 'kappa', 'figure-a', 'figure-b'}]
        persist_progress_items(cursor, groups, bulk)
        inserted = bulk.call_args.args[2]
        self.assertIn(('shared', 'Kappa'), inserted)
        self.assertIn(('shared', 'Rebirth'), inserted)
        deletes = [call for call in cursor.execute.call_args_list if 'DELETE FROM' in call.args[0]]
        self.assertEqual([c.args[1][0] for c in deletes], ['Kappa', 'Rebirth'])
        self.assertTrue(all('user_progress_item' not in c.args[0] for c in cursor.execute.call_args_list))
