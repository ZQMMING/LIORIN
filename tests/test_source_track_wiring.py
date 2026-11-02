"""Source applicability, candidate identity and unranked-state regressions."""
import unittest
from engines.common.yongshen_multi_track import _track_qtbj, _conflict_layer
from p0_v2.bazi_gate import paipan


class SourceTrackWiringTests(unittest.TestCase):
    def test_registered_monthly_rules_are_not_disabled_in_spring_autumn(self):
        for dm in '甲乙丙丁戊己庚辛壬癸':
            for month in '寅卯辰巳午未申酉戌亥子丑':
                with self.subTest(dm=dm, month=month):
                    track = _track_qtbj({}, {'day_stem': dm, 'month_branch': month}, {}, {}, {}, None)
                    self.assertTrue(track['activated'])
                    self.assertEqual(track['urgency'], 'NOT_EVALUATED')

    def test_explicit_unregistered_input_is_not_silently_replaced(self):
        track = _track_qtbj({}, {'day_stem': '乙', 'month_branch': '戌'}, {}, {}, {},
                            {'state': 'NOT_REGISTERED', 'climate_candidates': []})
        self.assertFalse(track['activated'])

    def test_candidate_order_and_polarity_are_preserved(self):
        track = _track_qtbj({'year': ['壬', '子']}, {'day_stem': '甲', 'month_branch': '戌'},
                            {}, {}, {}, {'climate_candidates': [
                                {'stem': '壬', 'order': 2}, {'stem': '癸', 'order': 3}]})
        self.assertEqual([(c['stem_element'], c['priority']) for c in track['candidates']],
                         [('壬', 2), ('癸', 3)])
        self.assertEqual(track['candidates'][0]['visible_positions'], ['year'])
        self.assertEqual(track['candidates'][1]['visible_positions'], [])

    def test_unranked_candidate_array_cannot_manufacture_a_first_choice(self):
        tracks = [dict(track_id='DTS', track_name='体用', activated=True,
                       candidates=[{'element': '木'}], rank_status='UNDETERMINED'),
                  dict(track_id='QTBJ', track_name='调候', activated=True,
                       candidates=[{'element': '水'}])]
        self.assertFalse(_conflict_layer(tracks)['has_conflict'])

    def test_case_keeps_source_specific_water_candidates(self):
        r = paipan('癸亥 壬戌 乙未 壬午', gender='女')['yongshen_multi_track']
        self.assertTrue(r['tracks']['QTBJ']['activated'])
        self.assertEqual(r['tracks']['QTBJ']['candidates'][0]['stem_element'], '癸')
        water = [c for c in r['all_candidates'] if c['element'] == '水']
        self.assertTrue(any(c['track_id'] == 'ZPZQ' for c in water))
        self.assertTrue(any(c['track_id'] == 'QTBJ' and c['stem_element'] == '癸' for c in water))
        self.assertNotIn('DTS', r['conflict']['tracks_involved'])
        self.assertEqual({c['priority'] for c in r['tracks']['DTS']['candidates']}, {1})


if __name__ == '__main__':
    unittest.main()
