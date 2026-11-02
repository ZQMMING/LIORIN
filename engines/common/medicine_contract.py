"""Evidence boundary for medicine output; relations are not unconditional efficacy.

No numeric strength model, new classic slice, or single universal yongshen is introduced.
The original-rule candidates and legacy calculations remain separate for review.
"""
from copy import deepcopy

STEMS = '甲乙丙丁戊己庚辛壬癸'
WX = dict(zip(STEMS, '木木火火土土金金水水'))
SHENG = dict(zip('木火土金水', '火土金水木'))
KE = dict(zip('木土水火金', '土水火金木'))
PZZQ_SOURCE = 'registries/source/raw/PZZQ_子平真诠_沈孝瞻原文.md'
QTBJ_SOURCE = 'registries/source/raw/QTBJ_穷通宝鉴_原文.md'


def function_matrix(facts, disease_wx):
    """Enumerate mechanics per stem, without assuming net benefit or equivalence."""
    dm = WX.get(facts.get('day_stem'))
    out = []
    for stem in STEMS:
        wx = WX[stem]
        effects = []
        if wx == dm:
            effects.append('同类帮身')
        if SHENG.get(wx) == dm:
            effects.append('生身')
        if SHENG.get(dm) == wx:
            effects.append('泄身')
        if KE.get(dm) == wx:
            effects.append('日主克财需承载')
        if KE.get(wx) == dm:
            effects.append('克身')
        if disease_wx:
            if wx == disease_wx:
                effects.append('同病五行_不等于助病成立')
            if KE.get(wx) == disease_wx:
                effects.append('克病五行_不等于制病有效')
            if SHENG.get(disease_wx) == wx:
                effects.append('泄病五行_不等于承接有效')
            if SHENG.get(wx) == disease_wx:
                effects.append('生病五行_不等于最终为忌')
        out.append({'stem': stem, 'wuxing': wx, 'effects': effects,
                    'efficacy': 'NOT_EVALUABLE',
                    'required': ['病机成立', '作用路径有效', '日主承载', '合冲制化及气候兼容']})
    return out


def enforce_medicine_contract(result, facts, bing_list):
    """Quarantine unresolved rules at the shared resolver used by all entry points."""
    issues = []
    disease = next((b for b in bing_list if b.get('bing_id') == 'YIN_DUO_MAI_ZI'), None)
    if disease:
        issues.append({'code': 'YIN_EXCESS_CONDITION_NOT_VALIDATED',
                       'rule_status': 'ENGINE_DEFINED',
                       'reason': '透根数量阈值及无重根不足以独立证明印已构成损害',
                       'required': ['印的有效生扶与实际损害判据', '位置及制化影响'],
                       'source_boundary': {'path': PZZQ_SOURCE, 'lines': [1127, 1130],
                                           'authority': 'LATER_COMMENTARY',
                                           'excluded_as': 'SHEN_ORIGINAL'}})
    if result.get('state') == 'NOT_EVALUABLE':
        issues.append({'code': 'CLIMATE_SELECTION_UNRESOLVED',
                       'required': (result.get('selection_trace') or {}).get('missing_conditions', [])})
    lanes = []
    # Source-scoped rule: original text at L2076, not the adjacent Xu commentary.
    # This is an independent candidate, not a universal verdict or 癸==壬 substitution.
    if facts.get('day_stem') == '乙' and facts.get('month_branch') == '戌':
        lanes.append({'source': 'QTBJ', 'authority': 'ORIGINAL_TEXT',
                      'path': QTBJ_SOURCE, 'line': 2076,
                      'condition': {'day_stem': '乙', 'month_branch': '戌'},
                      'candidate_stems': ['癸'], 'status': 'SOURCE_RULE_MATCHED',
                      'scope': '癸水滋养候选_非全部水无条件为喜',
                      'efficacy': 'NOT_EVALUABLE'})
    result['source_lanes'] = lanes
    if not issues:
        return result
    # Preserve all old values in a diagnostic namespace, never in final verdict fields.
    keys = ('primary_medicine', 'auxiliary_medicine', 'ji_shen', 'xiji_xian',
            'rejected_climate', 'routing')
    result['diagnostic_legacy'] = {k: deepcopy(result.get(k)) for k in keys}
    result['assessment'] = {'status': 'NOT_EVALUABLE', 'issues': issues,
                            'blocked_outputs': ['主用神', '喜忌', '岁运吉凶']}
    result['state'] = 'NOT_EVALUABLE'
    result['primary_medicine'] = None
    result['auxiliary_medicine'] = []
    result['ji_shen'] = []
    result['rejected_climate'] = []
    result['xiji_xian'] = {'status': 'NOT_EVALUABLE', 'xi_wx': [], 'ji_wx': [],
                           'xian_wx': [], 'unknown_wx': ['木', '火', '土', '金', '水'],
                           'basis': '规则未决，未知不归闲神；原计算仅保留诊断字段'}
    route = deepcopy(result.get('routing') or {})
    route.update(status='NOT_EVALUABLE', winner_route='', winner_shen=None,
                 winner_basis='规则成立及效用条件未决，未裁决',
                 xiji_xian=result['xiji_xian'])
    result['routing'] = route
    trace = result.get('selection_trace') or {}
    trace.update(selected=None, review_status='NOT_EVALUABLE')
    result['selection_trace'] = trace
    result['function_matrix'] = function_matrix(facts, (disease or {}).get('bing_wx'))
    return result


def unresolved_transit(base_medicine, step_medicine=None):
    """A final transit verdict cannot consume an unresolved natal or transit chain."""
    return any(x and x.get('state') == 'NOT_EVALUABLE'
               for x in (base_medicine, step_medicine))


def unknown_verdict():
    return {'status': 'NOT_EVALUABLE', 'level': None, 'shorthand': '未决',
            'direction': None, 'reason': '原局或复合局病药未决，禁止输出确定岁运吉凶'}
