"""Transit changes must update consumed structural predicates and hidden members."""
import copy
import unittest
from engines.common.compound_queries import evaluate_compound_queries
from engines.common.suiyun_validate import build_compound_facts, run_chain_on
from engines.common.l0_fact_builder import HIDDEN
from p0_v2.bazi_gate import paipan


def state(queries, suffix):
    return next(q['state'] for q in queries if q['query_id'].endswith(suffix))


class CompoundQueryRefreshTests(unittest.TestCase):
    def setUp(self):
        self.r = paipan('戊申 己酉 甲申 戊午')
        self.facts = self.r['raw_facts']
        self.pillars = self.r['pillars']

    def test_new_root_reverses_no_root_query_instead_of_reusing_natal_answer(self):
        before = evaluate_compound_queries(self.facts)
        self.assertEqual(state(before, 'CAIDUO-SHENRUAN'), 'SUPPORTED')
        step = run_chain_on(self.pillars, self.facts, [['甲', '寅']], before)
        self.assertEqual(state(step['queries'], 'CAIDUO-SHENRUAN'), 'NOT_SUPPORTED')
        self.assertEqual(state(before, 'CAIDUO-SHENRUAN'), 'SUPPORTED')
        self.assertTrue(all(q['evaluation_scope'] == 'COMPOUND_STRUCTURE' for q in step['queries']))

    def test_transit_hidden_stems_keep_position_and_polarity(self):
        compound, _, _ = build_compound_facts(self.pillars, self.facts, [['癸', '亥']])
        hidden = [m for m in compound['ten_god_members'] if m['pillar'] == 't0' and m['type'] == 'hidden']
        self.assertEqual([m['stem'] for m in hidden], HIDDEN['亥'])
        self.assertEqual([m['hidden_index'] for m in hidden], list(range(len(HIDDEN['亥']))))
        self.assertTrue(all(m['ten_god'] for m in hidden))

    def test_compound_construction_does_not_mutate_natal_facts(self):
        before = copy.deepcopy(self.facts)
        build_compound_facts(self.pillars, self.facts, [['甲', '寅'], ['丙', '午']])
        self.assertEqual(self.facts, before)

    def test_no_transit_preserves_consumed_structural_query_results(self):
        before = evaluate_compound_queries(self.facts)
        step = run_chain_on(self.pillars, self.facts, [], before)
        self.assertEqual([(q['query_id'], q['state']) for q in before],
                         [(q['query_id'], q['state']) for q in step['queries']])

if __name__ == '__main__':
    unittest.main()
