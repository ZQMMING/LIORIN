#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""地支角色矩阵 - 每个地支输出六层角色画像
L1 宫位角色: 年/月/日/时
L2 十神角色: 藏干对应的十神
L3 通根角色: 对日主是重根/轻根/无根
L4 用神角色: 藏干是否为用神四轨候选
L5 格局角色: 是否月令、是否格局之根
L6 气势角色: 是否成局、是否被合
"""
import sys
from spec.yinyang_system import SHENG, KE, SHENG_ME, KE_ME
sys.path.insert(0, '.')

WUXING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}


HIDDEN_STEMS = {
    '子':['癸'], '丑':['己','癸','辛'], '寅':['甲','丙','戊'], '卯':['乙'],
    '辰':['戊','乙','癸'], '巳':['丙','戊','庚'], '午':['丁','己'], '未':['己','丁','乙'],
    '申':['庚','壬','戊'], '酉':['辛'], '戌':['戊','辛','丁'], '亥':['壬','甲'],
}

TEN_GOD_MAP = {
    # (日主五行, 目标五行, 阴阳相同?) -> 十神
    ('木','木',True):'比肩', ('木','木',False):'劫财',
    ('木','火',True):'食神', ('木','火',False):'伤官',
    ('木','土',True):'偏财', ('木','土',False):'正财',
    ('木','金',True):'七杀', ('木','金',False):'正官',
    ('木','水',True):'偏印', ('木','水',False):'正印',
}

def get_ten_god(daymaster, target_stem):
    """计算十神"""
    dm_wx = WUXING[daymaster]
    tg_wx = WUXING[target_stem]
    same_yinyang = (daymaster in '甲丙戊庚壬') == (target_stem in '甲丙戊庚壬')
    # 通用计算
    if dm_wx == tg_wx:
        return '比肩' if same_yinyang else '劫财'
    elif SHENG[dm_wx] == tg_wx:
        return '食神' if same_yinyang else '伤官'
    elif KE[dm_wx] == tg_wx:
        return '偏财' if same_yinyang else '正财'
    elif KE[tg_wx] == dm_wx:
        return '七杀' if same_yinyang else '正官'
    elif SHENG[tg_wx] == dm_wx:
        return '偏印' if same_yinyang else '正印'
    return '未知'

def build_branch_role_matrix(fp, ye, f):
    """建立地支角色矩阵 - 每个地支输出六层角色画像
    
    Args:
        fp: 四柱 [(年干,年支), (月干,月支), (日干,日支), (时干,时支)]
        ye: 用神引擎输出
        f: facts输出
        
    Returns:
        dict: {position: {branch, palace, hidden_roles, root_role, yongshen_role, pattern_role, qi_role}}
    """
    positions = ['year', 'month', 'day', 'hour']
    dm = f.get('day_stem', fp[2][0])
    
    # 用神候选
    yongshen_candidates = ye.get('yongshen_candidates', [])
    candidate_wuxing = set(c.get('wuxing') for c in yongshen_candidates if c.get('wuxing'))
    primary = ye.get('yongshen_primary')
    secondary = set(ye.get('yongshen_secondary', []))
    avoid = set(ye.get('yongshen_avoid', []))
    
    # 通根信息
    root_weight = f.get('root_weight_class_facts', {})
    
    # 月令信息
    month_branch = f.get('month_branch', fp[1][1])
    month_transparent = f.get('month_transparent', [])
    month_supports_dm = f.get('month_supports_daymaster', False)
    
    # 气势信息 - 从combination_facts获取
    combination_facts = f.get('combination_facts', {})
    
    result = {}
    for i, pos in enumerate(positions):
        g, z = fp[i]
        hidden = HIDDEN_STEMS.get(z, [])
        
        # L1 宫位角色
        palace_map = {'year':'年柱', 'month':'月令', 'day':'日支', 'hour':'时柱'}
        palace = palace_map.get(pos, pos)
        
        # L2 十神角色 - 每个藏干的十神
        hidden_ten_gods = []
        for h in hidden:
            tg = get_ten_god(dm, h)
            hidden_ten_gods.append({'stem': h, 'ten_god': tg, 'wuxing': WUXING[h]})
        
        # L3 通根角色
        root_info = root_weight.get(pos, {})
        root_type = root_info.get('root_type', '无根')
        root_class = root_info.get('class', 'NONE')
        
        # L4 用神角色 - 每个藏干是否为用神候选
        hidden_yongshen = []
        for htg in hidden_ten_gods:
            h_wx = htg['wuxing']
            is_primary = (h_wx == primary) if primary else False
            is_secondary = (h_wx in secondary)
            is_candidate = (h_wx in candidate_wuxing)
            is_avoid = (h_wx in avoid)
            role = 'primary' if is_primary else ('secondary' if is_secondary else ('candidate' if is_candidate else ('avoid' if is_avoid else 'none')))
            hidden_yongshen.append({
                'stem': htg['stem'],
                'wuxing': h_wx,
                'ten_god': htg['ten_god'],
                'yongshen_role': role,
                'is_primary': is_primary,
                'is_secondary': is_secondary,
                'is_candidate': is_candidate,
                'is_avoid': is_avoid,
            })
        
        # L5 格局角色
        is_month = (pos == 'month')
        is_day_branch = (pos == 'day')
        is_month_branch = (z == month_branch)
        is_transparent_root = (z == month_branch and len(month_transparent) > 0)
        is_pattern_root = is_month_branch or is_transparent_root
        
        pattern_role = []
        if is_month: pattern_role.append('月令')
        if is_day_branch: pattern_role.append('日支(配偶宫)')
        if is_transparent_root: pattern_role.append('格局之根(透干)')
        if month_supports_dm and is_month: pattern_role.append('月令生扶日主')
        
        # L6 气势角色 - 简化版，后续完善
        qi_role = []
        # 检查是否被天干合
        stem_combos = f.get('stem_combination_facts', {}).get('wuhe', [])
        for sc in stem_combos:
            if z in str(sc):
                qi_role.append('被合')
        
        result[pos] = {
            'branch': z,
            'palace': palace,  # L1
            'hidden_roles': hidden_yongshen,  # L2+L4 合并
            'root_type': root_type,  # L3
            'root_class': root_class,  # L3
            'pattern_role': pattern_role,  # L5
            'qi_role': qi_role,  # L6
            # 综合角色标签
            'is_dm_root': root_class.startswith('HEAVY') or root_class.startswith('LIGHT')
                      or root_class.startswith('SPECIAL'),
            'is_heavy_root': root_class.startswith('HEAVY'),
            'is_light_root': root_class.startswith('LIGHT') or root_class.startswith('SPECIAL'),
            'has_primary_yongshen': any(h['is_primary'] for h in hidden_yongshen),
            'has_secondary_yongshen': any(h['is_secondary'] for h in hidden_yongshen),
            'has_avoid': any(h['is_avoid'] for h in hidden_yongshen),
            'is_pattern_root': is_pattern_root,
        }
    
    return result


def format_branch_role_matrix(matrix):
    """格式化输出地支角色矩阵"""
    lines = []
    for pos, info in matrix.items():
        line = f"[{info['palace']}{info['branch']}] "
        roles = []
        if info['is_heavy_root']: roles.append(f"重根({info['root_type']})")
        elif info['is_light_root']: roles.append(f"轻根({info['root_type']})")
        if info['has_primary_yongshen']: roles.append('用神根')
        elif info['has_secondary_yongshen']: roles.append('喜神根')
        if info['has_avoid']: roles.append('忌神根')
        if info['is_pattern_root']: roles.append('格局根')
        roles.extend(info['pattern_role'])
        roles.extend(info['qi_role'])
        # 藏干十神
        hidden_str = '/'.join(f"{h['stem']}({h['ten_god']})" for h in info['hidden_roles'])
        line += f"藏干:{hidden_str} 角色:{','.join(roles) if roles else '普通'}"
        lines.append(line)
    return '\n'.join(lines)


if __name__ == '__main__':
    # 测试用L491案例
    import importlib.util
    spec = importlib.util.spec_from_file_location("dayun_align_mod", "scripts/dayun_align.py")
    mod = importlib.util.module_from_spec(spec)
    import unittest.mock
    with unittest.mock.patch('sys.argv', ['dayun_align.py']):
        try: spec.loader.exec_module(mod)
        except SystemExit: pass
    
    for li, fp, dy, txt in mod.cases:
        if li+1 != 491: continue
        try: p, f, ye, tp0 = mod.engine(fp)
        except: continue
        matrix = build_branch_role_matrix(fp, ye, f)
        print(f"L491 {''.join(a+b for a,b in fp)}")
        print(format_branch_role_matrix(matrix))
        print()
        break
