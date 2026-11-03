# -*- coding: utf-8 -*-
"""
专旺格判定 - 纯谓词版（无浮点权重）

依据：
- 《滴天髓》专旺五格：曲直(木) 炎上(火) 稼穑(土) 从革(金) 润下(水)
- 关键：专旺的本质是"无克破"，不是"力量大"
"""
import sys
sys.path.insert(0, '.')

from spec.yinyang_system import (
    STEM_WUXING, stem_yang, get_tonggen_strength,
    SHENG, KE, SHENG_ME, KE_ME,
)
from spec.root_qi import BRANCH_CANGGAN


# 专旺五格
ZHUANWANG_WUGE = {
    '木': '曲直格',
    '火': '炎上格',
    '土': '稼穑格',
    '金': '从革格',
    '水': '润下格',
}


def check_de_ling(day_wx, month_branch):
    """
    P_得令：X为月令本气
    """
    canggan = BRANCH_CANGGAN.get(month_branch, [])
    if canggan:
        return STEM_WUXING.get(canggan[0], '') == day_wx
    return False


def check_root_lu_ren(day_stem, branches):
    """
    P_通根∈{禄刃}：日主根气是禄或刃
    """
    for b in branches:
        strength = get_tonggen_strength(day_stem, b)
        if strength == '禄刃':
            return True
    return False


def check_node_dong_gen(stems, branches, wx):
    """
    P_节点动且根气≥本气：某五行有节点透干且有根（本气以上）
    """
    # 天干透干
    for stem in stems:
        if STEM_WUXING.get(stem, '') == wx:
            # 查有没有根
            for b in branches:
                canggan = BRANCH_CANGGAN.get(b, [])
                for cg in canggan:
                    if STEM_WUXING.get(cg, '') == wx:
                        return True  # 透干且有根
    return False


def check_ke_x_dong(stems, branches, day_wx):
    """
    P_无克X之动节点：克日主干系中，没有"动"的节点（虚透不破，制尽才破）
    
    克日主干系 = 官杀（KE_ME[day_wx]）
    """
    ke_wx = KE_ME[day_wx]  # 克日主的五行（官杀）
    
    # 查克日主的五行有没有"动"的节点
    for stem in stems:
        if STEM_WUXING.get(stem, '') == ke_wx:
            # 克神透干，查有没有根
            has_gen = False
            for b in branches:
                canggan = BRANCH_CANGGAN.get(b, [])
                for cg in canggan:
                    if STEM_WUXING.get(cg, '') == ke_wx:
                        has_gen = True
                        break
                if has_gen:
                    break
            
            if has_gen:
                # 克神透干且有根 → 动，破格
                return False
    
    # 克神藏干有根但不透 → 静，不算动
    return True


def zhuanwang_pan_predicate(day_stem, stems, branches):
    """
    专旺格判定主入口（纯谓词版）
    
    全量求值：列出所有不满足的条件，不短路
    返回：(是否专旺, 格名, 失败原因列表)
    """
    day_wx = STEM_WUXING[day_stem]
    month_branch = branches[1]  # 月支
    failures = []
    
    # 条件②：X得令
    if not check_de_ling(day_wx, month_branch):
        failures.append(f'②{day_wx}不得令')
    
    # 条件③：日主通根∈{禄刃}
    if not check_root_lu_ren(day_stem, branches):
        failures.append('③日主根气非禄刃')
    
    # 条件④：印星动（生X的节点动且根气≥本气）
    yin_wx = SHENG_ME[day_wx]  # 印星五行
    if not check_node_dong_gen(stems, branches, yin_wx):
        failures.append(f'④印星{yin_wx}不动')
    
    # 条件⑥：无克X之动节点（虚透不破，制尽才破）
    if not check_ke_x_dong(stems, branches, day_wx):
        failures.append('⑥官杀动有根（破格）')
    
    # 全部满足 → 专旺
    if not failures:
        ge_name = ZHUANWANG_WUGE.get(day_wx, '专旺')
        return True, ge_name, [f'{ge_name}成']
    
    return False, None, failures


# ============ 测试 ============

if __name__ == '__main__':
    print('=== 专旺纯谓词版测试 ===')
    print()
    
    # 案例1：甲日主，寅卯月，亥卯未支全，壬透动，无庚辛动 → 曲直格
    case1_stems = ['壬', '甲', '甲', '壬']
    case1_branches = ['寅', '寅', '卯', '亥']
    case1_day = '甲'
    
    result1 = zhuanwang_pan_predicate(case1_day, case1_stems, case1_branches)
    print(f'案例1（曲直格）:')
    print(f'  天干: {case1_stems}')
    print(f'  地支: {case1_branches}')
    print(f'  结果: {result1}')
    print()
    
    # 案例2：同案例1但加庚@干虚透（无根）→ 曲直格（虚透不破）
    case2_stems = ['壬', '甲', '庚', '壬']
    case2_branches = ['寅', '寅', '卯', '亥']
    case2_day = '甲'
    
    result2 = zhuanwang_pan_predicate(case2_day, case2_stems, case2_branches)
    print(f'案例2（虚透庚）:')
    print(f'  天干: {case2_stems}')
    print(f'  地支: {case2_branches}')
    print(f'  结果: {result2}')
    print()
    
    # 案例3：加庚@干有根 → 破格
    case3_stems = ['壬', '甲', '庚', '壬']
    case3_branches = ['寅', '寅', '酉', '亥']
    case3_day = '甲'
    
    result3 = zhuanwang_pan_predicate(case3_day, case3_stems, case3_branches)
    print(f'案例3（庚有根酉）:')
    print(f'  天干: {case3_stems}')
    print(f'  地支: {case3_branches}')
    print(f'  结果: {result3}')
