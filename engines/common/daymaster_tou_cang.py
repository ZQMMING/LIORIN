# -*- coding: utf-8 -*-
"""PATCH-160-B V2 / D13 透藏关系派生器
只消费 L0 ten_god_members(确定性 Fact), 不重算, 不改 L0.

原典授权(仅结构层):
- "干以通根为美, 支以透出为贵" -> 透/藏是客观结构
- PZZQ "透干会支, 别取财官煞食为用" -> 透干会支是结构; "为用"属用神层, 不进本层

四态(纯结构, 离散, 无数值):
- TOU_CANG_BOTH : 天干透出 且 地支藏有 (透干会支/通根)
- TOU_ONLY      : 透于天干而支中不藏 (只记"透而不藏"结构; 不判"虚浮无力")
- CANG_ONLY     : 支中藏而天干不透 (只记结构; 不判"不得用")
- ABSENT        : 天干地支俱不现

禁: 有力/无力/旺衰/强弱/美贵吉凶/为用/score/weight.
"""
from typing import Any, Dict, List

# 五大大类(与 160-A 分组对齐), 每类含正偏两神
GROUPS = {
    'BIJIE': {'比肩', '劫财'},
    'YIN': {'正印', '偏印'},
    'SHISHANG': {'食神', '伤官'},
    'CAI': {'正财', '偏财'},
    'GUANSHA': {'正官', '七杀'},
}

TOU_CANG_BOTH = 'TOU_CANG_BOTH'
TOU_ONLY = 'TOU_ONLY'
CANG_ONLY = 'CANG_ONLY'
ABSENT = 'ABSENT'


def _group_state(members: List[Dict[str, Any]], tg_set: set) -> Dict[str, Any]:
    stem_pillars = []   # 天干透出的柱
    hidden_pillars = []  # 地支藏有的柱
    stem_shen = set()
    hidden_shen = set()
    for m in members:
        if m['ten_god'] not in tg_set:
            continue
        if m['type'] == 'stem':
            stem_pillars.append(m['pillar'])
            stem_shen.add(m['ten_god'])
        elif m['type'] == 'hidden':
            hidden_pillars.append(f"{m['pillar']}:{m['branch']}({m.get('qi_position')})")
            hidden_shen.add(m['ten_god'])
    tou = len(stem_pillars) > 0
    cang = len(hidden_pillars) > 0
    if tou and cang:
        state = TOU_CANG_BOTH
    elif tou:
        state = TOU_ONLY
    elif cang:
        state = CANG_ONLY
    else:
        state = ABSENT
    return {
        'tou': tou,
        'cang': cang,
        'state': state,
        'stem_pillars': stem_pillars,
        'hidden_pillars': hidden_pillars,
        'stem_ten_gods': sorted(stem_shen),
        'hidden_ten_gods': sorted(hidden_shen),
    }


def build_tou_cang(facts: Dict[str, Any]) -> Dict[str, Any]:
    """输入 L0 build() 输出(取 ten_god_members). 输出逐大类透藏四态."""
    members = facts.get('ten_god_members', [])
    groups = {gname: _group_state(members, tg) for gname, tg in GROUPS.items()}
    return {
        'generator': 'DaymasterTouCangStructure',
        'patch': 'PATCH-160-B-V2-D13',
        'groups': groups,
        'judgment_status': 'TOU_CANG_STRUCTURE_ONLY',
        'boundary_note': (
            '透藏四态仅为客观结构; 不判有力/无力/虚浮/旺衰/强弱/美贵/为用; '
            'TOU_ONLY 不等于虚浮无力, CANG_ONLY 不等于不得用'
        ),
    }
