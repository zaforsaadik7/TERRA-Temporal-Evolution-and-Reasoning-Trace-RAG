"""Generated dictionaries only; no dependency/model/data reads."""
from pathlib import Path
import runpy
import unittest


class SizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measure = staticmethod(runpy.run_path(str(Path(__file__).with_name('check_inventory_sizes.py')))['measure'])

    def row(self, index):
        return {'path':'F:\\fixture\\file_'+str(index)+'.py', 'sha256':'a'*64, 'size_bytes':1}

    def test_small_fixture_fits(self):
        result = self.measure([self.row(0)])
        self.assertLess(result['partial_packet_bytes'],result['packet_limit_bytes'])
        self.assertLess(result['request_pins_only_bytes'],result['child_request_limit_bytes'])

    def test_duplicate_paths_count_once(self):
        self.assertEqual(self.measure([self.row(0), self.row(0)])['unique_files'],1)

    def test_large_synthetic_pin_map_exceeds_request_and_context(self):
        result = self.measure([self.row(index) for index in range(30508)])
        self.assertGreater(result['request_pins_only_bytes'],result['child_request_limit_bytes'])
        self.assertGreater(result['request_pins_only_bytes'],result['child_context_limit_bytes'])


if __name__ == '__main__':
    unittest.main()
