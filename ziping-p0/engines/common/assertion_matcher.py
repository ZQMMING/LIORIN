# -*- coding: utf-8 -*-
"""PATCH-132C Assertion Loader / Matcher Core (纯三态)
Assertion subject -> subject_type_router -> Resolver facts[] -> 比对L0 -> ActivatedAssertion
不产 state/use_god/strength; condition古文本阶段不消费.
"""
import json, re
from pathlib import Path
from qtbj_subject_normalizer import normalize_subject

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / 'registries' / 'assertion_subject_type_registry_v1.json'


class Matcher:
    FORBIDDEN = ('climate_state','strength_state','use_god','destiny','fortune_level',
                 'state','fortune','winner','score')

    def __init__(self, route_path=REG):
        self.routes = json.load(open(route_path, encoding='utf-8'))['routes']

    def _route(self, subject):
        for r in self.routes:
            if r['type'] == 'UNKNOWN':
                continue
            pat = r['match']
            try:
                if re.match(pat, subject):
                    return r
            except re.error:
                continue
        return {'type': 'UNKNOWN', 'action': 'ABSTAIN'}

    def _facts_match(self, facts, l0):
        """facts[] vs L0. 任一fact缺事实->ABSTAIN; 矛盾->NOT_MATCHED; 全一致->MATCHED"""
        for f in facts:
            val = l0.get(f['fact'])
            if val is None:
                return 'ABSTAIN', f'missing_l0_fact:{f["fact"]}'
            if f['operator'] == 'eq':
                if val != f['value']:
                    return 'NOT_MATCHED', f'{f["fact"]}={val} != {f["value"]}'
            elif f['operator'] == 'any_of':
                if val not in f['value']:
                    return 'NOT_MATCHED', f'{f["fact"]}={val} not in {f["value"]}'
        return 'MATCHED', 'all facts aligned'

    def match(self, assertion, l0_facts):
        subj = assertion['subject']
        route = self._route(subj)

        if route.get('action') == 'ABSTAIN' or route.get('status') != 'READY':
            return {'status': 'ABSTAIN', 'reason': f"resolver_not_ready:{route.get('type')}"}

        if route['resolver'] == 'qtbj_subject_normalizer':
            r = normalize_subject(subj)
        else:
            return {'status': 'ABSTAIN', 'reason': f"no_resolver_impl:{route['resolver']}"}

        if r['status'] == 'ABSTAIN':
            return {'status': 'ABSTAIN', 'reason': r['reason']}

        status, why = self._facts_match(r['facts'], l0_facts)
        out = {'status': status, 'reason': why}
        if status == 'MATCHED':
            # ActivatedAssertion: 仅允许字段, 禁state
            aa = {
                'assertion_id': assertion['assertion_id'],
                'source_evidence': assertion['source_evidence'],
                'predicate': assertion['predicate'],
                'object': assertion['object'],
                'condition': assertion.get('condition', {}),
                'matched_facts': r['facts'],
            }
            for k in self.FORBIDDEN:
                assert k not in aa, f'ActivatedAssertion含越权字段:{k}'
            out['activated_assertion'] = aa
        return out


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    m = Matcher()
    # GC-001: 乙木戌月
    test_a = {'subject': '乙木九月', 'assertion_id': 'QTBJ-GC001', 'source_evidence': ['QTBJ-022-001'], 'predicate': 'requires', 'object': '癸水润'}
    l0 = {'day_stem': '乙', 'month_branch': '戌'}
    print('GC-001 乙木戌月:', json.dumps(m.match(test_a, l0), ensure_ascii=False))
    # 反例: 乙木寅月(应NOT_MATCHED)
    print('反例 乙木寅月:', json.dumps(m.match(test_a, {'day_stem': '乙', 'month_branch': '寅'}), ensure_ascii=False))
    # 缺事实
    print('缺month:', json.dumps(m.match(test_a, {'day_stem': '乙'}), ensure_ascii=False))
    # ABSTAIN resolver
    test_b = {'subject': '五行', 'assertion_id': 'QTBJ-T', 'source_evidence': [], 'predicate': 'needs', 'object': '和'}
    print('五行:', json.dumps(m.match(test_b, l0), ensure_ascii=False))
