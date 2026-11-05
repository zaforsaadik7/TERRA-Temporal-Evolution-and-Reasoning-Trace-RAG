"""Synthetic JSON only; never opens the real benchmark."""
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


class SelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = runpy.run_path(str(Path(__file__).with_name('select_query.py')))

    def test_excluded_values_are_not_json_decoded(self):
        raw = b'[{"id":"B1","category":"B","query":"fixture","target_nodes":["SECRET_SENTINEL",{"a":"x"}],"gold":"SECRET_SENTINEL"}]'
        original = json.loads
        def guarded(fragment, *args, **kwargs):
            self.assertNotIn(b'SECRET_SENTINEL', fragment)
            return original(fragment, *args, **kwargs)
        with patch('json.loads', side_effect=guarded):
            rows = self.module['Projection'](raw).records()
        self.assertEqual(rows, [{'id':'B1','category':'B','query':'fixture'}])

    def test_first_category_b_in_file_order_not_id_sort(self):
        rows = [{'id':'A1','category':'A','query':'fake'},
                {'id':'B9','category':'B_Evolutionary','query':'first'},
                {'id':'B1','category':'B','query':'later'}]
        chosen = self.module['choose'](rows)
        self.assertEqual(chosen['query_id'], 'B9')
        self.assertEqual(chosen['record_index_zero_based'], 1)

    def test_escapes_unicode_and_nested_skipped_values(self):
        value = [{'query_id':'B1','category':'B','query':'quote " and café',
                  'gold':{'nested':[False,None,1.25e-10,{'text':'escaped \\ "'}]}}]
        rows = self.module['Projection'](json.dumps(value).encode()).records()
        self.assertEqual(rows[0]['query'], value[0]['query'])
        self.assertNotIn('gold', rows[0])

    def test_duplicate_and_trailing_content_fail(self):
        for raw in (b'[{"id":1,"id":2}]', b'[] false', b'[{"gold":"\\x"}]'):
            with self.assertRaises(ValueError):
                self.module['Projection'](raw).records()

    def test_missing_or_conflicting_query_identity_fails(self):
        for row in ({'category':'B','query':'x'}, {'id':'B1','query_id':'B2','category':'B','query':'x'},
                    {'id':'B1','category':'B'}):
            with self.assertRaises(ValueError):
                self.module['choose']([row])


if __name__ == '__main__':
    unittest.main()
