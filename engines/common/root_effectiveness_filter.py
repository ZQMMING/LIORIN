# -*- coding: utf-8 -*-
"""根有效性过滤层: 考虑冲合对根的影响.
- 多冲一: 根支被多个冲支冲, 根失效(旺者冲衰衰者拔)
- 合去: 根支被六合化神成功且化神非日主同类, 根失效
- 三合/三会: 根支参与合局且合神非日主同类, 根气被合走
只过滤无效根, 不评分不加权. 离散枚举."""
from typing import Dict, List, Any

# 六冲映射
# ★ ARCHIVED_FALLBACK (2026-10-06): 六冲/三合/三会存在性已改消费 combination_facts
#   (排盘引擎权威源), 本表仅作兜底, 不再主链计算. 备份: _legacy_relation_tables.
LIUCHONG = {
    '子': '午', '午': '子',
    '丑': '未', '未': '丑',
    '寅': '申', '申': '寅',
    '卯': '酉', '酉': '卯',
    '辰': '戌', '戌': '辰',
    '巳': '亥', '亥': '巳',
}

# 三合局
SANHE = {
    '申子辰': '水', '亥卯未': '木', '寅午戌': '火', '巳酉丑': '金',
}

# 三会方
SANHUI = {
    '寅卯辰': '木', '巳午未': '火', '申酉戌': '金', '亥子丑': '水',
}

WUXING = {
    '甲': '木', '乙': '木',
    '丙': '火', '丁': '火',
    '戊': '土', '己': '土',
    '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}


def filter_root_effectiveness(
    root_classes: Dict[str, Any],
    combination_facts: Dict[str, Any],
    pillars: Dict[str, list],
    daymaster: str,
) -> Dict[str, Any]:
    """过滤无效根, 返回有效根的root_class.
    输入: root_classes(build_root_classes输出), combination_facts, pillars, daymaster
    输出: {per_pillar: {pillar: {root_class, effective, reason}}, has_effective_root, effective_root_weight_class}
    """
    if not root_classes or 'per_pillar' not in root_classes:
        return {'has_effective_root': False, 'effective_root_weight_class': 'NONE', 'per_pillar': {}}

    dm_wx = WUXING.get(daymaster, '')
    branches = {k: pillars[k][1] for k in ('year', 'month', 'day', 'hour')}

    # 构建地支支持度映射(用于一对一冲旺衰比较)
    # HEAVY=3, LIGHT=2, SPECIAL=2, 藏干同类=1, NONE=0
    branch_support = {}
    for pillar, rc in root_classes['per_pillar'].items():
        z = branches.get(pillar, '')
        root_class = rc.get('root_class', 'NONE')
        if root_class.startswith('HEAVY'):
            branch_support[z] = 3
        elif root_class.startswith('LIGHT') or root_class.startswith('SPECIAL'):
            branch_support[z] = 2
        else:
            # 检查藏干中是否有日主同类
            hidden = rc.get('hidden_stems', [])
            has_same_element = any(WUXING.get(h, '') == dm_wx for h in hidden)
            branch_support[z] = 1 if has_same_element else 0

    # 1. 统计每个地支出现次数
    branch_count = {}
    for z in branches.values():
        branch_count[z] = branch_count.get(z, 0) + 1

    # 2. 检查冲: 多冲一 + 一对一冲旺衰比较
    #    2026-10-06: 冲关系以 combination_facts(排盘引擎权威) 为准, 不用本地表
    _ch_pairs = [frozenset(_p) for _p in combination_facts.get('liuchong', []) if len(_p) == 2]
    def _chong_of(z):
        for _k in _ch_pairs:
            if z in _k:
                return next((x for x in _k if x != z), '')
        return ''
    chong_map = {}  # root_branch -> [chong_branches]
    for pillar, z in branches.items():
        chong_z = _chong_of(z)
        if chong_z and chong_z in branch_count:
            chong_count = branch_count.get(chong_z, 0)
            root_count = branch_count.get(z, 0)
            if chong_count > root_count:
                chong_map[z] = f'多冲一({chong_z}x{chong_count}冲{z}x{root_count})'
            elif chong_count == root_count and root_count == 1:
                # 一对一冲, 比较旺衰(滴天髓: 旺者冲衰衰者拔, 衰神冲旺旺神发)
                z_support = branch_support.get(z, 0)
                chong_support = branch_support.get(chong_z, 0)
                if z_support < chong_support:
                    chong_map[z] = f'一对一冲衰者拔({chong_z}(支持{chong_support})冲{z}(支持{z_support}))'
                elif z_support > chong_support:
                    chong_map[z] = f'一对一冲旺神发({z}(支持{z_support})被{chong_z}(支持{chong_support})冲, 根增强)'
                else:
                    chong_map[z] = f'一对一冲两停({z}与{chong_z}支持度均为{z_support})'

    # 3. 检查三合局/三会局/半合局: 根支参与合局且合神非日主同类
    #    2026-10-06: 合局以 combination_facts(排盘权威) 为准
    heju_map = {}  # root_branch -> reason
    all_branches = list(branches.values())
    _sanhe_jus = []
    for _n in combination_facts.get('sanhe', []):
        _m = _n.split('合')
        if len(_m) == 2 and len(_m[0]) == 3:
            _sanhe_jus.append((tuple(_m[0]), _m[1]))
    _sanhui_jus = []
    for _n in combination_facts.get('sanhui', []):
        _m = _n.split('三会')
        if len(_m) == 2 and len(_m[0]) == 3:
            _sanhui_jus.append((tuple(_m[0]), _m[1]))
    _banhe_pairs = [(tuple(_b.get('pair', [])), _b.get('wx', ''))
                    for _b in combination_facts.get('banhe', [])]
    # 三合局(全)
    for ju_branches, he_wx in _sanhe_jus:
        if all(b in all_branches for b in ju_branches):
            if he_wx != dm_wx:
                for b in ju_branches:
                    if b in [z for z in branches.values()]:
                        heju_map[b] = f'三合局{ju_branches}化{he_wx}(非日主{dm_wx}), 根气被合'
    # 半合局(缺一支, 但有两支)
    for ju_branches, he_wx in _banhe_pairs:
        present = [b for b in ju_branches if b in all_branches]
        if len(present) == 2 and he_wx != dm_wx:
            # 半合局, 合神非日主同类, 参与半合的根支根气被合走(力量较弱但仍合)
            for b in present:
                if b not in heju_map:  # 不覆盖三合局的判断
                    heju_map[b] = f'半合局{present[0]}{present[1]}化{he_wx}(非日主{dm_wx}), 根气被合'
    # 三会方
    for hui_branches, he_wx in _sanhui_jus:
        if all(b in all_branches for b in hui_branches):
            if he_wx != dm_wx:
                for b in hui_branches:
                    if b in [z for z in branches.values()]:
                        heju_map[b] = f'三会方{hui_branches}化{he_wx}(非日主{dm_wx}), 根气被合'

    # 4. 过滤无效根
    per_pillar = {}
    effective_heavy = False
    effective_light = False
    for pillar, rc in root_classes['per_pillar'].items():
        z = branches.get(pillar, '')
        root_class = rc.get('root_class', 'NONE')
        if root_class == 'NONE':
            per_pillar[pillar] = {'root_class': 'NONE', 'effective': False, 'reason': '无根'}
            continue
        # 检查是否被冲(多冲一 或 一对一冲衰者拔) -> 完全失效
        if z in chong_map and ('多冲一' in chong_map[z] or '衰者拔' in chong_map[z]):
            per_pillar[pillar] = {'root_class': root_class, 'effective': False, 'reason': chong_map[z]}
            continue
        # 检查是否被三合局/三会局合走(全合) -> 降级(HEAVY->LIGHT, LIGHT->NONE)
        if z in heju_map and ('三合局' in heju_map[z] or '三会方' in heju_map[z]):
            if root_class.startswith('HEAVY'):
                downgraded = 'LIGHT'
                effective_light = True
            else:
                downgraded = 'NONE'
            per_pillar[pillar] = {'root_class': root_class, 'effective': downgraded != 'NONE',
                                   'downgraded_to': downgraded, 'reason': heju_map[z] + '(全合降级)'}
            continue
        # 检查是否被半合局合走(半合力量弱, 只标记不降级)
        if z in heju_map and '半合局' in heju_map[z]:
            per_pillar[pillar] = {'root_class': root_class, 'effective': True,
                                   'reason': heju_map[z] + '(半合仅标记)'}
            if root_class.startswith('HEAVY'):
                effective_heavy = True
            elif root_class != 'NONE':
                effective_light = True
            continue
        # 有效根
        per_pillar[pillar] = {'root_class': root_class, 'effective': True, 'reason': '有效根'}
        if root_class.startswith('HEAVY'):
            effective_heavy = True
        elif root_class != 'NONE':
            effective_light = True

    # 5. 聚合有效根weight_class
    if effective_heavy:
        effective_rwc = 'HEAVY'
    elif effective_light:
        effective_rwc = 'LIGHT'
    else:
        effective_rwc = 'NONE'

    return {
        'daymaster': daymaster,
        'per_pillar': per_pillar,
        'has_effective_root': effective_heavy or effective_light,
        'effective_root_weight_class': effective_rwc,
        'chong_map': chong_map,
        'heju_map': heju_map,
        'boundary_note': '根有效性过滤: 多冲一根失效/一对一冲旺衰比较(衰者拔旺神发两停)/合局合神非日主同类则根气被合; 不评分不加权',
    }
