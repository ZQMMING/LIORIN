"""Fact presence and decision provenance, without prescribing a correct medicine."""
import unittest
from p0_v2.bazi_gate import paipan, _liu_qin_of


class CasePresenceTraceTests(unittest.TestCase):
    def test_hidden_relatives_and_self_exclusion(self):
        r = paipan('癸亥 壬戌 乙未 壬午', gender='女')
        items = {x['symbol']: x for x in r['liu_qin']['items']}
        for relative in ('父', '夫星', '子女'):
            self.assertTrue(items[relative]['hidden_present'])
            self.assertFalse(items[relative]['visible_present'])
            self.assertTrue(items[relative]['present'])
        self.assertFalse(any(x['pos'] == 'day' and x['source'] == 'VISIBLE_STEM'
                             for x in items['兄弟']['positions']))
        trace = r['yongshen_decision']['selection_trace']
        self.assertEqual(trace['selected'], r['yongyao']['primary_detail'])
        self.assertFalse(trace['climate_applied'])
        self.assertIsNone(trace['selected'])
        self.assertEqual(r['yongyao']['state'], 'NOT_EVALUABLE')
        self.assertTrue(trace['missing_conditions'])
        self.assertNotIn('无硬情形无病', r['yongshen_decision']['winner_basis'])

    def test_month_alone_cannot_promote_food_output(self):
        from engines.common.tiaohou_rank import _hanzao_shishang_rank
        for month in '子丑寅卯辰巳午未申酉戌亥':
            with self.subTest(month=month):
                rank = _hanzao_shishang_rank({}, '木', month, {})
                self.assertEqual(rank['rank'], 'ABSTAIN')

    def test_authoritative_empty_hidden_list_is_not_repopulated(self):
        pillars = dict(year=('癸', '亥'), month=('壬', '戌'),
                       day=('乙', '未'), hour=('壬', '午'))
        facts = {'day_stem': '乙', 'hidden_stems': {p: [] for p in pillars}}
        items = _liu_qin_of(facts, pillars, '女')['items']
        self.assertFalse(next(x for x in items if x['symbol'] == '兄弟')['present'])


if __name__ == '__main__':
    unittest.main()
