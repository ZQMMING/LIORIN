# -*- coding: utf-8 -*-
"""P160 QTBJ 调候干盘中存在性投影 · 第五刀(只读对照, 不判调候得力/成败)

承接刚封板的 QTBJ 调候十干全表(_CLIMATE_TABLE):
  前一刀只回答「甲日寅月应取何干」(干名序列);
  本刀回答「这个盘里, 应取的干到底出现在哪里」。

只做(纯结构对照, 不新增判断):
  对 build_climate_candidates 输出的每个调候干, 只读聚合:
    - TRANSPARENT: 该调出干名出现在四柱天干(type=stem)
    - HIDDEN:      该调出干名仅出现在地支藏干(type=hidden)
    - ABSENT:      四柱天干/藏干均无此干
  并列保留原表干序; 不排序重排。

铁律(用户裁决):
  - 只读 ten_god_members 的 stem 名, 不重算十神/藏干/月令;
  - TRANSPARENT/HIDDEN 只是「干出现在哪」的位置事实, 不是力度评分;
  - 不判「调候得力/无力/无效」; 不判「无丙=不吉/寒」; 不判调候成败;
  - 不输出 winner/selected/final/use; 不判身强弱; 不接 production_entry;
  - 透干/藏干为位置事实分层, 非加权计数(不加 power/score)。

原典依据(仅授权「透干/出干/藏干」位置事实, 不授权成败):
  QTBJ 各月原文通篇以「丙出干/癸透/丙藏支」论调候干的出现位置;
  位置存在 ≠ 调候成立。成败/得力属 EFFECT, 本刀不授权。
"""
from typing import Any, Dict, List
from engines.common.qtbj_climate_candidates import build_climate_candidates

PRESENT_TRANSPARENT = 'TRANSPARENT'   # 出现在四柱天干
PRESENT_HIDDEN = 'HIDDEN'             # 仅出现在地支藏干
PRESENT_ABSENT = 'ABSENT'             # 四柱天干/藏干均无

# 位置事实证据: 调候干「透干/出干/藏支」是 QTBJ 各月原文反复出现的位置语义;
# 仅授权位置存在, 不授权调候成败/得力。
_EVIDENCE = ['QTBJ-PRESENCE-LOCATION']


def _collect_stem_locations(facts: Dict[str, Any]) -> Dict[str, Dict[str, List[str]]]:
    """聚合每个天干名在四柱的出现位置。只读 ten_god_members, 不重算。"""
    locs: Dict[str, Dict[str, List[str]]] = {}
    for m in facts.get('ten_god_members', []):
        stem = m.get('stem')
        if not stem:
            continue
        slot = locs.setdefault(stem, {'transparent': [], 'hidden': []})
        pillar = m.get('pillar', '?')
        if m.get('type') == 'stem':
            if pillar not in slot['transparent']:
                slot['transparent'].append(pillar)
        else:
            if pillar not in slot['hidden']:
                slot['hidden'].append(pillar)
    return locs


def build_climate_presence(facts: Dict[str, Any]) -> Dict[str, Any]:
    """调候干序列 × 盘中存在位置的只读对照投影。"""
    base = build_climate_candidates(facts)
    locs = _collect_stem_locations(facts)

    candidates: List[Dict[str, Any]] = []
    for c in base.get('climate_candidates', []):
        stem = c.get('stem')
        loc = locs.get(stem, {'transparent': [], 'hidden': []})
        if loc['transparent']:
            status = PRESENT_TRANSPARENT
        elif loc['hidden']:
            status = PRESENT_HIDDEN
        else:
            status = PRESENT_ABSENT
        candidates.append({
            'candidate_id': c.get('candidate_id'),
            'stem': stem,
            'order': c.get('order'),
            'present_status': status,                       # 位置事实, 非力度
            'transparent_pillars': list(loc['transparent']),
            'hidden_pillars': list(loc['hidden']),
            'base_evidence_refs': list(c.get('evidence_refs', [])),
            'status': 'CANDIDATE',
        })

    base_refs = list(base.get('evidence_refs', []))

    return {
        'module': 'QTBJ_CLIMATE_PRESENCE',
        'patch': 'P160-QTBJ-PRESENCE-5',
        'namespace': 'QTBJ.climate_use',
        'namespace_type': 'climate',
        'month_branch': facts.get('month_branch'),
        'day_stem': facts.get('day_stem'),
        'climate_presence_candidates': candidates,
        'candidate_count': len(candidates),
        'base_state': base.get('state'),
        'judgment_status': 'CLIMATE_PRESENCE_ONLY',
        'boundary_note': (
            '仅对照「调候应取干」与「盘中该干出现位置」(透干/藏支/全无); '
            'TRANSPARENT/HIDDEN 是位置事实分层非力度评分, 不判调候得力/无力/无效; '
            '不判无X=不吉/寒, 不判调候成败, 不输出 selected/final; 并列保留原表干序; '
            '不判身强弱; 不接 production_entry'
        ),
        'evidence_refs': base_refs + _EVIDENCE,
    }
