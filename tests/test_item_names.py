import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
from custom_module import tarkov_json_api as api
from custom_module.item_task_func import v3_item_row_process
from custom_module.queries.item import INSERT_ITEMS


class ItemNameTests(unittest.TestCase):
    def test_only_valid_translated_names_are_extracted_by_id(self):
        responses = [
            {'data': {'items': {
                'a': {'id': 'a', 'name': 'name-a', 'description': 'desc-a'},
                'b': {'id': 'b', 'name': 'name-b'},
                'c': {'id': 'c', 'name': 'name-c'},
            }}},
            {'data': {'name-a': '한글 이름', 'name-b': ' ', 'desc-a': '설명'}},
            {'data': {'name-a': '日本語名', 'name-b': None}},
        ]
        with patch.object(api, '_request_json', side_effect=responses) as request:
            names = api.get_item_names()
        self.assertEqual(names, {'ko': {'a': {'name': '한글 이름'}}, 'ja': {'a': {'name': '日本語名'}}})
        self.assertEqual([c.args[0] for c in request.call_args_list], ['regular/items', 'regular/items_ko', 'regular/items_ja'])
        row = v3_item_row_process({'id': 'a', 'name': 'English', 'weight': 2}, names['ko']['a'], names['ja']['a'])
        self.assertEqual(row[3:6], ('English', '한글 이름', '日本語名'))
        self.assertEqual(row[7], 2)
        self.assertIn("name_ko=COALESCE(NULLIF(excluded.name_ko, ''), items.name_ko)", INSERT_ITEMS)
        self.assertIn("name_ja=COALESCE(NULLIF(excluded.name_ja, ''), items.name_ja)", INSERT_ITEMS)

    def test_name_fetch_failure_does_not_publish_partial_files(self):
        path = Path(__file__).resolve().parents[1] / 'dags/v3_dags_item.py'
        tree = ast.parse(path.read_text())
        fn = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'fetch_item')
        namespace = {'get_items': Mock(return_value=[]), 'get_item_names': Mock(side_effect=RuntimeError('unavailable')), 'open': Mock()}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), 'exec'), namespace)
        with self.assertRaises(RuntimeError):
            namespace['fetch_item']()
        namespace['open'].assert_not_called()


if __name__ == '__main__':
    unittest.main()
