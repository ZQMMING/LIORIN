# -*- coding: utf-8 -*-
"""
从格判定 - 纯谓词版（无浮点权重）

依据：
- 《滴天髓》"五阳从气不从势，五阴从势无情义"
- 《子平真诠》从格条件
"""
import sys
sys.path.insert(0, '.')

from spec.yinyang_system import (
    STEM_WUXING, stem_yang, get_shishen,
    SHENG, KE, SHENG_ME, KE_ME,
    get_tonggen_strength,
)
from spec.root_qi import BRANCH_CANGGAN


def check_root_none(day_stem, branches, strict=False):
    """
    P_日主无根：根气=无根或仅墓库
    strict=True时（阳干）：连墓库都不能有，完全无根
    """
    for b in branches:
        strength = get_tonggen_strength(day_stem, b)
        if strict:
            # 阳干从气：完全无根，连墓库都不能有
            if strength != '无根':
                return False
        else:
            # 阴干从势：根气=无根或仅墓库
            if strength in ['禄刃', '本气', '中气', '长生']:
                return False
    return True


def check_yin_tou_gan_dong(day_stem, stems, branches):
    """
    P_印星透干动：印星透干且有根
    """
    day_wx = STEM_WUXING[day_stem]
    yin_wx = SHENG_ME[day_wx]  # 印星五行
    
    for stem in stems:
        if STEM_WUXING.get(stem, '') == yin_wx:
            # 印星透干，查有没有根
            for b in branches:
                canggan = BRANCH_CANGGAN.get(b, [])
                for cg in canggan:
                    if STEM_WUXING.get(cg, '') == yin_wx:
                        return True  # 印星透干且有根
    return False


def check_bijie_gen(day_stem, branches):
    """
    P_比劫无根：比劫（同五行）在地支没有根
    """
    day_wx = STEM_WUXING[day_stem]
    
    for b in branches:
        canggan = BRANCH_CANGGAN.get(b, [])
        for cg in canggan:
            if STEM_WUXING.get(cg, '') == day_wx:
                return False  # 比劫有根
    return True


def find_cong_target(day_stem, stems, branches):
    """
    找从对象：克/耗/泄日主且动的五行中，谁最众
    返回：(从对象五行, 从对象十神类型)
    """
    day_wx = STEM_WUXING[day_stem]
    
    # 候选：克我（官杀）、我克（财）、我生（食伤）
    candidates = {
        KE_ME[day_wx]: '官杀',  # 克我者
        KE[day_wx]: '财',      # 我克者
        SHENG[day_wx]: '食伤',  # 我生者
    }
    
    # 统计每个候选的"动"节点数（透干且有根）
    scores = {}
    for wx, name in candidates.items():
        count = 0
        
        # 天干透干
        for stem in stems:
            if STEM_WUXING.get(stem, '') == wx:
                # 查有没有根
                has_gen = False
                for b in branches:
                    canggan = BRANCH_CANGGAN.get(b, [])
                    for cg in canggan:
                        if STEM_WUXING.get(cg, '') == wx:
                            has_gen = True
                            break
                    if has_gen:
                        break
                if has_gen:
                    count += 1
        
        # 地支有根（即使不透干）
        for b in branches:
            canggan = BRANCH_CANGGAN.get(b, [])
            for cg in canggan:
                if STEM_WUXING.get(cg, '') == wx:
                    count += 1
                    break
        
        scores[wx] = count
    
    # 找得分最高的
    best_wx = max(scores.items(), key=lambda kv: kv[1])[0]
    best_name = candidates[best_wx]
    
    return best_wx, best_name


def check_yin_cang_gen(day_stem, branches):
    """
    P_印星藏干：印星在地支藏干中存在（阳干从气需要连藏干印都没有）
    """
    day_wx = STEM_WUXING[day_stem]
    yin_wx = SHENG_ME[day_wx]  # 印星五行
    
    for b in branches:
        canggan = BRANCH_CANGGAN.get(b, [])
        for cg in canggan:
            if STEM_WUXING.get(cg, '') == yin_wx:
                return True  # 印星藏干有根
    return False


def cong_ge_pan_predicate(day_stem, stems, branches):
    """
    从格判定主入口（纯谓词版）
    
    全量求值：列出所有不满足的条件，不短路
    返回：(是否从格, 从对象, 失败原因列表)
    """
    day_yang = stem_yang(day_stem)
    failures = []
    
    # 硬条件1：日主无根
    # 阳干从气不从势：更严格，连墓库都不能有
    strict = day_yang
    if not check_root_none(day_stem, branches, strict=strict):
        failures.append('①日主有根')
    
    # 硬条件2：印星不透干动
    if check_yin_tou_gan_dong(day_stem, stems, branches):
        failures.append('②印星透干动')
    
    # 硬条件3：比劫无根
    if not check_bijie_gen(day_stem, branches):
        failures.append('③比劫有根')
    
    # 阳干更严：印星连藏干都不能有（从气不从势）
    if day_yang:
        if check_yin_cang_gen(day_stem, branches):
            failures.append('④阳干从气：印星藏干有根')
    
    # 全部满足 → 从格
    if not failures:
        # 找从对象
        cong_wx, cong_name = find_cong_target(day_stem, stems, branches)
        return True, cong_name, [f'从{cong_name}']
    
    return False, None, failures


# ============ 测试 ============

if __name__ == '__main__':
    print('=== 从格纯谓词版测试 ===')
    print()
    
    # 测试1：乙木日主全局金动无根 → 从杀
    # 乙日主，全局金官杀成势，乙木无根
    case1_stems = ['辛', '庚', '乙', '辛']
    case1_branches = ['酉', '申', '酉', '巳']
    case1_day = '乙'
    
    result1 = cong_ge_pan_predicate(case1_day, case1_stems, case1_branches)
    print(f'案例1（乙全局金）:')
    print(f'  结果: {result1}')
    print()
    
    # 测试2：甲日主同样的金局 → 不从（阳干从气不从势）
    case2_stems = ['辛', '庚', '甲', '辛']
    case2_branches = ['酉', '申', '酉', '巳']
    case2_day = '甲'
    
    result2 = cong_ge_pan_predicate(case2_day, case2_stems, case2_branches)
    print(f'案例2（甲全局金）:')
    print(f'  结果: {result2}')
    print()
    
    # 测试3：用户案例（癸亥 壬戌 乙未 壬午）
    case3_stems = ['癸', '壬', '乙', '壬']
    case3_branches = ['亥', '戌', '未', '午']
    case3_day = '乙'
    
    result3 = cong_ge_pan_predicate(case3_day, case3_stems, case3_branches)
    print(f'案例3（用户案例）:')
    print(f'  结果: {result3}')
