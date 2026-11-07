# -*- coding: utf-8 -*-
"""PATCH-160-B V2 / D8 根支关系叠加结构派生器
把 D2 识别出的日主根支 与 L0 combination_facts(冲合刑害破会) 做结构关联.

只回答一个纯结构问题:
    "日主的某个根支, 是否参与了某类地支关系? 对方/同局是哪些支?"
不回答(作用层, 未授权, HOLD):
    - 冲则根拔 / 衰者拔 / 旺者发 (DTS "旺者冲衰衰者拔" 是作用判断)
    - 合化 / 合走 / 合局改变根气归属 (合化 L0 已 HOLD)
    - 墓库逢冲则开 / 根藏不用
    - 根增强 / 根失效 / 强弱变化

原典: L0 八类关系 Fact 已 CLOSED 且有 provenance; 本派生器只做结构组织, 不新增关系判定.
"""
from typing import Any, Dict, List

BRANCHES = list('子丑寅卯辰巳午未申酉戌亥')
BRANCH_SET = set(BRANCHES)

# combination_facts 键 -> (关系语义, 结构分组, 数据形态)
# group: STRUCK=冲刑害破(对立/伤损类关系, 仅命名, 不判伤); COMBINE=合会类
RELATION_SPEC = {
    'liuchong': ('CLASH', 'STRUCK'),
    'sanxing': ('TRIPLE_PUNISH', 'STRUCK'),
    'self_punishment': ('SELF_PUNISH', 'STRUCK'),
    'liuhai': ('HARM', 'STRUCK'),
    'liupo': ('BREAK', 'STRUCK'),
    'liuhe': ('SIX_COMBINE', 'COMBINE'),
    'sanhe': ('TRIPLE_COMBINE', 'COMBINE'),
    'sanhui': ('DIRECTIONAL_COMBINE', 'COMBINE'),
}


def _branches_in_text(text: str) -> List[str]:
    seen = []
    for ch in text:
        if ch in BRANCH_SET and ch not in seen:
            seen.append(ch)
    return seen


def _relations_touching(branch: str, comb: Dict[str, Any]) -> List[Dict[str, Any]]:
    """返回某支参与的全部关系(结构记录)."""
    out = []
    for key, (sem, group) in RELATION_SPEC.items():
        items = comb.get(key) or []
        for item in items:
            members, raw, positions = [], None, []
            if key == 'self_punishment':
                # {"branch": "辰", "positions": [...]}
                if isinstance(item, dict):
                    if item.get('branch') == branch:
                        members = [item.get('branch')]
                        positions = item.get('positions', [])
                        raw = item.get('branch') + '自刑'
            elif isinstance(item, (list, tuple)) and len(item) == 2 and all(isinstance(x, str) for x in item):
                # 成对: [支, 支]
                a, b = item
                members = [a, b]
                raw = a + b
            elif isinstance(item, str):
                members = _branches_in_text(item)
                raw = item
            if branch in members:
                others = [b for b in members if b != branch]
                out.append({
                    'relation': sem,
                    'group': group,
                    'fact_key': key,
                    'with_branches': others,
                    'positions': positions,
                    'raw': raw,
                })
    return out


def build_root_relations(root_classes: Dict[str, Any], comb: Dict[str, Any]) -> Dict[str, Any]:
    """root_classes = D2 build_root_classes; comb = L0 combination_facts."""
    per_pillar_root = root_classes.get('per_pillar', {})
    detail = {}
    struck, combined = [], []
    for pillar, rc in per_pillar_root.items():
        branch = rc['branch']
        root_class = rc['root_class']
        is_root = root_class != 'NONE'
        rels = _relations_touching(branch, comb) if is_root else []
        if is_root:
            groups = {r['group'] for r in rels}
            if 'STRUCK' in groups:
                struck.append(pillar)
            if 'COMBINE' in groups:
                combined.append(pillar)
        detail[pillar] = {
            'branch': branch,
            'root_class': root_class,
            'is_root': is_root,
            'relations': rels,
        }
    return {
        'generator': 'DaymasterRootRelationOverlay',
        'patch': 'PATCH-160-B-V2-D8',
        'root_branch_relations': detail,
        'struck_root_pillars': struck,
        'combined_root_pillars': combined,
        'judgment_status': 'ROOT_RELATION_STRUCTURE_ONLY',
        'boundary_note': (
            '仅标记日主根支参与何种地支关系; 关系存在≠根失效; '
            '冲则根拔/衰者拔旺者发/合化改根/开库/根增强均为作用层, 未授权 HOLD; '
            'struck/combined 只是结构分组, 不带好坏, 不输出 STRONG/WEAK'
        ),
    }
