import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch
from contextlib import closing

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
from custom_module import tarkov_json_api as api
from custom_module.v3.item_price_task_func import (
    v3_item_price_row, v3_item_trader_price_rows, v3_item_price_history_rows,
)

ROOT = Path(__file__).resolve().parents[1]


def dag_function(path, name, namespace):
    tree = ast.parse((ROOT / path).read_text())
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), path, 'exec'), namespace)
    return namespace[name]


class PriceSeasonTests(unittest.TestCase):
    def setUp(self):
        self.item = {'id': 'item', 'sellFor': [
            {'vendor': {'name': 'Trader'}, 'priceRUB': 100},
            {'vendor': {'name': 'Flea Market'}, 'priceRUB': 200},
        ], 'historicalPrices': [{'price': 200, 'timestamp': 1776431739000}]}
        self.season = {'id': 'season', 'name': 'Season', 'starts_at': None, 'ends_at': None}

    def test_scope_and_trader_ids(self):
        for mode, season in [('pvp', None), ('pve', None), ('pvp-season', 's1')]:
            self.assertEqual(v3_item_price_row(self.item, mode, {'Trader': 't'}, season)[2], season)
            row = v3_item_trader_price_rows(self.item, mode, {'Trader': 't'}, season)[0]
            self.assertEqual(row[3], season)
            self.assertEqual(v3_item_price_history_rows(self.item, mode, season)[0][3], season)
        self.assertNotEqual(
            v3_item_trader_price_rows(self.item, 'pvp-season', {'Trader': 't'}, 's1')[0][0],
            v3_item_trader_price_rows(self.item, 'pvp-season', {'Trader': 't'}, 's2')[0][0],
        )

    def test_season_validation_and_utc(self):
        with patch.object(api, 'get_json_data', return_value={'id': 's', 'name': 'Season', 'start': 1776431739000, 'end': None}):
            self.assertTrue(api.get_price_season()['starts_at'].endswith('+00:00'))
        for data in [{}, {'id': ''}, {'id': 's', 'start': 'bad'}]:
            with patch.object(api, 'get_json_data', return_value=data), self.assertRaises(ValueError):
                api.get_price_season()

    def test_invalid_items_rejected(self):
        for data in [{}, {'items': {}}, {'items': {'x': {}}},
                     {'items': {'x': {'id': 'x', 'lastLowPrice': 'bad'}}},
                     {'items': {'x': {'id': 'x', 'sellToTrader': [{}]}}}]:
            with self.assertRaises(ValueError):
                api.validate_price_items(data)

    def test_atomic_load_and_scoped_deletes(self):
        hook = MagicMock()
        conn = hook.return_value.get_conn.return_value
        cursor = conn.cursor.return_value
        bulk = MagicMock()
        ns = {'PostgresHook': hook, 'closing': closing, 'execute_values': bulk,
              '_load_item_lists': lambda: ([self.item], [self.item], {'season': self.season, 'items': [self.item]}),
              '_fetch_trader_name_map': lambda cursor: {'Trader': 't'},
              'v3_item_price_row': v3_item_price_row,
              'v3_item_trader_price_rows': v3_item_trader_price_rows,
              'v3_item_price_history_rows': v3_item_price_history_rows}
        fn = dag_function('dags/v3_dags_item_price.py', 'upsert_item_price', ns)
        fn('test')
        self.assertEqual(bulk.call_count, 3)
        conn.__exit__.assert_called_once_with(None, None, None)
        deletes = [call.args for call in cursor.execute.call_args_list if 'DELETE FROM' in call.args[0]]
        self.assertEqual(len(deletes), 3)
        self.assertEqual(deletes[0][1], ('season',))
        self.assertIn('season_id IS NULL', deletes[2][0])
        conn.reset_mock()
        bulk.side_effect = RuntimeError('write failed')
        with self.assertRaises(RuntimeError):
            fn('test')
        self.assertIs(conn.__exit__.call_args.args[0], RuntimeError)

    def test_fetch_failure_and_season_rollover_do_not_write_files(self):
        for seasons, items in [([self.season], RuntimeError("API failed")),
                               ([self.season, {**self.season, "id": "next"}], [self.item])]:
            ns = {"get_price_season": MagicMock(side_effect=seasons),
                  "get_item_prices": MagicMock(), "open": MagicMock()}
            if isinstance(items, Exception):
                ns["get_item_prices"].side_effect = items
            else:
                ns["get_item_prices"].return_value = items
            fn = dag_function('dags/v3_dags_item_price.py', 'fetch_item_price', ns)
            with self.assertRaises((RuntimeError, ValueError)):
                fn()
            ns["open"].assert_not_called()

    def test_static_modes_and_selected_season(self):
        ns = {}
        dag_function('dags/v3_dags_price_static_json.py', '_build_price_tiers', ns)
        rank = dag_function('dags/v3_dags_price_static_json.py', '_rank_payload', ns)
        result = rank([], selected_season_id='s1')
        self.assertIn('pvp-season_top_list', result)
        self.assertEqual(result['selected_season_id'], 's1')


if __name__ == '__main__':
    unittest.main()
