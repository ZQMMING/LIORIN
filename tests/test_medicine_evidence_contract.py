"""Independent contract checks: source separation, unresolved propagation, no fitted verdict."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from engines.common.medicine_contract import enforce_medicine_contract, function_matrix
from engines.common import suiyun_validate as transit
from p0_v2.bazi_gate import paipan


class MedicineEvidenceContractTests(unittest.TestCase):
    def test_unresolved_disease_cannot_publish_legacy_verdicts(self):
        legacy = {'state': 'YONGYAO_RESOLVED', 'primary_medicine': {'wuxing': '火'},
                  'ji_shen': ['水'], 'xiji_xian': {'xi_wx': ['火'], 'ji_wx': ['水']},
                  'routing': {'winner_shen': '火'}, 'rejected_climate': [{'stem': '癸'}]}
        old = deepcopy(legacy)
        result = enforce_medicine_contract(legacy, {'day_stem': '乙', 'month_branch': '戌'},
                                          [{'bing_id': 'YIN_DUO_MAI_ZI', 'bing_wx': '水'}])
        self.assertEqual(result['state'], 'NOT_EVALUABLE')
        self.assertIsNone(result['primary_medicine'])
        self.assertEqual(result['ji_shen'], [])
        self.assertEqual(result['xiji_xian']['xi_wx'], [])
        self.assertEqual(set(result['xiji_xian']['unknown_wx']), set('木火土金水'))
        self.assertEqual(result['rejected_climate'], [])
        self.assertEqual(result['diagnostic_legacy']['xiji_xian'], old['xiji_xian'])
        self.assertIsNone(result['routing']['winner_shen'])

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

    def test_case_and_transits_do_not_leak_old_luck_verdicts(self):
        with patch.object(transit, 'verdict_step', side_effect=AssertionError('must not arbitrate unresolved chain')):
            r = paipan('癸亥 壬戌 乙未 壬午', gender='女',
                       dayun_list=['癸亥', '丙寅'], liunian_map={0: '甲子'})
        self.assertEqual(r['assessment_status']['dependent_conclusions'], 'NOT_EVALUABLE')
        for step in r['suiyun']['dayun_steps']:
            self.assertIsNone(step['verdict']['level'])
            self.assertEqual(step['verdict']['status'], 'NOT_EVALUABLE')
            if 'liunian' in step:
                self.assertIsNone(step['liunian']['verdict']['level'])
        self.assertEqual(r['yongyao']['xiji_xian']['ji_wx'], [])
        self.assertEqual(r['yongyao']['source_lanes'][0]['candidate_stems'], ['癸'])

    def test_unrelated_rules_are_not_quarantined(self):
        original = {'state': 'YONGYAO_RESOLVED', 'primary_medicine': {'wuxing': '木'}}
        result = enforce_medicine_contract(original, {'day_stem': '庚', 'month_branch': '申'}, [])
        self.assertEqual(result['state'], 'YONGYAO_RESOLVED')
        self.assertEqual(result['primary_medicine'], {'wuxing': '木'})


if __name__ == '__main__':
    unittest.main()
