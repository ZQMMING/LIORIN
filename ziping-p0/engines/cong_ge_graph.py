# -*- coding: utf-8 -*-
"""
从格判定 - 纯谓词版（节点图入参）

依据：
- 《滴天髓》"五阳从气不从势，五阴从势无情义"
- 《子平真诠》从格条件
"""
import sys
sys.path.insert(0, '.')

from spec.yinyang_system import (
    STEM_WUXING, stem_yang,
    SHENG, KE, SHENG_ME, KE_ME,
    get_tonggen_strength,
)


def check_root_none(day_stem, nodes, strict=False):
    """
    P_日主无独立根：无禄刃/本气根（长生/余气/墓库属弱根，不挡从）
    依据：《滴天髓》"五阴从势无情义"——阴干弱根不挡从
    从日干节点查root_strength
    """
    day_node = None
    for node in nodes:
        if node.get('is_day') and node['type'] == 'stem':
            day_node = node
            break
    
    if day_node is None:
        return False
    
    strength = day_node.get('root_strength', '无根')
    
    # 独立根：禄刃/本气 → 不从
    # 弱根：长生/中气/余气/墓库 → 不挡从（阴干从势）
    if strength in ['禄刃', '本气']:
        return False
    
    return True


def check_yin_tou_gan_dong(day_stem, nodes):
    """
    P_印星见：印星透干，或坐独立根（该支本气=印）
    依据：《子平真诠》"不见印星"+推演（独立根据地才算见）
    印寄生他神支（如申中壬，申本气庚）→ 不算见
    """
    day_wx = STEM_WUXING[day_stem]
    yin_wx = SHENG_ME[day_wx]  # 印星五行
    
    # 印星透干（哪怕虚透也算见）
    for node in nodes:
        if node['type'] == 'stem' and not node.get('is_day'):
            if node.get('wuxing') == yin_wx:
                return True
    
    # 印星独立根：该支本气=印（canggan_level=本气）
    for node in nodes:
        if node['type'] == 'canggan' and node.get('wuxing') == yin_wx:
            if node.get('canggan_level') == '本气':
                return True
    
    return False


def check_bijie_gen(day_stem, nodes):
    """
    P_比劫无独立根：比劫（同五行）在本气根才算挡从
    依据：与从格②同口径——独立根才挡从
    中气/余气/长生/墓库不算
    返回True=无独立根（不挡从），False=有独立根（挡从）
    """
    day_wx = STEM_WUXING[day_stem]
    
    for node in nodes:
        if node['type'] == 'canggan':
            if node.get('wuxing') == day_wx:
                if node.get('canggan_level') == '本气':
                    return False  # 比劫有独立根，挡从
    
    return True  # 比劫无独立根，不挡从


def check_yin_cang_gen(day_stem, nodes):
    """
    P_印星藏干：印星在地支藏干中存在（阳干从气需要连藏干印都没有）
    """
    day_wx = STEM_WUXING[day_stem]
    yin_wx = SHENG_ME[day_wx]
    
    for node in nodes:
        if node['type'] == 'canggan':
            if node.get('wuxing') == yin_wx:
                return True
    
    return False


def find_cong_target(day_stem, nodes):
    """
    找从对象：克/耗/泄日主且动的五行中，谁最众
    """
    day_wx = STEM_WUXING[day_stem]
    
    candidates = {
        KE_ME[day_wx]: '官杀',
        KE[day_wx]: '财',
        SHENG[day_wx]: '食伤',
    }
    
    scores = {}
    for wx, name in candidates.items():
        count = 0
        
        # 天干透干且动
        for node in nodes:
            if node['type'] == 'stem' and not node.get('is_day'):
                if node.get('wuxing') == wx and node.get('dong_jing') == '动':
                    count += 1
        
        # 地支藏干
        for node in nodes:
            if node['type'] == 'canggan':
                if node.get('wuxing') == wx:
                    count += 1
                    break
        
        scores[wx] = count
    
    best_wx = max(scores.items(), key=lambda kv: kv[1])[0]
    best_name = candidates[best_wx]
    
    return best_wx, best_name


def cong_ge_pan_graph(day_stem, nodes, edges):
    """
    从格判定主入口（节点图入参）
    
    返回：(是否从格, 从对象, 失败原因列表)
    """
    day_yang = stem_yang(day_stem)
    failures = []
    
    # 硬条件1：日主无独立根
    strict = day_yang
    if not check_root_none(day_stem, nodes, strict=strict):
        failures.append('①日主有根')
    
    # 硬条件2：印星不见
    if check_yin_tou_gan_dong(day_stem, nodes):
        failures.append('②印星见')
    
    # 硬条件3：比劫无独立根
    if not check_bijie_gen(day_stem, nodes):
        failures.append('③比劫有根')
    
    # 从格四条并为三条，全部走v4统一口径，无阴阳分支
    
    if not failures:
        cong_wx, cong_name = find_cong_target(day_stem, nodes)
        return True, cong_name, [f'从{cong_name}']
    
    return False, None, failures


# ============ 测试 ============

if __name__ == '__main__':
    from spec.node_system import build_nodes, build_edges
    
    print('=== 从格纯谓词版（节点图入参）测试 ===')
    print()
    
    # 测试1：乙木日主全局金动无根 → 从杀
    case1_pillars = {
        '年': ['辛', '酉'],
        '月': ['庚', '申'],
        '日': ['乙', '酉'],
        '时': ['辛', '巳'],
    }
    case1_day = '乙'
    
    nodes1 = build_nodes(case1_pillars, case1_day)
    edges1 = build_edges(case1_pillars, nodes1)
    
    result1 = cong_ge_pan_graph(case1_day, nodes1, edges1)
    print(f'案例1（乙全局金）:')
    print(f'  结果: {result1}')
    print()
    
    # 测试2：甲日主同样的金局 → 不从
    case2_pillars = {
        '年': ['辛', '酉'],
        '月': ['庚', '申'],
        '日': ['甲', '酉'],
        '时': ['辛', '巳'],
    }
    case2_day = '甲'
    
    nodes2 = build_nodes(case2_pillars, case2_day)
    edges2 = build_edges(case2_pillars, nodes2)
    
    result2 = cong_ge_pan_graph(case2_day, nodes2, edges2)
    print(f'案例2（甲全局金）:')
    print(f'  结果: {result2}')
    print()
    
    # 测试3：用户案例
    case3_pillars = {
        '年': ['癸', '亥'],
        '月': ['壬', '戌'],
        '日': ['乙', '未'],
        '时': ['壬', '午'],
    }
    case3_day = '乙'
    
    nodes3 = build_nodes(case3_pillars, case3_day)
    edges3 = build_edges(case3_pillars, nodes3)
    
    result3 = cong_ge_pan_graph(case3_day, nodes3, edges3)
    print(f'案例3（用户案例）:')
    print(f'  结果: {result3}')
