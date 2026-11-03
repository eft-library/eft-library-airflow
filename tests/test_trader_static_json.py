import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
from custom_module import trader_static_json as module


class TraderStaticTests(unittest.TestCase):
    def fetch(self, endpoint, **params):
        mode = params['game_mode']
        season = 'season' if mode == 'pvp-season' else None
        if endpoint == 'list':
            return {'game_mode': mode, 'season_id': season,
                    'traders': [{'id': 'trader'}, {'id': 'empty'}]}
        return {'game_mode': mode, 'season_id': season, 'page': params['page'],
                'page_size': params['page_size'], 'total': 1, 'offers': [{
                    'id': 'offer', 'trader_id': 'trader', 'game_mode': mode,
                    'season_id': season, 'costs': [{'item': {'id': 'rub'}, 'quantity': 10}],
                    'rewards': [{'item': {'id': 'item'}, 'quantity': 1}], 'task_unlocks': []}]}

    def test_publish_manifest_and_complete_details(self):
        with tempfile.TemporaryDirectory() as tmp:
            module.generate_trader_static_json(tmp, self.fetch)
            root = Path(tmp)
            index = json.loads((root / 'static/trader/v3/index.json').read_text())
            self.assertEqual(set(index['data']['modes']), {'pvp', 'pve', 'pvp-season'})
            for mode, entry in index['data']['modes'].items():
                for trader, path in entry['offers'].items():
                    data = json.loads((root / path.lstrip('/')).read_text())['data']
                    self.assertEqual(data['total'], 1 if trader == 'trader' else 0)
                    self.assertEqual(data['game_mode'], mode)
            self.assertEqual(index['data']['modes']['pvp-season']['season_id'], 'season')

    def test_request_failure_keeps_previous_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            module.generate_trader_static_json(tmp, self.fetch)
            path = Path(tmp) / 'static/trader/v3/index.json'
            before = path.read_bytes()
            def fail(endpoint, **params):
                if params['game_mode'] == 'pve':
                    raise RuntimeError('API failure')
                return self.fetch(endpoint, **params)
            with self.assertRaises(RuntimeError):
                module.generate_trader_static_json(tmp, fail)
            self.assertEqual(path.read_bytes(), before)

    def test_write_failure_keeps_previous_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            module.generate_trader_static_json(tmp, self.fetch)
            path = Path(tmp) / 'static/trader/v3/index.json'
            before = path.read_bytes()
            original = module.write_atomic
            def fail(path, data):
                if path.name == 'trader.json':
                    raise OSError('disk full')
                return original(path, data)
            with patch.object(module, 'write_atomic', side_effect=fail), self.assertRaises(OSError):
                module.generate_trader_static_json(tmp, self.fetch)
            self.assertEqual(path.read_bytes(), before)

    def test_truncated_and_scope_changed_pages_rejected(self):
        for change in ({'offers': []}, {'total': 2}, {'season_id': 'wrong'}, {'page': 2}):
            def fetch(endpoint, **params):
                data = self.fetch(endpoint, **params)
                if endpoint == 'offers':
                    data.update(change)
                return data
            with self.assertRaises(ValueError):
                module.collect_mode('pvp', fetch)

    def test_multi_page_and_duplicate_detection(self):
        def fetch(endpoint, **params):
            data = self.fetch(endpoint, **params)
            if endpoint == 'offers':
                data['total'] = 2
                data['offers'][0]['id'] = str(params['page'])
            return data
        with patch.object(module, 'PAGE_SIZE', 1):
            _, grouped = module.collect_mode('pvp', fetch)
            self.assertEqual(len(grouped['trader']), 2)
            def duplicate(endpoint, **params):
                data = fetch(endpoint, **params)
                if endpoint == 'offers':
                    data['offers'][0]['id'] = 'same'
                return data
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                module.collect_mode('pvp', duplicate)

    def test_restock_update_during_collection_rejected(self):
        count = 0
        def fetch(endpoint, **params):
            nonlocal count
            data = copy.deepcopy(self.fetch(endpoint, **params))
            if endpoint == 'list':
                count += 1
                data['traders'][0]['next_restock_at'] = count
            return data
        with self.assertRaisesRegex(ValueError, 'changed'):
            module.collect_mode('pvp', fetch)
