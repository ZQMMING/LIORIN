# -*- coding: utf-8 -*-
"""
节点系统 - 十神级节点，取代五行级节点

节点 := 干支@宫位 × 阴阳 × 十神 × 根气 × 月令态 × 动静
边 := 生|克|合|冲|刑|害|盖头|截脚|贴身
"""
import sys
sys.path.insert(0, '.')

from spec.yinyang_system import (
    STEM_WUXING, YANG_STEMS, stem_yang,
    get_shishen, get_wuhe, get_tonggen_strength,
    SHENG, KE, SHENG_ME, KE_ME,
)
from spec.root_qi import BRANCH_CANGGAN


# ============ 节点构建 ============

def build_nodes(pillars, day_stem):
    """
    构建全部节点
    
    pillars: {'年': ['甲','子'], '月': ['乙','亥'], '日': ['丙','寅'], '时': ['丁','卯']}
    day_stem: '丙'
    
    返回：节点列表 + 边列表
    """
    positions = ['年', '月', '日', '时']
    nodes = []
    
    # 1. 干节点
    for pos in positions:
        stem = pillars[pos][0]
        is_day = (pos == '日')
        
        # 十神（日干自己不算）
        if is_day:
            shishen = '日主'
        else:
            shishen = get_shishen(day_stem, stem)
        
        nodes.append({
            'type': 'stem',
            'pos': pos,
            'ganzhi': stem,
            'wuxing': STEM_WUXING[stem],
            'yinyang': '阳' if stem_yang(stem) else '阴',
            'shishen': shishen,
            'is_day': is_day,
        })
    
    # 2. 支节点（含藏干子节点）
    for pos in positions:
        branch = pillars[pos][1]
        canggan = BRANCH_CANGGAN.get(branch, [])
        
        # 支节点本身
        nodes.append({
            'type': 'branch',
            'pos': pos,
            'ganzhi': branch,
            'wuxing': '',  # 支不直接定五行，看藏干
            'yinyang': '',
            'shishen': '',
            'is_day': False,
        })
        
        # 藏干子节点
        for level, stem in enumerate(canggan):
            if not stem:
                continue
            
            level_name = ['本气', '中气', '余气'][level] if level < 3 else '余气'
            shishen = get_shishen(day_stem, stem)
            
            nodes.append({
                'type': 'canggan',
                'pos': pos,
                'ganzhi': stem,
                'canggan_level': level_name,
                'wuxing': STEM_WUXING[stem],
                'yinyang': '阳' if stem_yang(stem) else '阴',
                'shishen': shishen,
                'is_day': False,
            })
    
    # 3. 给每个干节点加：根气、动静（包括日干）
    month_branch = pillars['月'][1]
    
    for node in nodes:
        if node['type'] == 'stem':
            stem = node['ganzhi']
            
            # 根气：查通根表，看四个地支有没有通根
            root_strength = '无根'
            for pos in positions:
                branch = pillars[pos][1]
                strength = get_tonggen_strength(stem, branch)
                if strength != '无根':
                    # 取最高级
                    order = ['无根', '库', '余气', '中气', '本气', '长生', '禄刃']
                    if order.index(strength) > order.index(root_strength):
                        root_strength = strength
            
            node['root_strength'] = root_strength
            
            # 动静：动=透干∧通根, 虚透=透干∧无根, 静=不透干
            # 干节点本身就是透干的，所以：
            if root_strength == '无根':
                node['dong_jing'] = '虚透'
            else:
                node['dong_jing'] = '动'
    
    # 4. 给每个非日干干节点加：月令态
    for node in nodes:
        if node['type'] == 'stem' and not node['is_day']:
            wx = node['wuxing']
            month_wx = STEM_WUXING.get(BRANCH_CANGGAN.get(month_branch, [''])[0], '')
            
            if month_wx == wx:
                node['yueling_state'] = '当令'
            elif SHENG[month_wx] == wx:
                node['yueling_state'] = '令生'
            elif SHENG[wx] == month_wx:
                node['yueling_state'] = '令泄'
            elif KE[month_wx] == wx:
                node['yueling_state'] = '令克'
            elif KE[wx] == month_wx:
                node['yueling_state'] = '令耗'
            else:
                node['yueling_state'] = '未知'
    
    return nodes


# ============ 边构建 ============

def build_edges(pillars, nodes):
    """
    构建边列表
    """
    edges = []
    positions = ['年', '月', '日', '时']
    
    # 1. 天干五合边
    for i, pos1 in enumerate(positions):
        for j, pos2 in enumerate(positions):
            if j <= i:
                continue
            stem1 = pillars[pos1][0]
            stem2 = pillars[pos2][0]
            
            hua_wx = get_wuhe(stem1, stem2)
            if hua_wx:
                edges.append({
                    'type': '合',
                    'pos1': pos1,
                    'stem1': stem1,
                    'pos2': pos2,
                    'stem2': stem2,
                    'hua_wx': hua_wx,
                })
    
    # 2. 天干生克边
    for i, pos1 in enumerate(positions):
        for j, pos2 in enumerate(positions):
            if j <= i:
                continue
            stem1 = pillars[pos1][0]
            stem2 = pillars[pos2][0]
            
            wx1 = STEM_WUXING[stem1]
            wx2 = STEM_WUXING[stem2]
            
            if SHENG[wx1] == wx2:
                edges.append({
                    'type': '生',
                    'pos1': pos1,
                    'stem1': stem1,
                    'pos2': pos2,
                    'stem2': stem2,
                })
            elif KE[wx1] == wx2:
                edges.append({
                    'type': '克',
                    'pos1': pos1,
                    'stem1': stem1,
                    'pos2': pos2,
                    'stem2': stem2,
                })
    
    # 3. 六冲边
    LIU_CHONG = [('子','午'),('丑','未'),('寅','申'),('卯','酉'),('辰','戌'),('巳','亥')]
    
    for i, pos1 in enumerate(positions):
        for j, pos2 in enumerate(positions):
            if j <= i:
                continue
            b1 = pillars[pos1][1]
            b2 = pillars[pos2][1]
            
            for c1, c2 in LIU_CHONG:
                if (b1 == c1 and b2 == c2) or (b1 == c2 and b2 == c1):
                    edges.append({
                        'type': '冲',
                        'pos1': pos1,
                        'branch1': b1,
                        'pos2': pos2,
                        'branch2': b2,
                    })
    
    # 4. 盖头边（干克支）
    for pos in positions:
        stem = pillars[pos][0]
        branch = pillars[pos][1]
        stem_wx = STEM_WUXING[stem]
        
        canggan = BRANCH_CANGGAN.get(branch, [])
        if canggan:
            benqi_wx = STEM_WUXING.get(canggan[0], '')
            if KE[stem_wx] == benqi_wx:
                edges.append({
                    'type': '盖头',
                    'pos': pos,
                    'stem': stem,
                    'branch': branch,
                })
    
    # 5. 截脚边（支克干）
    for pos in positions:
        stem = pillars[pos][0]
        branch = pillars[pos][1]
        stem_wx = STEM_WUXING[stem]
        
        canggan = BRANCH_CANGGAN.get(branch, [])
        if canggan:
            benqi_wx = STEM_WUXING.get(canggan[0], '')
            if KE[benqi_wx] == stem_wx:
                edges.append({
                    'type': '截脚',
                    'pos': pos,
                    'stem': stem,
                    'branch': branch,
                })
    
    # 6. 贴身边（相邻宫位：年月/月日/日时）
    adjacent_pairs = [('年', '月'), ('月', '日'), ('日', '时')]
    for pos1, pos2 in adjacent_pairs:
        edges.append({
            'type': '贴身',
            'pos1': pos1,
            'pos2': pos2,
        })
    
    return edges


# ============ 边判定函数（单一定义源） ============

def is_gaitou(stem_wx, branch_benqi_wx):
    """盖头：天干克地支（柱内）。出处：《神峰通考·盖头说》泛指干覆支，本表收窄为干克支（工程定义）"""
    return KE[stem_wx] == branch_benqi_wx


def is_jiejiao(stem_wx, branch_benqi_wx):
    """截脚：地支克天干（柱内）。出处：《滴天髓·六亲论》"""
    return KE[branch_benqi_wx] == stem_wx


def is_adjacent(pos1, pos2):
    """贴身：相邻宫位（年月/月日/日时）。出处：《子平真诠》'贴身'"""
    adjacent = {('年', '月'), ('月', '日'), ('日', '时')}
    return (pos1, pos2) in adjacent or (pos2, pos1) in adjacent


# ============ 病药查询（图查询） ============

def find_bing_yong(nodes, day_stem):
    """
    病药图查询：
    病 := ∃节点N: 克(N, 日主/相神) ∧ 动(N) ∧ 根气∈{禄刃|本气|长生}
    
    返回：(病节点, 药节点)
    """
    day_wx = STEM_WUXING[day_stem]
    
    # 找"病"节点：克日主的五行（官杀）或生日主的五行但太旺（印）
    bing_candidates = []
    
    for node in nodes:
        if node['type'] != 'stem' or node['is_day']:
            continue
        if node.get('dong_jing') != '动':
            continue
        
        wx = node['wuxing']
        root = node.get('root_strength', '无根')
        
        # 病的类型：
        # 1. 印太旺（母慈灭子）：印透干≥2个
        if wx == SHENG_ME[day_wx]:
            # 印星透干，且根气够
            if root in ['禄刃', '本气', '长生']:
                bing_candidates.append((node, '印旺成病'))
        
        # 2. 官杀克身（杀重身轻）：官杀当令
        elif wx == KE_ME[day_wx]:
            if node.get('yueling_state') == '当令':
                bing_candidates.append((node, '官杀旺成病'))
        
        # 3. 财星耗身（财多身弱）：财当令
        elif wx == KE[day_wx]:
            if node.get('yueling_state') == '当令':
                bing_candidates.append((node, '财旺成病'))
        
        # 4. 食伤泄身（泄身太过）：食伤当令
        elif wx == SHENG[day_wx]:
            if node.get('yueling_state') == '当令':
                bing_candidates.append((node, '食伤旺成病'))
    
    if not bing_candidates:
        return None, None
    
    # 按优先级取第一个病（印>官杀>财>食伤）
    priority = {'印旺成病': 0, '官杀旺成病': 1, '财旺成病': 2, '食伤旺成病': 3}
    bing_candidates.sort(key=lambda x: priority.get(x[1], 99))
    
    bing_node, bing_type = bing_candidates[0]
    
    # 找药：克病神的五行
    bing_wx = bing_node['wuxing']
    yao_wx = KE_ME.get(bing_wx, '')
    
    # 找药节点（透干或藏干）
    yao_node = None
    for node in nodes:
        if node['wuxing'] == yao_wx:
            yao_node = node
            break
    
    return bing_node, yao_node


# ============ 测试 ============

if __name__ == '__main__':
    # 用户案例：癸亥 壬戌 乙未 壬午
    pillars = {
        '年': ['癸', '亥'],
        '月': ['壬', '戌'],
        '日': ['乙', '未'],
        '时': ['壬', '午'],
    }
    day_stem = '乙'
    
    print('=== 节点系统测试 ===')
    print(f'八字: 癸亥 壬戌 乙未 壬午')
    print(f'日主: {day_stem}')
    print()
    
    nodes = build_nodes(pillars, day_stem)
    edges = build_edges(pillars, nodes)
    
    print('【干节点】')
    for node in nodes:
        if node['type'] == 'stem':
            print(f"  {node['pos']}干 {node['ganzhi']}({node['wuxing']}/{node['yinyang']}) "
                  f"= {node['shishen']} "
                  f"根气={node.get('root_strength','-')} "
                  f"动静={node.get('dong_jing','-')} "
                  f"月令={node.get('yueling_state','-')}")
    
    print()
    print('【边】')
    for edge in edges[:10]:
        print(f"  {edge['type']}: {edge}")
    
    print()
    print('【病药查询】')
    bing, yao = find_bing_yong(nodes, day_stem)
    if bing:
        print(f"  病: {bing['pos']}干 {bing['ganzhi']}({bing['wuxing']}/{bing['shishen']})")
        print(f"  药: {yao['pos']}干 {yao['ganzhi']}({yao['wuxing']}/{yao['shishen']})")
    else:
        print('  无病')
