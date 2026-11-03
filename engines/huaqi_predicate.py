# -*- coding: utf-8 -*-
"""
化气格判定 - 纯谓词版（无浮点权重）

依据：
- 《渊海子平·论化气》
- 《三命通会·论十干合》
"""
import sys
sys.path.insert(0, '.')

from spec.yinyang_system import (
    STEM_WUXING, get_wuhe, get_tonggen_strength,
    SHENG, KE, SHENG_ME, KE_ME,
)
from spec.root_qi import BRANCH_CANGGAN


def check_root_none(stem, branches):
    """
    P_日主无根：根气=无根或仅墓库
    """
    for b in branches:
        strength = get_tonggen_strength(stem, b)
        if strength in ['禄刃', '本气', '中气', '长生']:
            return False
    return True


def check_de_ling(wx, month_branch):
    """
    P_得令：X为月令本气
    """
    canggan = BRANCH_CANGGAN.get(month_branch, [])
    if canggan:
        return STEM_WUXING.get(canggan[0], '') == wx
    return False


def check_ke_x_dong(stems, branches, hua_wx):
    """
    P_无克化神之动节点：克化神的五行没有"动"的节点（虚透不破）
    """
    ke_wx = KE_ME[hua_wx]  # 克化神的五行
    
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
                return False  # 克神透干且有根 → 动，破格
    
    return True


def huaqi_pan_predicate(day_stem, stems, branches):
    """
    化气格判定主入口（纯谓词版）
    
    全量求值：列出所有不满足的条件，不短路
    返回：(是否化气, 化神五行, 失败原因列表)
    """
    month_branch = branches[1]  # 月支
    failures = []
    
    # 条件①：五合边(D,N)存在
    he_target = None
    hua_wx = None
    
    if stems[1] != day_stem:
        hua = get_wuhe(day_stem, stems[1])
        if hua:
            he_target = stems[1]
            hua_wx = hua
    
    if he_target is None and stems[3] != day_stem:
        hua = get_wuhe(day_stem, stems[3])
        if hua:
            he_target = stems[3]
            hua_wx = hua
    
    if he_target is None:
        failures.append('①无五合边')
        return False, None, failures
    
    # 条件②：D无根
    if not check_root_none(day_stem, branches):
        failures.append('②日干有根（化神有根不化）')
    
    # 条件③：N同理不占强根
    if not check_root_none(he_target, branches):
        failures.append('③合神有强根（合而不专则不化）')
    
    # 条件④：化神得令
    if not check_de_ling(hua_wx, month_branch):
        failures.append(f'④化神{hua_wx}不得令')
    
    # 条件⑤：无克化神之动节点
    if not check_ke_x_dong(stems, branches, hua_wx):
        failures.append('⑤克化神之动节点（破格）')
    
    # 全部满足 → 化气
    if not failures:
        return True, hua_wx, [f'{day_stem}{he_target}化{hua_wx}']
    
    return False, None, failures


# ============ 测试 ============

if __name__ == '__main__':
    print('=== 化气纯谓词版测试 ===')
    print()
    
    # 案例1 真化：丁日主，壬@月干，丁无根，卯月 → 化木格
    case1_stems = ['丙', '壬', '丁', '甲']
    case1_branches = ['卯', '卯', '未', '辰']
    case1_day = '丁'
    
    result1 = huaqi_pan_predicate(case1_day, case1_stems, case1_branches)
    print(f'案例1（真化木）:')
    print(f'  天干: {case1_stems}')
    print(f'  地支: {case1_branches}')
    print(f'  结果: {result1}')
    print()
    
    # 案例2 假化①根破：同案例1但支中有午 → 不化
    case2_stems = ['丙', '壬', '丁', '甲']
    case2_branches = ['卯', '卯', '午', '辰']
    case2_day = '丁'
    
    result2 = huaqi_pan_predicate(case2_day, case2_stems, case2_branches)
    print(f'案例2（根破-丁有午根）:')
    print(f'  天干: {case2_stems}')
    print(f'  地支: {case2_branches}')
    print(f'  结果: {result2}')
    print()
    
    # 案例3 假化②令破：同案例1换申月 → 不化
    case3_stems = ['丙', '壬', '丁', '甲']
    case3_branches = ['申', '申', '未', '辰']
    case3_day = '丁'
    
    result3 = huaqi_pan_predicate(case3_day, case3_stems, case3_branches)
    print(f'案例3（令破-申月木绝）:')
    print(f'  天干: {case3_stems}')
    print(f'  地支: {case3_branches}')
    print(f'  结果: {result3}')
