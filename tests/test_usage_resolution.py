"""Cross-source disagreement is conditional, never resolved by a vote."""
import copy
import unittest
from engines.common.usage_resolution import summarize_usage

class UsageResolutionTests(unittest.TestCase):
    def setUp(self):
        self.medicine = {'xiji_xian': {'xi_wx': ['土', '木', '火'], 'ji_wx': ['金', '水'], 'xian_wx': []}}
        self.track = {'tracks': {'QTBJ': {'activated': True, 'track_name': '调候',
                       'candidates': [{'element': '水', 'stem_element': '癸'},
                                      {'element': '金', 'stem_element': '辛'}]}}}

    def test_candidates_opposed_by_legacy_taboo_are_conditional(self):
        r = summarize_usage(self.track, self.medicine)
        self.assertEqual(r['summary']['conditional_wx'], ['金', '水'])
        self.assertEqual(r['summary']['ji_wx'], [])
        self.assertNotIn('水', r['summary']['xi_wx'])
        self.assertEqual(r['conditional_evidence']['水'][0]['stem'], '癸')

    def test_inactive_or_unranked_track_cannot_change_summary(self):
        for change in ({'activated': False}, {'rank_status': 'UNDETERMINED'}):
            track = copy.deepcopy(self.track)
            track['tracks']['QTBJ'].update(change)
            self.assertEqual(summarize_usage(track, self.medicine)['summary']['ji_wx'], ['金', '水'])

    def test_inputs_are_not_modified_and_missing_tracks_are_explicit(self):
        before = copy.deepcopy(self.medicine)
        r = summarize_usage(self.track, self.medicine)
        self.assertEqual(self.medicine, before)
        self.assertEqual(r['sources']['SMTH']['status'], 'NO_INDEPENDENT_USAGE_TRACK')
        self.assertEqual(r['sources']['YHZP']['status'], 'NO_INDEPENDENT_USAGE_TRACK')

    def test_debug_and_production_publish_same_source_classification(self):
        from p0_v2.bazi_gate import paipan
        from engines.production_entry import production_entry, FrozenCanonicalBaziChart
        pillars = dict(year=['癸', '亥'], month=['壬', '戌'], day=['乙', '未'], hour=['壬', '午'])
        production = production_entry(FrozenCanonicalBaziChart(pillars=pillars))
        debug = paipan('癸亥 壬戌 乙未 壬午', gender='女')
        self.assertEqual(production['usage_resolution']['summary'], debug['usage_resolution']['summary'])
        self.assertEqual(production['usage_resolution']['sources']['QTBJ']['candidates'][0]['stem_element'], '癸')

if __name__ == '__main__':
    unittest.main()
