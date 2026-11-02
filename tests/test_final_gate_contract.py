"""Acceptance must reject skipped, absent, crashed and failing checks."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('ziping_final_gate', Path(__file__).with_name('final_gate.py'))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class GateContractTests(unittest.TestCase):
    def run_script(self, source):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'check.py').write_text(source, encoding='utf-8')
            return gate.run_check(root, 'check.py')

    def test_skipped_suite_does_not_pass(self):
        row = self.run_script("print('SKIP frozen test')")
        self.assertEqual(row['status'], 'SKIP')
        self.assertFalse(gate.summarize([row])['passed'])

    def test_failed_process_does_not_pass(self):
        row = self.run_script("raise SystemExit(1)")
        self.assertEqual(row['status'], 'FAIL')

    def test_dependency_block_is_distinct_from_algorithm_failure(self):
        row = self.run_script("print('BLOCKED missing dependency'); raise SystemExit(2)")
        self.assertEqual(row['status'], 'BLOCKED')
        self.assertFalse(gate.summarize([row])['passed'])

    def test_crash_count_does_not_pass_even_with_zero_exit(self):
        row = self.run_script("print('Total crashes: 2')")
        self.assertEqual(row['status'], 'FAIL')

    def test_missing_script_blocks_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            row = gate.run_check(Path(directory), 'absent.py')
        self.assertEqual(row['status'], 'BLOCKED')
        self.assertFalse(gate.summarize([row])['passed'])

    def test_all_pass_required(self):
        row = self.run_script("print('PASS')")
        self.assertTrue(gate.summarize([row])['passed'])
        self.assertFalse(gate.summarize([])['passed'])


if __name__ == '__main__':
    unittest.main()
