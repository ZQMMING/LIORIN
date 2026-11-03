# -*- coding: utf-8 -*-
"""PATCH-171 八格Entry->Candidate Contract
Entry只传候选身份, 绝不升级成Judgment/格成。"""

# 月令本气十神 -> 八格Entry (建禄月劫/食神/七煞/伤官/财/官/印)
_TG_TO_ENTRY = {
    '比肩': '建禄', '劫财': '月劫',
    '食神': '食神格', '七杀': '七煞格', '伤官': '伤官格',
    '正财': '财格', '偏财': '财格',
    '正官': '官格',
    '正印': '印格', '偏印': '印格',
}


def build_candidates(facts):
    """汇总八格Entry为Candidate; state=CANDIDATE, 不判成格/身强弱/用神。"""
    cands = []
    # 月令本气十神 -> Entry (财/官/印/食/杀/伤/建禄月劫)
    mqi_god = facts.get('month_qi_ten_god')
    mqi_map = {
        '比肩': '建禄', '劫财': '月劫', '食神': '食神格', '七杀': '七煞格',
        '伤官': '伤官格', '正财': '财格', '偏财': '财格', '正官': '官格',
        '正印': '印格', '偏印': '印格',
    }
    if mqi_god in mqi_map:
        cands.append(_mk(mqi_map[mqi_god], 'month_qi_ten_god'))
    # 阳刃(五阳, 非普通月令十神)
    yr = facts.get('yangren_entry', {})
    if yr.get('is_entry'):
        cands.append(_mk('阳刃格', 'yangren_entry'))
    return {
        'candidates': cands,
        'boundary': {
            'state_values': ['CANDIDATE', 'BLOCKED', 'UNKNOWN'],
            'forbidden_outputs': ['格成','格败','吉','凶','身强','身弱','旺','弱','用神已定'],
            'note': 'Entry仅候选身份; premise_refs=可查询前提源, 非前提已成立; 成格后续Rule/Judgment',
        },
    }


def _mk(etype, src):
    return {
        'entry_type': etype,
        'state': 'CANDIDATE',
        'source_fact_ids': [src],
        'premise_refs': ['hezuo_relation_premise(可查询, 非已成立)'],
        'boundary': f'{etype}=候选身份, 不判成格',
    }
