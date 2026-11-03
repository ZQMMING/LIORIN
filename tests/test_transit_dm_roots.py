"""Compound roots survive the natal-only clash adjustment."""
import unittest

from engines.common.ge_jie_layer import dm_tier
from engines.common.suiyun_validate import build_compound_facts
from p0_v2.bazi_gate import paipan


class TransitDaymasterRootsTests(unittest.TestCase):
    def test_natal_clash_deducts_only_the_natal_root(self):
        result = paipan('甲寅 庚申 甲子 戊戌')
        pillars, natal = result['pillars'], result['raw_facts']
        self.assertEqual(natal['wuxing_power']['wuxing_power']['木']['ben_n'], 1)
        self.assertEqual(dm_tier(natal['wuxing_power'], '甲', '申', pillars, facts=natal)['ben_n'], 0)
        compound, _, _ = build_compound_facts(pillars, natal, [['甲', '寅'], ['乙', '卯']])
        tier = dm_tier(compound['wuxing_power'], '甲', '申', pillars, facts=compound)
        self.assertEqual(tier['ben_n'], 2)

    def test_new_root_reaches_the_strength_tier(self):
        result = paipan('癸亥 壬戌 乙未 壬午')
        pillars, natal = result['pillars'], result['raw_facts']
        for extra, expected in (([['甲', '寅']], 1), ([['戊', '辰']], 0)):
            compound, _, _ = build_compound_facts(pillars, natal, extra)
            tier = dm_tier(compound['wuxing_power'], '乙', '戌', pillars, facts=compound)
            self.assertEqual(tier['ben_n'], expected)
            self.assertEqual(tier['name'], '旺' if expected else '平')


if __name__ == '__main__':
    unittest.main()
