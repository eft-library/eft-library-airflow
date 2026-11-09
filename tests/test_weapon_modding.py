"""Source mapping and isolated PostgreSQL synchronization checks."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
from custom_module.weapon_modding import build_modding_rows, sync_modding_rows
from custom_module import tarkov_json_api as api
from custom_module.queries.item import TRUNCATE_ITEM_PENALTIES

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT.parent / 'eft-library-back'
SAMPLE = ROOT / 'tests/item.json'


class SnapshotContractTests(unittest.TestCase):
    def test_empty_and_partial_snapshots_are_rejected(self):
        for data in ({}, {'items': {}, 'itemCategories': {}},
                     {'items': {'x': {'id': 'x'}}, 'itemCategories': {'c': {'id': 'c', 'parent': ''}}}):
            with self.assertRaises((KeyError, ValueError)):
                build_modding_rows(data)

    def test_default_only_link_and_nested_values_are_preserved(self):
        def item(key, props):
            return {'id': key, 'properties': props, 'categories': ['c'],
                    'conflictingItems': [], 'conflictingSlotIds': ['undefined'],
                    'conflictingCategories': [], 'containsItems': []}
        gun = item('g', {'propertiesType': 'ItemPropertiesWeapon', 'slots': [],
                         'presets': [], 'defaultPreset': 'p'})
        preset = item('p', {'propertiesType': 'ItemPropertiesPreset', 'baseItem': 'g'})
        preset['containsItems'] = [{'item': 'g', 'count': 1, 'attributes': {'nested': [1, 2]}}] * 2
        mod = item('m', {'propertiesType': 'ItemPropertiesScope', 'slots': [], 'zoomLevels': [[1, 4], [2.5]],
                         'recoilModifier': 0, 'ergonomics': None})
        rows = build_modding_rows({'items': {'g': gun, 'p': preset, 'm': mod},
                                  'itemCategories': {'c': {'id': 'c', 'parent': ''}}})
        self.assertEqual(rows['weapon_preset_links'], [('g', 'p', False, True, None)])
        self.assertEqual(rows['item_mod_properties'][0][2:6], (None, 0, None, [[1, 4], [2.5]]))
        self.assertEqual(len(rows['item_preset_components']), 2)
        self.assertEqual(rows['item_conflicting_slots'][0], ('g', 'undefined', 0))


@unittest.skipUnless(SAMPLE.exists(), 'Local source snapshot required')
class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SAMPLE.read_text())['data']

    def test_real_source_mapping_preserves_paths_scales_and_duplicates(self):
        rows = build_modding_rows(self.data)
        self.assertEqual(len(rows['item_slots']), 3673)
        self.assertEqual(len(rows['item_slot_item_filters']), 40854)
        receiver = '55d355e64bdc2d962f8b4569'
        slot = next(r for r in rows['item_slots'] if r[0] == receiver and r[2] == 'mod_sight_rear')
        sights = [r for r in rows['item_slot_item_filters'] if r[:2] == slot[:2] and r[2] == 'allowed']
        self.assertEqual(len(sights), 16)
        props = next(r for r in rows['item_mod_properties'] if r[0] == receiver)
        self.assertEqual(props[3], -0.01)
        self.assertEqual(props[7], -1)
        self.assertNotIn('weapon_items,', TRUNCATE_ITEM_PENALTIES)

    def test_partial_snapshot_and_unknown_reference_fail_before_sync(self):
        for mutate in (
            lambda d: d['items']['5447a9cd4bdc2dbd208b4567'].pop('conflictingItems'),
            lambda d: d['items']['5447a9cd4bdc2dbd208b4567']['categories'].append('missing'),
            lambda d: d['items']['5447a9cd4bdc2dbd208b4567']['properties'].pop('slots'),
        ):
            data = copy.deepcopy(self.data)
            mutate(data)
            with self.assertRaises((ValueError, KeyError)):
                build_modding_rows(data)

    def test_fetch_uses_one_source_snapshot_and_keeps_raw_keys(self):
        gun = '5447a9cd4bdc2dbd208b4567'
        key = self.data['items'][gun]['name']
        with patch.object(api, '_request_json', side_effect=[{'data': self.data},
                {'data': {key: 'English'}}, {'data': {key: '한국어'}}, {'data': {key: '日本語'}}]) as request:
            snapshot = api.get_item_snapshot()
        self.assertEqual([c.args[0] for c in request.call_args_list],
                         ['regular/items', 'regular/items_en', 'regular/items_ko', 'regular/items_ja'])
        self.assertEqual(snapshot['data']['items'][gun]['name'], key)
        self.assertEqual(snapshot['names']['ko'][gun]['name'], '한국어')
        self.assertEqual(next(i for i in snapshot['items'] if i['id'] == gun)['name'], 'English')


@unittest.skipUnless(SAMPLE.exists() and BACK.exists() and importlib.util.find_spec('pgserver')
                     and importlib.util.find_spec('psycopg2'), 'pgserver, psycopg2 and backend DDL required')
class DatabaseTests(unittest.TestCase):
    def test_full_snapshot_repeat_removal_and_rollback(self):
        import pgserver
        import psycopg2
        from psycopg2.extras import execute_values
        data = json.loads(SAMPLE.read_text())['data']
        rows = build_modding_rows(data)
        with tempfile.TemporaryDirectory(prefix='airflow-modding-') as directory:
            server = pgserver.get_server(Path(directory) / 'postgres', cleanup_mode='delete')
            try:
                with psycopg2.connect(server.get_uri()) as conn:
                    with conn.cursor() as cur:
                        cur.execute('CREATE TABLE items (id text PRIMARY KEY); CREATE TABLE weapon_items (item_id text PRIMARY KEY)')
                        cur.execute((BACK / 'sql/migrations/20261110_weapon_modding.sql').read_text())
                        execute_values(cur, 'INSERT INTO items VALUES %s', [(k,) for k in data['items']])
                        weapons = [(k,) for k, x in data['items'].items() if (x['properties'] or {}).get('propertiesType') == 'ItemPropertiesWeapon']
                        execute_values(cur, 'INSERT INTO weapon_items VALUES %s', weapons)
                        sync_modding_rows(cur, rows)
                    conn.commit()
                    with conn.cursor() as cur:
                        sync_modding_rows(cur, rows)
                        cur.execute('SELECT count(*) FROM item_slot_item_filters')
                        self.assertEqual(cur.fetchone()[0], 40854)
                    conn.commit()
                    modified = copy.deepcopy(data)
                    modified['items']['55d355e64bdc2d962f8b4569']['properties']['slots'] = []
                    with conn.cursor() as cur:
                        sync_modding_rows(cur, build_modding_rows(modified))
                        cur.execute("SELECT count(*) FROM item_slots WHERE item_id='55d355e64bdc2d962f8b4569'")
                        self.assertEqual(cur.fetchone()[0], 0)
                        # A failure after replacement must restore the previously committed snapshot.
                        with self.assertRaises(psycopg2.Error):
                            cur.execute('SELECT 1/0')
                    conn.rollback()
                    with conn.cursor() as cur:
                        cur.execute("SELECT count(*) FROM item_slots WHERE item_id='55d355e64bdc2d962f8b4569'")
                        self.assertEqual(cur.fetchone()[0], 4)
                    with conn.cursor() as cur:
                        sync_modding_rows(cur, build_modding_rows(modified))
                    conn.commit()
                    with conn.cursor() as cur:
                        cur.execute("SELECT count(*) FROM item_slot_item_filters WHERE item_id='55d355e64bdc2d962f8b4569'")
                        self.assertEqual(cur.fetchone()[0], 0)
            finally:
                server.cleanup()


if __name__ == '__main__':
    unittest.main()
