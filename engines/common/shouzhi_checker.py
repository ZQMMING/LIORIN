# -*- coding: utf-8 -*-
"""
L2-4 受制折减(降档制)
机制: 降档制, 不用系数
原则: 维1保底不穿负档, 崩坏归维4, 维3不与母灭叠加算术
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import _is_chong

# 降档映射表(参数外置)
# 档位枚举: 禄刃 > 长生 > 库 > 无根 > 受制
DANG_WEI = ['禄刃', '长生', '库', '无根', '受制']

# 降档规则(参数外置)
JIANG_DANG = {
    'chong_zhong': 1,  # 冲克(中神/禄刃)→降一档
    'chong_fei': 0,    # 冲克(非中神)→不降档, 仅标记
    'jushang': 0,      # 局伤/方伤→党众加成折减数值⏸挂验, 机制先记标记
}


def check_shouzhi(day_master: str, branches: list, hehui_summary: dict) -> dict:
    """
    受制判定入口(接拓扑维3)
    输入: 日主+四支+合会汇总层
    输出: {shouzhi_type: '无'/'冲克'/'局伤'/'崩坏', jiang_dang: 降档数}
    """
    # 1. 冲克检测
    chong_type = '无'
    for i, b1 in enumerate(branches):
        for b2 in branches[i+1:]:
            if _is_chong(b1, b2):
                # 中神/禄刃被冲?
                # 简化: 先判有无冲克
                chong_type = '冲克'
                break
        if chong_type != '无':
            break

    # 2. 局伤检测(接#017/#023)
    jushang = False
    for h in hehui_summary.get('hehui', []):
        if h.get('status') in ['局伤', '方伤']:
            jushang = True
            break

    # 3. 降档数计算
    jiang = 0
    if chong_type == '冲克':
        jiang += JIANG_DANG['chong_zhong']  # 先按中神算
    if jushang:
        # 局伤数值⏸挂验, 机制先记标记
        pass

    # 4. 边界守卫: 保底不穿负档
    jiang = min(jiang, 4)  # 最多降到受制档

    return {
        'shouzhi_type': chong_type,
        'jushang': jushang,
        'jiang_dang': jiang,
    }


if __name__ == '__main__':
    print('=== L2-4受制折减测试 ===')
    print()

    # 盘1: 庚金被冲(R-GENG-002)
    r1 = check_shouzhi('庚', ['申', '寅', '子', '辰'], {'hehui': []})
    print(f'庚金被冲盘: {r1}')

    # 盘2: 非中神受冲盘
    r2 = check_shouzhi('甲', ['子', '午', '卯', '酉'], {'hehui': []})
    print(f'非中神受冲盘: {r2}')

    # 盘3: 局伤盘(C5)
    r3 = check_shouzhi('丙', ['寅', '午', '戌', '子'], {'hehui': [{'status': '局伤'}]})
    print(f'局伤盘: {r3}')
