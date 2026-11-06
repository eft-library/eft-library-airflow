"""Exercise DAG callables without starting Airflow or touching the real DB."""
import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]


def load_functions(path, namespace):
    tree = ast.parse((ROOT / path).read_text())
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    exec(compile(ast.Module(body=functions, type_ignores=[]), path, 'exec'), namespace)
    return namespace


class CollectionFileTests(unittest.TestCase):
    def cases(self, tmp):
        return [
            ('dags/dags_progress_item.py', 'fetch_progress_item', 'upsert_progress_item',
             'TASKS_PATH', 'tasks', 'get_json_data', 'upsert_progress_items'),
            ('dags/dags_kord_breach.py', 'fetch_kord_breach', 'upsert_kord_breach',
             'SEASON_PATH', 'season', 'get_season_snapshot', 'upsert_kord_breach_modifiers'),
        ]

    def test_upsert_retries_use_fetched_file_without_refetching(self):
        with tempfile.TemporaryDirectory() as tmp:
            for path, fetch_name, upsert_name, variable, key, api_name, writer_name in self.cases(tmp):
                with self.subTest(path=path):
                    raw = {'raw_api_data': ['한국어', '日本語'], 'nested': {'points': -5}}
                    api = MagicMock(return_value=raw)
                    writer = MagicMock(side_effect=[RuntimeError('temporary DB failure'), None])
                    ti = MagicMock()
                    ns = load_functions(path, {'json': json, 'Path': Path,
                        variable: str(Path(tmp) / key / 'source.json'), api_name: api,
                        writer_name: writer, 'get_current_context': lambda: {'ti': ti}})
                    paths = ns[fetch_name]()
                    source = Path(paths[key])
                    self.assertEqual(json.loads(source.read_text()), raw)
                    self.assertEqual(set(paths), {key})  # Only a file path crosses XCom.
                    ti.xcom_pull.return_value = paths
                    with self.assertRaisesRegex(RuntimeError, 'DB failure'):
                        ns[upsert_name]('platform_db')
                    self.assertTrue(source.exists())
                    ns[upsert_name]('platform_db')
                    api.assert_called_once()
                    self.assertEqual(writer.call_count, 2)
                    self.assertEqual(writer.call_args.args, (raw, 'platform_db'))
                    ti.xcom_pull.assert_called_with(task_ids=fetch_name)
                    ns['remove_json_files']()
                    self.assertFalse(source.exists())
                    ns['remove_json_files']()  # Cleanup also handles fetch failure/missing file.

    def test_fetch_failure_does_not_write_source_or_touch_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            for path, fetch_name, _, variable, key, api_name, writer_name in self.cases(tmp):
                with self.subTest(path=path):
                    source = Path(tmp) / key / 'source.json'
                    writer = MagicMock()
                    ns = load_functions(path, {'json': json, 'Path': Path,
                        variable: str(source), api_name: MagicMock(side_effect=RuntimeError('API failure')),
                        writer_name: writer})
                    with self.assertRaisesRegex(RuntimeError, 'API failure'):
                        ns[fetch_name]()
                    self.assertFalse(source.exists())
                    writer.assert_not_called()
                    ns['remove_json_files']()

    def test_missing_source_file_prevents_database_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            for path, _, upsert_name, variable, key, api_name, writer_name in self.cases(tmp):
                with self.subTest(path=path):
                    ti = MagicMock()
                    ti.xcom_pull.return_value = {key: str(Path(tmp) / 'missing.json')}
                    writer = MagicMock()
                    ns = load_functions(path, {'json': json, 'Path': Path,
                        variable: str(Path(tmp) / 'missing.json'), api_name: MagicMock(),
                        writer_name: writer, 'get_current_context': lambda: {'ti': ti}})
                    with self.assertRaises(FileNotFoundError):
                        ns[upsert_name]('platform_db')
                    writer.assert_not_called()
