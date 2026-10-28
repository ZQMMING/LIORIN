# -*- coding: utf-8 -*-
"""PATCH-160-B V2 / D6 两端构成投影 (Two-Side Composition Projection)

DTS 众寡论明言 "须分日主与四柱两端而论"; 本派生器只做原著框架里的纯结构投影:
把已建维度(D2 根 / D13 透藏 / D8 根支关系 / D3-D5 十神) 归到两个阵营,
列出每端有哪些成员及其结构态.

严格不做(DTS "强众敌寡, 势在去其寡; 强寡敌众, 势在成乎众" 的 "势/去取" 层):
- 不数成员个数, 不比谁多谁少(众/寡)
- 不判哪端 "成势 / 得势"
- 不判胜负 / 去取 / 从某
- 不输出 STRONG/WEAK
"present" 仅布尔存在性; 柱位列表仅供审计, 不产生 len 比较结论.

成势判据(得令/成局/有源/众寡)即便结构可见, 其 "势" 的结论仍 HOLD,
须未来 DTS Query 单独取得授权, 本投影不代为裁决.
"""
from typing import Any, Dict

DAYMASTER_SIDE = 'DAYMASTER_SIDE'   # 日主 + 根 + 同党(比劫) + 生我(印)
OPPOSING_SIDE = 'OPPOSING_SIDE'     # 我生(食伤) + 我克(财) + 克我(官杀)

# 阵营成员(与 160-A / D13 五大类对齐)
SIDE_MEMBERS = {
    DAYMASTER_SIDE: ['BIJIE', 'YIN'],
    OPPOSING_SIDE: ['SHISHANG', 'CAI', 'GUANSHA'],
}


def _shen_member(tou_cang: Dict[str, Any], gname: str) -> Dict[str, Any]:
    g = (tou_cang or {}).get('groups', {}).get(gname, {})
    tou = bool(g.get('tou'))
    cang = bool(g.get('cang'))
    return {
        'member': gname,
        'present': tou or cang,
        'tou': tou,
        'cang': cang,
        'tou_cang_state': g.get('state'),
        'stem_pillars': g.get('stem_pillars', []),
        'hidden_pillars': g.get('hidden_pillars', []),
    }


def build_two_side(root_classes: Dict[str, Any], tou_cang: Dict[str, Any],
                   root_relations: Dict[str, Any] = None) -> Dict[str, Any]:
    # 日主端: 根结构
    root_block = {
        'member': 'ROOT',
        'present': bool((root_classes or {}).get('has_root')),
        'root_pillars': (root_classes or {}).get('root_pillars', []),
        'root_class_detail': {
            k: v['root_class'] for k, v in (root_classes or {}).get('per_pillar', {}).items()
        } if root_classes else {},
        'struck_root_pillars': (root_relations or {}).get('struck_root_pillars', []),
        'combined_root_pillars': (root_relations or {}).get('combined_root_pillars', []),
    }

    sides = {}
    for side, members in SIDE_MEMBERS.items():
        block = {'members': [_shen_member(tou_cang, g) for g in members]}
        sides[side] = block
    sides[DAYMASTER_SIDE]['root'] = root_block

    return {
        'generator': 'DaymasterTwoSideComposition',
        'patch': 'PATCH-160-B-V2-D6',
        'sides': sides,
        'judgment_status': 'TWO_SIDE_COMPOSITION_ONLY_NO_SHISHI',
        'boundary_note': (
            '仅按 DTS 分两端列出成员结构态; 不计数/不比众寡/不判成势胜负去取; '
            '"势在去其寡/成乎众" 属去取用神层, HOLD; 不输出 STRONG/WEAK'
        ),
    }
