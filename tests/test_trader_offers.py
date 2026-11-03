import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
from custom_module.trader_offers import normalize_snapshot, persist_snapshots, fetch_snapshots


class TraderOfferTests(unittest.TestCase):
    def setUp(self):
        self.items = {'items': {'i': {'id': 'i', 'buyFromTrader': [
            {'trader': 't', 'minTraderLevel': 2, 'price': 100,
             'currencyItem': 'rub', 'buyLimit': 5, 'taskUnlock': 'quest'}]}}}
        self.barters = [{'id': 'b', 'trader': 't', 'minTraderLevel': 1,
                         'requiredItems': [{'item': 'material', 'count': 1.5}, {'item': 'material', 'count': 2}],
                         'offeredItem': {'item': 'i', 'count': 2}, 'buyLimit': -1}]
        self.traders = {'t': {'id': 't', 'resetTime': '2026-11-03T03:00:00Z'}}
        self.season = {'id': 's', 'name': 'S', 'starts_at': None, 'ends_at': None}

    def snapshot(self, mode='pvp', season=None):
        return normalize_snapshot(self.items, self.barters, self.traders, mode, season)

    def test_stable_identity_scope_and_price_changes(self):
        before = self.snapshot()
        self.items['items']['i']['buyFromTrader'][0].update(price=200, buyLimit=10)
        after = self.snapshot()
        self.assertEqual([o['id'] for o in before['offers']], [o['id'] for o in after['offers']])
        self.assertNotEqual(before['offers'][0]['id'], self.snapshot('pve')['offers'][0]['id'])
        self.assertNotEqual(self.snapshot('pvp-season', 's1')['offers'][0]['id'], self.snapshot('pvp-season', 's2')['offers'][0]['id'])
        purchase = next(o for o in after['offers'] if o['type'] == 'purchase')
        self.assertEqual(purchase['tasks'], ['quest'])
        self.assertEqual(purchase['costs']['rub'], 200)

    def test_aggregate_fractional_cost_and_unknown_limits(self):
        barter = next(o for o in self.snapshot()['offers'] if o['type'] == 'barter')
        self.assertEqual(float(barter['costs']['material']), 3.5)
        self.assertEqual(barter['raw_limit'], -1)
        self.assertIsNone(barter['limit'])
        self.assertIsNone(barter['unlimited'])
        for limit in [None, 0, -1]:
            self.items['items']['i']['buyFromTrader'][0]['buyLimit'] = limit
            purchase = next(o for o in self.snapshot()['offers'] if o['type'] == 'purchase')
            self.assertIsNone(purchase['unlimited'])
            self.assertEqual(purchase['raw_limit'], limit)

    def test_conflicting_duplicate_rejected(self):
        rows = self.items['items']['i']['buyFromTrader']
        rows.append({**rows[0], 'price': 300})
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            self.snapshot()

    def test_invalid_snapshot_rejected(self):
        original = copy.deepcopy(self.items)
        for field, value in [('price', 0), ('price', float('nan')), ('price', True),
                             ('minTraderLevel', 0), ('taskUnlock', {'id': 'quest'})]:
            self.items = copy.deepcopy(original)
            self.items['items']['i']['buyFromTrader'][0][field] = value
            with self.assertRaises(ValueError):
                self.snapshot()
        with self.assertRaises(ValueError):
            normalize_snapshot(original, [], self.traders, 'pvp')
        with self.assertRaises(ValueError):
            normalize_snapshot(original, self.barters, self.traders, 'pvp-season')

    def test_missing_reference_prevents_writes(self):
        cursor = MagicMock()
        cursor.fetchall.side_effect = [[('i',)], [('t',)]]
        bulk = MagicMock()
        with self.assertRaisesRegex(ValueError, 'missing items'):
            persist_snapshots(cursor, self.season, [self.snapshot()], bulk)
        bulk.assert_not_called()
        self.assertEqual(cursor.execute.call_count, 2)

    def test_scoped_deactivation_and_children_replacement(self):
        cursor = MagicMock()
        cursor.fetchall.side_effect = [[('i',), ('rub',), ('material',)], [('t',)]]
        bulk = MagicMock()
        persist_snapshots(cursor, self.season, [self.snapshot()], bulk)
        calls = cursor.execute.call_args_list
        deletes = [c for c in calls if c.args[0].startswith('DELETE')]
        self.assertEqual(len(deletes), 3)
        deactivation = next(c for c in calls if 'is_use=false' in c.args[0])
        self.assertIn('season_id IS NOT DISTINCT FROM', deactivation.args[0])
        self.assertEqual(deactivation.args[1][:2], ('pvp', None))

    def test_rollover_rejected(self):
        with patch('custom_module.trader_offers.get_price_season', side_effect=[self.season, {**self.season, 'id': 'next'}]), patch('custom_module.trader_offers.get_json_data', side_effect=[self.items, self.barters, self.traders] * 3):
            with self.assertRaisesRegex(ValueError, 'Season changed'):
                fetch_snapshots()


if __name__ == '__main__':
    unittest.main()
