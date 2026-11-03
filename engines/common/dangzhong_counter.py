# -*- coding: utf-8 -*-
"""
党众计数器(纯布尔枚举版)
修正: 去掉浮点累加, 改用布尔条件组合
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import BRANCH_CANGGAN, get_hehui_summary

WUXING_OF_STEM = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火',
    '戊': '土', '己': '土', '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}


def calc_dangzhong(branches: list, stems: list) -> dict:
    """
    党众计数器(纯布尔枚举)
    输出: {五行: {透干数, 本气根数, 中气根数, 合会状态}}
    """
    result = {
        wx: {
            'stem_count': 0,
            'ben_qi_root': 0,
            'zhong_qi_root': 0,
            'yu_qi_root': 0,
            'has_sanhui': False,
            'has_sanhe_full': False,
            'has_sanhe_half': False,
        }
        for wx in ['木', '火', '土', '金', '水']
    }

    # 1. 透干计数
    for s in stems:
        wx = WUXING_OF_STEM.get(s, '')
        if wx:
            result[wx]['stem_count'] += 1

    # 2. 地支藏干计数
    for b in branches:
        cg = BRANCH_CANGGAN.get(b, ['', '', ''])
        if cg[0]:
            wx = WUXING_OF_STEM.get(cg[0], '')
            if wx:
                result[wx]['ben_qi_root'] += 1
        if cg[1]:
            wx = WUXING_OF_STEM.get(cg[1], '')
            if wx:
                result[wx]['zhong_qi_root'] += 1
        if cg[2]:
            wx = WUXING_OF_STEM.get(cg[2], '')
            if wx:
                result[wx]['yu_qi_root'] += 1

    # 3. 合会状态(走汇总层)
    summary = get_hehui_summary(branches, stems)
    if summary['fang_wx']:
        result[summary['fang_wx']]['has_sanhui'] = True
    for h in summary['hehui']:
        if h['status'] == '全':
            result[h['hua']]['has_sanhe_full'] = True
        elif h['status'] == '半局':
            result[h['hua']]['has_sanhe_half'] = True

    return result


def is_dangzhong_strong(wx_data: dict) -> bool:
    """
    党众成势判定(纯布尔)
    条件: 透干≥2 OR (本气根≥2 AND (三会 OR 三合全))
    """
    if wx_data['stem_count'] >= 2:
        return True
    if wx_data['ben_qi_root'] >= 2 and (wx_data['has_sanhui'] or wx_data['has_sanhe_full']):
        return True
    return False


if __name__ == '__main__':
    branches = ['卯', '寅', '卯', '辰']
    stems = ['癸', '甲', '丁', '甲']
    dz = calc_dangzhong(branches, stems)
    print('木多火熄盘:', branches, stems)
    for wx, data in dz.items():
        strong = is_dangzhong_strong(data)
        print(f'  {wx}: 透干{data["stem_count"]} 本气{data["ben_qi_root"]} 成势={strong}')
