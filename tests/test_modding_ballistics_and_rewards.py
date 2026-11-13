import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugins'))
from custom_module.weapon_modding import build_modding_rows, sync_modding_rows
from custom_module.kord_breach_reward_static_json import generate_kord_breach_reward_static_json
from custom_module import weapon_modding_static_json as static

BACK=Path(__file__).resolve().parents[2]/'eft-library-back'


def fixture():
    def item(identity,props):
        return {'id':identity,'properties':props,'categories':['c'],'velocity':0,
                'conflictingItems':[],'conflictingSlotIds':[],'conflictingCategories':[]}
    return {'itemCategories':{'c':{'id':'c','parent':''}}, 'items':{
        'g':item('g',{'propertiesType':'ItemPropertiesWeapon','slots':[],'defaultPreset':None,'presets':[],
                     'centerOfImpact':0.01,'deviationCurve':1.35}),
        'a':item('a',{'propertiesType':'ItemPropertiesAmmo','initialSpeed':900})}}


class ExportTests(unittest.TestCase):
    def test_raw_values_keep_zero_and_missing_distinct(self):
        rows=build_modding_rows(fixture())['item_ballistics']
        self.assertEqual(rows[0],('g','ItemPropertiesWeapon',0.01,1.35,None,0,None))
        self.assertEqual(rows[1][-1],900)

    def test_curated_rewards_export_and_bad_response_preserves_file(self):
        data={'season_id':'kord-breach','total':1,'source_url':'manual:screen','source_revision':'r1',
              'collected_at':'2026-11-13T00:00:00Z','condition_logic':'or_groups_of_and_conditions',
              'rewards':[{'id':'reward','sort_order':0,'item':{'id':'a'},'unlock_conditions':[]}]}
        payload={'status':200,'msg':'OK','data':data}
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'rewards.json'
            generate_kord_breach_reward_static_json(path,lambda:payload)
            saved=path.read_text()
            self.assertEqual(json.loads(saved)['data'],data)
            for mutate in (lambda p:p.update(status=503),lambda p:p['data'].update(total=2)):
                bad=copy.deepcopy(payload);mutate(bad)
                with self.assertRaises(ValueError):generate_kord_breach_reward_static_json(path,lambda:bad)
                self.assertEqual(path.read_text(),saved)


@unittest.skipUnless(importlib.util.find_spec('pgserver') and BACK.exists(),'pgserver and backend required')
class BallisticsSyncTests(unittest.TestCase):
    def test_repeat_snapshot_missing_and_removed_rows_roll_back_atomically(self):
        import pgserver
        import psycopg2
        with tempfile.TemporaryDirectory() as d:
            server=pgserver.get_server(Path(d)/'db',cleanup_mode='delete')
            try:
                with psycopg2.connect(server.get_uri()) as conn:
                    with conn.cursor() as cur:
                        cur.execute('create table items(id text primary key);create table weapon_items(item_id text primary key);')
                        cur.execute((BACK/'sql/migrations/20261110_weapon_modding.sql').read_text())
                        cur.execute((BACK/'sql/migrations/20261113_rewards_and_modding_stats.sql').read_text())
                        cur.execute("insert into items values ('g'),('a');insert into weapon_items values ('g')")
                        sync_modding_rows(cur,build_modding_rows(fixture()))
                    conn.commit()
                    updated=fixture();updated['items']['a']['properties']['initialSpeed']=None
                    with conn.cursor() as cur:
                        sync_modding_rows(cur,build_modding_rows(updated))
                        cur.execute("select initial_speed_mps from item_ballistics where item_id='a'")
                        self.assertIsNone(cur.fetchone()[0])
                    conn.rollback()
                    with conn.cursor() as cur:
                        cur.execute("select initial_speed_mps from item_ballistics where item_id='a'")
                        self.assertEqual(cur.fetchone()[0],900)
                        updated=fixture();del updated['items']['a']
                        sync_modding_rows(cur,build_modding_rows(updated))
                        sync_modding_rows(cur,build_modding_rows(updated))
                        cur.execute("select count(*) from item_ballistics where item_id='a'")
                        self.assertEqual(cur.fetchone()[0],0)
            finally:
                server.cleanup()
