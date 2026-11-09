import ast
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
from custom_module import weapon_modding_static_json as module
from custom_module import weapon_modding_snapshot_cleanup as cleanup


def summary(key, slots=0):
    return {'id': key, 'name_en': key, 'slot_count': slots, 'mod_properties': None}


class ModdingStaticTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.summaries = {key: summary(key, slots) for key, slots in [('g1', 1), ('g2', 1), ('r', 1), ('l', 0), ('c', 0), ('p', 0)]}
        self.preset = {'item': self.summaries['p'], 'base_item_id': 'g1', 'is_default': False,
                       'ergonomics': None, 'recoil_vertical': 0, 'recoil_horizontal': None, 'moa': 2.5}
        self.link = {'is_listed': False, 'is_default_reference': True, 'sort_order': None}

    def page(self, field, values, params, **context):
        start = (params['page'] - 1) * params['page_size']
        return {'total': len(values), 'page': params['page'], 'page_size': params['page_size'],
                field: values[start:start + params['page_size']], **context}

    def fetch(self, endpoint, **params):
        self.calls.append((endpoint, params))
        parts = endpoint.split('/')
        if endpoint == 'weapons':
            return self.page('weapons', [{'item': self.summaries[k], 'weapon_properties': {},
                                         'preset_count': int(k == 'g1')} for k in ('g1', 'g2')], params)
        if parts[0] == 'weapons':
            return self.page('presets', [{**self.preset, 'link': self.link}] if parts[1] == 'g1' else [], params,
                             weapon_item_id=parts[1])
        if parts[0] == 'presets':
            return copy.deepcopy({'preset': self.preset, 'components': [
                {'component_index': i, 'quantity': 1, 'attributes': {'x': [1, {'v': None}]},
                 'item': self.summaries['c']} for i in range(2)],
                 'weapon_links': [{'weapon_item_id': 'g1', **self.link}], 'composition_type': 'flat_source_list'})
        key = parts[1]
        if len(parts) > 2:
            keys = ['r', 'l'] if key == 'r' else ['r']  # Shared part plus a cycle to itself.
            return self.page('candidates', [{'item': self.summaries[k]} for k in keys], params,
                             item_id=key, slot_id='s', validation_scope='slot_filters_only')
        slot = {'item_id': key, 'slot_id': 's', 'filters': {k: [] for k in
                ('allowed_items', 'excluded_items', 'allowed_categories', 'excluded_categories')}}
        return copy.deepcopy({'item': self.summaries[key], 'slots': [slot] if key in ('g1', 'g2', 'r') else [],
                              'categories': [], 'allowed_ammo': [], 'weapon_properties': None,
                              'conflicts': {'items': [], 'categories': [], 'slots': []}})

    def test_all_pages_recursive_candidates_and_flat_preset_components(self):
        with patch.object(module, 'PAGE_SIZE', 1):
            listing, bundles = module.collect_snapshot(self.fetch)
        self.assertEqual(listing['total'], 2)
        self.assertNotIn('page', listing)
        self.assertEqual(set(bundles['g1']['items']), {'g1', 'r', 'l', 'c'})
        self.assertEqual(set(bundles['g2']['items']), {'g2', 'r', 'l'})
        self.assertEqual(sum(path == 'items/r' for path, _ in self.calls), 1)
        self.assertEqual(bundles['g1']['presets']['p']['components'][1]['component_index'], 1)
        self.assertEqual(bundles['g1']['presets']['p']['components'][0]['attributes'], {'x': [1, {'v': None}]})
        self.assertFalse(bundles['g1']['presets']['p']['preset']['is_default'])
        self.assertTrue(bundles['g1']['preset_references']['presets'][0]['link']['is_default_reference'])
        self.assertEqual(bundles['g1']['slot_candidates']['r']['s']['validation_scope'], 'slot_filters_only')

    def test_pagination_duplicates_truncation_and_owner_mismatch_rejected(self):
        for change in ({'candidates': []}, {'item_id': 'other'}, {'slot_id': 'other'},
                       {'validation_scope': 'full_validation'}, {'page_size': 1000}):
            def fetch(endpoint, **params):
                data = self.fetch(endpoint, **params)
                if endpoint.endswith('/candidates'):
                    data.update(change)
                return data
            with self.subTest(change=change), self.assertRaises(ValueError):
                module.collect_snapshot(fetch)
        def duplicate(endpoint, **params):
            data = self.fetch(endpoint, **params)
            if endpoint == 'weapons' and params['page'] == 2:
                data['weapons'][0]['item'] = self.summaries['g1']
            return data
        with patch.object(module, 'PAGE_SIZE', 1), self.assertRaisesRegex(ValueError, 'Duplicate'):
            module.collect_snapshot(duplicate)

    def test_empty_and_changed_source_cannot_publish(self):
        def empty(endpoint, **params):
            return self.page('weapons', [], params)
        with self.assertRaisesRegex(ValueError, 'empty'):
            module.collect_snapshot(empty)
        count = 0
        def changed(endpoint, **params):
            nonlocal count
            data = self.fetch(endpoint, **params)
            if endpoint == 'weapons':
                count += 1
                if count == 2:
                    data['weapons'][0]['preset_count'] += 1
            return data
        with self.assertRaisesRegex(ValueError, 'changed'):
            module.collect_snapshot(changed)

    def test_item_or_preset_summary_drift_is_rejected(self):
        for endpoint in ('items/r', 'presets/p'):
            def changed(path, **params):
                data = self.fetch(path, **params)
                if path == endpoint:
                    key = 'item' if path.startswith('items/') else 'preset'
                    if key == 'item':
                        data[key]['name_en'] = 'changed'
                    else:
                        data[key]['ergonomics'] = 1
                return data
            with self.subTest(endpoint=endpoint), self.assertRaisesRegex(ValueError, 'mismatch|changed'):
                module.collect_snapshot(changed)

    def test_atomic_manifest_and_failure_keep_previous_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = module.generate_weapon_modding_static_json(tmp, self.fetch)
            root = Path(tmp)
            index = root / 'static/modding/v3/index.json'
            before = index.read_bytes()
            for path in [manifest['weapons_list'], *manifest['weapons'].values()]:
                self.assertEqual(json.loads((root / path.lstrip('/')).read_text())['status'], 200)
            def fail(endpoint, **params):
                if endpoint == 'items/r':
                    raise RuntimeError('API unavailable')
                return self.fetch(endpoint, **params)
            with self.assertRaises(RuntimeError):
                module.generate_weapon_modding_static_json(tmp, fail)
            self.assertEqual(index.read_bytes(), before)
            original = module.write_atomic
            def disk_full(path, data):
                if path.name == 'g2.json':
                    raise OSError('disk full')
                original(path, data)
            with patch.object(module, 'write_atomic', side_effect=disk_full), self.assertRaises(OSError):
                module.generate_weapon_modding_static_json(tmp, self.fetch)
            self.assertEqual(index.read_bytes(), before)

    def test_manifest_write_failure_and_traversal_limit_preserve_old_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            module.generate_weapon_modding_static_json(tmp, self.fetch)
            index = Path(tmp) / 'static/modding/v3/index.json'
            before = index.read_bytes()
            original = module.write_atomic
            def fail(path, data):
                if path.name == 'index.json':
                    raise OSError('manifest write failed')
                original(path, data)
            with patch.object(module, 'write_atomic', side_effect=fail), self.assertRaises(OSError):
                module.generate_weapon_modding_static_json(tmp, self.fetch)
            self.assertEqual(index.read_bytes(), before)
            with patch.object(module, 'MAX_ITEMS', 1), self.assertRaisesRegex(ValueError, 'limit'):
                module.generate_weapon_modding_static_json(tmp, self.fetch)
            self.assertEqual(index.read_bytes(), before)

    def test_item_dag_triggers_only_after_successful_upsert(self):
        root = Path(__file__).resolve().parents[1]
        tree = ast.parse((root / 'dags/dags_item.py').read_text())
        assignment = next(node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == 'publish_modding_task'
                                  for target in node.targets))
        options = {arg.arg: ast.literal_eval(arg.value) for arg in assignment.value.keywords}
        self.assertEqual(options['trigger_dag_id'], 'dags_weapon_modding_static_json')
        self.assertNotIn('trigger_rule', options)  # Default ALL_SUCCESS; never trigger after ALL_DONE cleanup.
        dependencies = [node for node in ast.walk(tree) if isinstance(node, ast.BinOp)
                        and isinstance(node.op, ast.RShift) and isinstance(node.left, ast.Name)
                        and isinstance(node.right, ast.Name)]
        self.assertTrue(any(node.left.id == 'upsert_item_task' and node.right.id == 'publish_modding_task'
                            for node in dependencies))
        ast.parse((root / 'dags/dags_weapon_modding_static_json.py').read_text())

    def test_api_response_contract_and_path_encoding(self):
        response = Mock()
        response.json.return_value = {'status': 200, 'msg': 'OK', 'data': {'ok': True}}
        with patch.object(module, 'get_api_response', return_value=response) as request:
            self.assertEqual(module.fetch_data('weapons', page=1, page_size=100), {'ok': True})
            self.assertIn('/api/modding/v3/weapons?page=1&page_size=100', request.call_args.args[0])
        for value in ('.', '..', '', ' x'):
            with self.assertRaises(ValueError):
                module.path_id(value)
        self.assertEqual(module.path_id('a/b'), 'a%2Fb')

    def test_publication_holds_ingestion_lock_and_releases_on_failure(self):
        cursor = Mock()
        conn = Mock()
        conn.cursor.return_value.__enter__ = Mock(return_value=cursor)
        conn.cursor.return_value.__exit__ = Mock(return_value=False)
        hook = SimpleNamespace(PostgresHook=Mock(return_value=SimpleNamespace(get_conn=lambda: conn)))
        def generate():
            cursor.execute.assert_any_call('SELECT pg_advisory_xact_lock(%s)', (724106110,))
            self.assertFalse(conn.autocommit)
            raise RuntimeError('API unavailable')
        with patch.dict(sys.modules, {'airflow.providers.postgres.hooks.postgres': hook}), \
                patch.object(module, 'generate_weapon_modding_static_json', side_effect=generate), \
                self.assertRaises(RuntimeError):
            module.publish_weapon_modding_static_json()
        conn.close.assert_called_once()

    def test_cleanup_keeps_three_latest_and_protects_active_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifests = [module.generate_weapon_modding_static_json(tmp, self.fetch) for _ in range(5)]
            base = Path(tmp) / 'static/modding/v3'
            for i, data in enumerate(manifests):
                os.utime(base / 'snapshots' / data['generation'], (100 + i, 100 + i))
            result = cleanup.cleanup_weapon_modding_snapshots(tmp, now=1000)
            self.assertEqual(result['deleted'], 2)
            self.assertEqual(len(list((base / 'snapshots').iterdir())), 3)
            # Roll back the active pointer to the oldest remaining generation.
            rollback = manifests[2]
            (base / 'index.json').write_text(json.dumps({'status': 200, 'msg': 'OK', 'data': rollback}))
            extra = base / 'snapshots' / ('f' * 32)
            extra.mkdir()
            os.utime(extra, (200, 200))
            cleanup.cleanup_weapon_modding_snapshots(tmp, now=1000)
            self.assertTrue((base / 'snapshots' / rollback['generation']).exists())

    def test_cleanup_corrupt_manifest_and_symlinks_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            for _ in range(4):
                module.generate_weapon_modding_static_json(tmp, self.fetch)
            base = Path(tmp) / 'static/modding/v3'
            symlink = base / 'snapshots' / ('f' * 32)
            symlink.symlink_to(base, target_is_directory=True)
            foreign = base / 'snapshots' / 'keep-me'
            foreign.mkdir()
            cleanup.cleanup_weapon_modding_snapshots(tmp, dry_run=True)
            self.assertEqual(len(list((base / 'snapshots').iterdir())), 6)
            (base / 'index.json').write_text('{broken')
            with self.assertRaises(ValueError):
                cleanup.cleanup_weapon_modding_snapshots(tmp)
            self.assertTrue(symlink.is_symlink())
            self.assertTrue(foreign.exists())


if __name__ == '__main__':
    unittest.main()
