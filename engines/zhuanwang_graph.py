# -*- coding: utf-8 -*-
"""
专旺格判定 - 纯谓词版（节点图入参）

依据：
- 《渊海子平·外十八格》专旺五格
- 关键：专旺的本质是"地支成局 + 无克破"
"""
import sys
sys.path.insert(0, '.')

from spec.yinyang_system import (
    STEM_WUXING,
    SHENG, KE, SHENG_ME, KE_ME,
)


# 专旺五格
ZHUANWANG_WUGE = {
    '木': '曲直格',
    '火': '炎上格',
    '土': '稼穑格',
    '金': '从革格',
    '水': '润下格',
}

# 五合成局要求（地支）
JU_REQUIRE = {
    '木': [['寅', '卯', '辰'], ['亥', '卯', '未']],  # 三会/三合
    '火': [['巳', '午', '未'], ['寅', '午', '戌']],  # 三会/三合
    '土': [['辰', '戌', '丑', '未']],  # 四库全
    '金': [['申', '酉', '戌'], ['巳', '酉', '丑']],  # 三会/三合
    '水': [['亥', '子', '丑'], ['申', '子', '辰']],  # 三会/三合
}


def check_de_ling(day_wx, nodes):
    """
    P_得令：X为月令本气
    从月支节点查
    """
    for node in nodes:
        if node['type'] == 'branch' and node['pos'] == '月':
            # 找月支的本气藏干
            for cg in nodes:
                if cg['type'] == 'canggan' and cg['pos'] == '月' and cg['canggan_level'] == '本气':
                    return cg['wuxing'] == day_wx
    return False


def check_branch_ju(day_wx, nodes):
    """
    P_地支成局：按五合成局要求判断
    依据：《渊海子平·外十八格》"X全"
    """
    # 收集所有地支
    branches = []
    for node in nodes:
        if node['type'] == 'branch':
            branches.append(node['ganzhi'])
    
    # 按五行检查是否成局
    required_ju = JU_REQUIRE.get(day_wx, [])
    for ju in required_ju:
        # 检查是否包含局中所有地支
        if all(b in branches for b in ju):
            return True
    
    return False


def check_ke_x_dong(nodes, day_wx):
    """
    P_无克X之动节点：克日主干系中，没有"动"的节点（虚透不破，制尽才破）
    """
    ke_wx = KE_ME[day_wx]  # 克日主的五行（官杀）
    
    for node in nodes:
        if node['type'] == 'stem' and not node.get('is_day'):
            if node.get('wuxing') == ke_wx:
                if node.get('dong_jing') == '动':
                    # 克神透干且有根 → 动，破格
                    return False
    
    return True


def zhuanwang_pan_graph(day_stem, nodes, edges):
    """
    专旺格判定主入口（节点图版）
    
    返回：(是否专旺, 格名, 失败原因列表)
    """
    day_wx = STEM_WUXING[day_stem]
    failures = []
    
    # 条件②：X得令
    if not check_de_ling(day_wx, nodes):
        failures.append(f'②{day_wx}不得令')
    
    # 条件③：地支成局（三会/三合/四库全）
    if not check_branch_ju(day_wx, nodes):
        failures.append('③地支不成局')
    
    # 条件⑥：无克X之动节点（虚透不破，制尽才破）
    if not check_ke_x_dong(nodes, day_wx):
        failures.append('⑥官杀动有根（破格）')
    
    if not failures:
        ge_name = ZHUANWANG_WUGE.get(day_wx, '专旺')
        return True, ge_name, [f'{ge_name}成']
    
    return False, None, failures


# ============ 测试 ============

if __name__ == '__main__':
    from spec.node_system import build_nodes, build_edges
    
    print('=== 专旺纯谓词版（节点图入参）测试 ===')
    print()
    
    # 案例1：曲直格（亥卯未全）
    case1_pillars = {
        '年': ['壬', '亥'],
        '月': ['甲', '卯'],
        '日': ['甲', '未'],
        '时': ['壬', '卯'],
    }
    case1_day = '甲'
    
    nodes1 = build_nodes(case1_pillars, case1_day)
    edges1 = build_edges(case1_pillars, nodes1)
    
    result1 = zhuanwang_pan_graph(case1_day, nodes1, edges1)
    print(f'案例1（曲直格-亥卯未全）:')
    print(f'  结果: {result1}')
    print()
    
    # 案例2：炎上格（巳午未全）
    case2_pillars = {
        '年': ['丙', '巳'],
        '月': ['甲', '午'],
        '日': ['丙', '未'],
        '时': ['甲', '午'],
    }
    case2_day = '丙'
    
    nodes2 = build_nodes(case2_pillars, case2_day)
    edges2 = build_edges(case2_pillars, nodes2)
    
    result2 = zhuanwang_pan_graph(case2_day, nodes2, edges2)
    print(f'案例2（炎上格-巳午未全）:')
    print(f'  结果: {result2}')
    print()
    
    # 案例3：普通正格（寅午子辰，不成局）
    case3_pillars = {
        '年': ['甲', '子'],
        '月': ['丙', '寅'],
        '日': ['甲', '辰'],
        '时': ['庚', '午'],
    }
    case3_day = '甲'
    
    nodes3 = build_nodes(case3_pillars, case3_day)
    edges3 = build_edges(case3_pillars, nodes3)
    
    result3 = zhuanwang_pan_graph(case3_day, nodes3, edges3)
    print(f'案例3（普通正格-不成局）:')
    print(f'  结果: {result3}')
