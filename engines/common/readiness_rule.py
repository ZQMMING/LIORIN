# -*- coding: utf-8 -*-
"""PATCH-160.11 Structure Comparison Readiness Rule
只判: 日主方↔目标十神方 比较所需已授权结构输入是否齐备。
SATISFIED=输入齐备, 非比较结果成立。不判强弱。"""

_TARGET_CAT = {
    '财': {'正财', '偏财'}, '官': {'正官', '七杀'}, '印': {'正印', '偏印'},
}


def readiness_readiness(facts, target):
    """facts: L0 build输出; target: '财'/'官'/'印'
    返回三态readiness, 缺什么UNKNOWN."""
    needs = []
    # 日主方结构: 区分"字段缺失" vs "已知为无根/无根成员"
    root_facts = facts.get('root_facts')
    root_field_present = root_facts is not None and len(root_facts) > 0
    dm_members = [m for m in facts.get('ten_god_members', [])
                  if m['ten_god'] in {'比肩', '劫财', '正印', '偏印'}]
    # 目标方结构
    cat = _TARGET_CAT.get(target)
    if not cat:
        return {'state': 'UNKNOWN', 'reason': f'未知target:{target}',
                'direction': None, 'missing': ['unknown_target']}
    has_target_root = facts.get('target_root_facts', {}).get(target)
    target_root_present = facts.get('target_root_facts') is not None
    target_members = [m for m in facts.get('ten_god_members', [])
                      if m['ten_god'] in cat]

    missing = []
    # 字段存在即可(哪怕值为False=已知无根), 不是缺失
    if not root_field_present: missing.append('根气字段缺失(非已知无根)')
    if 'month_supports_daymaster' not in facts: missing.append('月令字段缺失')
    if not dm_members: missing.append('日主方成员不可追溯')
    if not target_members: missing.append(f'{target}方成员不可追溯')
    if not target_root_present: missing.append(f'{target}根气字段缺失')
    # 注: 160.10 relations必需项当前阶段不要求, 已从Readiness必需项移除
    if missing:
        return {'state': 'UNKNOWN', 'reason': '比较输入不齐备',
                'direction': None, 'missing': missing}
    return {'state': 'SATISFIED', 'reason': '比较所需已授权结构输入齐备',
            'direction': '日主↔'+target+'结构可比较(仅输入齐备, 非强弱结论)',
            'missing': [],
            'dm_members': len(dm_members), 'target_members': len(target_members)}
