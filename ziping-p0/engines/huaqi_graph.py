# -*- coding: utf-8 -*-
"""
化气格判定 - 纯谓词版（节点图入参）

依据：
- 《渊海子平·论化气》
- 《三命通会·论十干合》
"""
import sys
sys.path.insert(0, '.')

from spec.yinyang_system import (
    STEM_WUXING, get_wuhe,
    SHENG, KE, SHENG_ME, KE_ME,
)


def check_root_none_stem(stem, nodes):
    """
    P_某干无根：根气=无根或仅墓库
    从该干节点查root_strength
    """
    for node in nodes:
        if node['type'] == 'stem' and node['ganzhi'] == stem:
            strength = node.get('root_strength', '无根')
            if strength in ['禄刃', '本气', '中气', '长生']:
                return False
    return True


def check_de_ling(wx, nodes):
    """
    P_得令：X为月令本气
    从月支节点查
    """
    for node in nodes:
        if node['type'] == 'canggan' and node['pos'] == '月' and node['canggan_level'] == '本气':
            return node['wuxing'] == wx
    return False


def check_ke_x_dong(nodes, hua_wx):
    """
    P_无克化神之动节点：克化神的五行没有"动"的节点（虚透不破）
    """
    ke_wx = KE_ME[hua_wx]
    
    for node in nodes:
        if node['type'] == 'stem' and not node.get('is_day'):
            if node.get('wuxing') == ke_wx:
                if node.get('dong_jing') == '动':
                    return False
    
    return True


def huaqi_pan_graph(day_stem, nodes, edges):
    """
    化气格判定主入口（节点图版）
    
    返回：(是否化气, 化神五行, 失败原因列表)
    """
    failures = []
    
    # 条件①：五合边(D,N)存在
    he_target = None
    hua_wx = None
    
    for edge in edges:
        if edge['type'] == '合':
            if edge['stem1'] == day_stem:
                he_target = edge['stem2']
                hua_wx = edge['hua_wx']
                break
            elif edge['stem2'] == day_stem:
                he_target = edge['stem1']
                hua_wx = edge['hua_wx']
                break
    
    if he_target is None:
        failures.append('①无五合边')
        return False, None, failures
    
    # 条件②：D无根（化神有根不化）
    if not check_root_none_stem(day_stem, nodes):
        failures.append('②日干有根（化神有根不化）')
    
    # 条件④：化神得令
    if not check_de_ling(hua_wx, nodes):
        failures.append(f'④化神{hua_wx}不得令')
    
    # 条件⑤：无克化神之动节点
    if not check_ke_x_dong(nodes, hua_wx):
        failures.append('⑤克化神之动节点（破格）')
    
    if not failures:
        return True, hua_wx, [f'{day_stem}{he_target}化{hua_wx}']
    
    return False, None, failures


# ============ 测试 ============

if __name__ == '__main__':
    from spec.node_system import build_nodes, build_edges
    
    print('=== 化气纯谓词版（节点图入参）测试 ===')
    print()
    
    # 案例1：真化木
    case1_pillars = {
        '年': ['丙', '卯'],
        '月': ['壬', '卯'],
        '日': ['丁', '未'],
        '时': ['甲', '辰'],
    }
    case1_day = '丁'
    
    nodes1 = build_nodes(case1_pillars, case1_day)
    edges1 = build_edges(case1_pillars, nodes1)
    
    result1 = huaqi_pan_graph(case1_day, nodes1, edges1)
    print(f'案例1（真化木）:')
    print(f'  结果: {result1}')
    print()
    
    # 案例2：根破（丁有午根）
    case2_pillars = {
        '年': ['丙', '卯'],
        '月': ['壬', '卯'],
        '日': ['丁', '午'],
        '时': ['甲', '辰'],
    }
    case2_day = '丁'
    
    nodes2 = build_nodes(case2_pillars, case2_day)
    edges2 = build_edges(case2_pillars, nodes2)
    
    result2 = huaqi_pan_graph(case2_day, nodes2, edges2)
    print(f'案例2（根破-丁有午根）:')
    print(f'  结果: {result2}')
    print()
    
    # 案例3：令破（申月木绝）
    case3_pillars = {
        '年': ['丙', '申'],
        '月': ['壬', '申'],
        '日': ['丁', '未'],
        '时': ['甲', '辰'],
    }
    case3_day = '丁'
    
    nodes3 = build_nodes(case3_pillars, case3_day)
    edges3 = build_edges(case3_pillars, nodes3)
    
    result3 = huaqi_pan_graph(case3_day, nodes3, edges3)
    print(f'案例3（令破-申月木绝）:')
    print(f'  结果: {result3}')
