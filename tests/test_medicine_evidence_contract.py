"""Independent contract checks: source separation, unresolved propagation, no fitted verdict."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from engines.common.medicine_contract import enforce_medicine_contract, function_matrix
from engines.common import suiyun_validate as transit
from p0_v2.bazi_gate import paipan


class MedicineEvidenceContractTests(unittest.TestCase):
    def test_provisional_outputs_preserve_computation_and_source_conflict(self):
        result = enforce_medicine_contract(
            {'state': 'YONGYAO_RESOLVED', 'primary_medicine': {'wuxing': '土'},
             'ji_shen': ['水'], 'xiji_xian': {'xi_wx': ['土'], 'ji_wx': ['水']}},
            {'day_stem': '乙', 'month_branch': '戌'},
            [{'bing_id': 'YIN_DUO_MAI_ZI', 'bing_wx': '水'}])
        self.assertEqual(result['state'], 'PROVISIONAL')
        self.assertEqual(result['primary_medicine']['wuxing'], '土')
        self.assertEqual(result['source_conflicts'][0]['stem'], '癸')
        self.assertEqual(result['xiji_xian']['status'], 'PROVISIONAL')

    def test_qtbj_rule_is_day_month_scoped_and_stem_specific(self):
        for dm in '甲乙丙丁戊己庚辛壬癸':
            for month in '子丑寅卯辰巳午未申酉戌亥':
                result = enforce_medicine_contract({'state': 'NO_BING'},
                                                   {'day_stem': dm, 'month_branch': month}, [])
                matched = result['source_lanes']
                self.assertEqual(bool(matched), dm == '乙' and month == '戌')
                if matched:
                    self.assertEqual(matched[0]['candidate_stems'], ['癸'])
                    self.assertEqual(matched[0]['authority'], 'ORIGINAL_TEXT')

    def test_function_mechanics_do_not_assert_net_benefit(self):
        rows = function_matrix({'day_stem': '乙'}, '水')
        self.assertEqual(len(rows), 10)
        rows = {x['stem']: x for x in rows}
        self.assertIn('泄身', rows['丙']['effects'])
        self.assertIn('日主克财需承载', rows['戊']['effects'])
        self.assertIn('克病五行_不等于制病有效', rows['戊']['effects'])
        self.assertEqual(rows['壬']['efficacy'], 'NOT_EVALUABLE')
        self.assertNotEqual(rows['癸']['stem'], rows['壬']['stem'])

    def test_case_and_transits_preserve_computation_with_provisional_status(self):
        r = paipan('癸亥 壬戌 乙未 壬午', gender='女',
                   dayun_list=['癸亥', '丙寅'], liunian_map={0: '甲子'})
        self.assertEqual(r['assessment_status']['dependent_conclusions'], 'PROVISIONAL')
        for step in r['suiyun']['dayun_steps']:
            self.assertIsNotNone(step['verdict']['level'])
            self.assertEqual(step['verdict']['status'], 'PROVISIONAL')
            if 'liunian' in step:
                self.assertEqual(step['liunian']['verdict']['status'], 'PROVISIONAL')
        self.assertEqual(r['yongyao']['source_lanes'][0]['candidate_stems'], ['癸'])

    def test_unrelated_rules_are_not_quarantined(self):
        original = {'state': 'YONGYAO_RESOLVED', 'primary_medicine': {'wuxing': '木'}}
        result = enforce_medicine_contract(original, {'day_stem': '庚', 'month_branch': '申'}, [])
        self.assertEqual(result['state'], 'YONGYAO_RESOLVED')
        self.assertEqual(result['primary_medicine'], {'wuxing': '木'})


if __name__ == '__main__':
    unittest.main()
