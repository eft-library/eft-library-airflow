import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
from custom_module import trader_snapshot_cleanup as module


class TraderSnapshotCleanupTests(unittest.TestCase):
    now = 1_000_000

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / 'static/trader/v3'
        self.snapshots = self.base / 'snapshots'
        self.snapshots.mkdir(parents=True)

    def folder(self, number, age_hours=48):
        folder = self.snapshots / f'{number:032x}'
        folder.mkdir()
        (folder / 'payload.json').write_text('{}')
        modified = self.now - age_hours * 3600
        os.utime(folder, (modified, modified))
        return folder

    def manifest(self, active, references=None):
        refs = references or [active]
        data = {'generation': active.name, 'modes': {
            str(i): {'list': f'/static/trader/v3/snapshots/{folder.name}/pvp/list.json',
                     'offers': {}} for i, folder in enumerate(refs)}}
        (self.base / 'index.json').write_text(json.dumps({'status': 200, 'msg': 'OK', 'data': data}))

    def run_cleanup(self, **options):
        return module.cleanup_trader_snapshots(self.root, now=self.now,
                                               min_generations=options.pop('min_generations', 2), **options)

    def test_deletes_only_expired_unreferenced_folders(self):
        active = self.folder(1, 100)
        old_reference = self.folder(2, 80)
        expired = self.folder(3, 48)
        young = [self.folder(4, 2), self.folder(5, 1)]
        self.manifest(active, [active, old_reference])
        before = (self.base / 'index.json').read_bytes()
        result = self.run_cleanup()
        self.assertEqual(result['deleted'], 1)
        self.assertFalse(expired.exists())
        for folder in [active, old_reference, *young]:
            self.assertTrue(folder.exists())
        self.assertEqual((self.base / 'index.json').read_bytes(), before)

    def test_minimum_generations_survive_even_when_all_old(self):
        folders = [self.folder(i, 100 - i) for i in range(1, 16)]
        self.manifest(folders[0])
        result = self.run_cleanup(min_generations=12)
        self.assertEqual(result['deleted'], 2)
        self.assertTrue(folders[0].exists())
        self.assertTrue(all(folder.exists() for folder in folders[-12:]))

    def test_age_grace_period_survives_beyond_minimum_count(self):
        active = self.folder(1, 48)
        young = [self.folder(i, 2) for i in range(2, 20)]
        self.manifest(active)
        self.assertEqual(self.run_cleanup()['deleted'], 0)
        self.assertTrue(all(folder.exists() for folder in young))

    def test_dry_run_reports_without_deleting(self):
        folders = [self.folder(i, 50 - i) for i in range(1, 6)]
        self.manifest(folders[0])
        result = self.run_cleanup(dry_run=True)
        self.assertEqual(result['deleted'], 0)
        self.assertEqual(result['would_delete'], 2)
        self.assertTrue(all(folder.exists() for folder in folders))

    def test_missing_or_corrupt_manifest_prevents_deletion(self):
        folders = [self.folder(i) for i in range(1, 5)]
        with self.assertRaises(FileNotFoundError):
            self.run_cleanup()
        (self.base / 'index.json').write_text('{broken')
        with self.assertRaises(ValueError):
            self.run_cleanup()
        self.assertTrue(all(folder.exists() for folder in folders))
        self.manifest(folders[0])
        payload = json.loads((self.base / 'index.json').read_text())
        payload['data']['modes']['0']['list'] = '/unexpected/path.json'
        (self.base / 'index.json').write_text(json.dumps(payload))
        with self.assertRaises(ValueError):
            self.run_cleanup()
        self.assertTrue(all(folder.exists() for folder in folders))

    def test_manifest_change_before_delete_protects_new_reference(self):
        active, target = self.folder(1, 100), self.folder(2, 90)
        self.folder(3, 1)
        self.folder(4, 2)
        self.manifest(active)
        original = module.referenced_generations
        calls = 0

        def changed(base):
            nonlocal calls
            calls += 1
            if calls == 2:
                self.manifest(active, [active, target])
            return original(base)

        with patch.object(module, 'referenced_generations', side_effect=changed):
            self.assertEqual(self.run_cleanup()['deleted'], 0)
        self.assertTrue(target.exists())

    def test_foreign_names_and_symlinks_are_not_followed(self):
        active, old = self.folder(1, 100), self.folder(2, 90)
        self.folder(3, 1)
        self.folder(4, 2)
        self.manifest(active)
        outside = self.root / 'outside'
        outside.mkdir()
        marker = outside / 'keep.txt'
        marker.write_text('keep')
        (old / 'linked-content').symlink_to(outside, target_is_directory=True)
        os.utime(old, (self.now - 90 * 3600, self.now - 90 * 3600))
        linked_generation = self.snapshots / f'{5:032x}'
        linked_generation.symlink_to(outside, target_is_directory=True)
        foreign = self.snapshots / 'manual-backup'
        foreign.mkdir()
        self.assertEqual(self.run_cleanup()['deleted'], 1)
        self.assertTrue(marker.exists())
        self.assertTrue(linked_generation.is_symlink())
        self.assertTrue(foreign.exists())

    def test_environment_settings_and_invalid_retention(self):
        folders = [self.folder(i, 12 - i) for i in range(1, 6)]
        self.manifest(folders[0])
        with patch.dict(os.environ, {'TRADER_SNAPSHOT_RETENTION_HOURS': '6',
                                    'TRADER_SNAPSHOT_MIN_GENERATIONS': '2'}):
            result = module.cleanup_trader_snapshots(self.root, now=self.now)
        self.assertEqual(result['retention_hours'], 6)
        self.assertEqual(result['deleted'], 2)
        for hours in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                self.run_cleanup(retention_hours=hours)


if __name__ == '__main__':
    unittest.main()
