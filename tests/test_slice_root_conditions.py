"""Independent root condition truth table: no numeric threshold changes."""
import unittest
from engines.common.slice_conditions import _dm_no_heavy, eval_slice_conditions

class RootPredicateTests(unittest.TestCase):
    def test_enum_family_and_unknown(self):
        for root in ('HEAVY', 'HEAVY_LU', 'HEAVY_BEN'):
            self.assertFalse(_dm_no_heavy({'root_weight_class_facts': {'year': {'class': root}}}))
        for root in ('LIGHT', 'LIGHT_YU_QI', 'SPECIAL_LONGSHENG_YIN', 'NONE'):
            self.assertTrue(_dm_no_heavy({'root_weight_class_facts': {'year': {'class': root}}}))
        for facts in ({}, {'root_weight_class_facts': {}},
                      {'root_weight_class_facts': {'year': {'class': 'UNREGISTERED'}}}):
            self.assertIsNone(_dm_no_heavy(facts))

    def test_disease_conditions_cannot_match_known_heavy_root(self):
        for disease in ('CAI_DUO_SHEN_RUO', 'SHA_ZHONG_SHEN_QING', 'YIN_DUO_MAI_ZI'):
            facts = {'day_stem': '乙', 'daymaster_element': '木', 'month_qi_element': '水',
                     'root_weight_class_facts': {'year': {'class': 'HEAVY_LU'}}}
            self.assertEqual(eval_slice_conditions(disease, '水', facts)['state'], 'NOT_MATCHED')

    def test_missing_roots_abstain_instead_of_proving_weakness(self):
        facts = {'day_stem': '乙', 'daymaster_element': '木', 'month_qi_element': '水'}
        self.assertEqual(eval_slice_conditions('YIN_DUO_MAI_ZI', '水', facts)['state'], 'ABSTAIN')

if __name__ == '__main__':
    unittest.main()
