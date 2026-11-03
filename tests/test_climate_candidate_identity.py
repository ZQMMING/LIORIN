"""A classical candidate stem must not be replaced by its same-element peer."""
import unittest
from engines.common.tiaohou_rank import _tiaohou_primary_rank

class CandidateIdentityTests(unittest.TestCase):
    def test_same_element_other_stem_cannot_prove_candidate_visible(self):
        climate = {'month_branch': '戌', 'climate_candidates': [
            {'stem': '丙', 'order': 1, 'evidence_refs': ['test-only']}]}
        base = {'year': ('丁', '子'), 'month': ('戊', '戌'),
                'day': ('乙', '卯'), 'hour': ('癸', '丑')}
        result = _tiaohou_primary_rank(climate, '水', '木', base)
        self.assertEqual(result['rank'], 'ABSTAIN')
        self.assertIn('EXACT_STEM_EFFECTIVENESS', result['missing_conditions'])
        base['year'] = ('丙', '子')
        self.assertEqual(_tiaohou_primary_rank(climate, '水', '木', base)['rank'], 'PROMOTE')

    def test_unknown_first_candidate_does_not_hide_valid_same_element_second(self):
        climate = {'month_branch': '丑', 'climate_candidates': [
            {'stem': '丙', 'order': 1}, {'stem': '丁', 'order': 2}]}
        pillars = {'year': ('丁', '酉'), 'month': ('己', '丑'),
                   'day': ('庚', '申'), 'hour': ('甲', '子')}
        result = _tiaohou_primary_rank(climate, '土', '金', pillars)
        self.assertEqual(result['rank'], 'PROMOTE')
        self.assertIn('丁', result['reason'][0])

if __name__ == '__main__':
    unittest.main()
