# -*- coding: utf-8 -*-
"""
L3-2 月令取格函数(两轮制完整版)
补丁①: 先正格, 无用走专旺
#038: 三合局全→跳第一轮(挂验⏸)
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import BRANCH_CANGGAN, SANHE


def extract_moon_structure(month_branch, four_stems, day_master, four_branches=None):
    """
    月令取格: 两轮制
    返回: (正格类型, 走第二轮原因)
      正格类型: '正官'/'七杀'/'正印'/'偏印'/'正财'/'偏财'/'食神'/'伤官'
      走第二轮原因: '三合局全(#038)' / '比劫不取格' / '藏干皆不透(TODO)' / None
    """
    # #038前置守卫: 三合局全→跳第一轮
    if four_branches and _is_sanhe_ju_full(four_branches, day_master):
        return None, '三合局全(#038挂验)'

    # 第一轮: 月令取正格
    canggan = BRANCH_CANGGAN.get(month_branch, [])
    if not canggan:
        return None, '月支无藏干'

    # ①本气透干
    ben_qi = canggan[0]
    if ben_qi in four_stems:
        pattern = _stem_to_pattern(ben_qi, day_master)
        if pattern in ['比肩', '劫财']:
            # 比劫不取格, 走第二轮
            return None, '比劫不取格'
        return pattern, None

    # ②藏干透干(本气不透时)
    for cg in canggan[1:]:  # 跳过本气(已查)
        if cg in four_stems:
            pattern = _stem_to_pattern(cg, day_master)
            if pattern in ['比肩', '劫财']:
                continue  # 比劫跳过, 查下一个
            return pattern, None

    # ④皆不透(TODO: 人元轻重较量)
    return None, '藏干皆不透(TODO)'


def _is_sanhe_ju_full(branches, day_master):
    """#038守卫: 三合成局全+日主=局神"""
    dm_wx = _stem_wx(day_master)
    # SANHE格式: ((支1,支2,支3), 五行)
    for ju_branches, ju_wx in SANHE:
        if set(ju_branches).issubset(set(branches)):
            if ju_wx == dm_wx:
                return True
    return False


def _stem_to_pattern(stem, day_master):
    """天干→格局类型(十神)"""
    WUXING_REL = {
        '木': {'木': '比肩', '火': '食神', '土': '正财', '金': '正官', '水': '正印'},
        '火': {'木': '正印', '火': '比肩', '土': '食神', '金': '偏财', '水': '七杀'},
        '土': {'木': '正官', '火': '正印', '土': '比肩', '金': '食神', '水': '偏财'},
        '金': {'木': '正财', '火': '七杀', '土': '正印', '金': '比肩', '水': '伤官'},
        '水': {'木': '伤官', '火': '正财', '土': '正官', '金': '正印', '水': '比肩'},
    }
    stem_wx = _stem_wx(stem)
    dm_wx = _stem_wx(day_master)
    return WUXING_REL[dm_wx][stem_wx]


def _stem_wx(stem):
    """天干→五行"""
    table = {
        '甲': '木', '乙': '木',
        '丙': '火', '丁': '火',
        '戊': '土', '己': '土',
        '庚': '金', '辛': '金',
        '壬': '水', '癸': '水',
    }
    return table.get(stem, '')


if __name__ == '__main__':
    print('=== 验收矩阵 ===')
    print()

    # 盘①: 甲寅乙亥乙卯癸未 (亥卯未+寅)
    pattern, reason = extract_moon_structure(
        '亥', ['甲', '乙', '乙', '癸'], '乙',
        ['寅', '亥', '卯', '未']
    )
    print(f'盘①(亥卯未+寅): 正格={pattern}, 走第二轮={reason}')
    print(f'  期望: 三合局全(#038)→专旺→曲直')
    print()

    # 盘A: 亥月乙日主, 无亥卯未全, 透壬→正印格
    # 造盘: 壬寅 辛亥 乙酉 丁亥 (地支寅亥酉亥, 无卯未)
    pattern, reason = extract_moon_structure(
        '亥', ['壬', '辛', '乙', '丁'], '乙',
        ['寅', '亥', '酉', '亥']
    )
    print(f'盘A(寅亥酉亥): 正格={pattern}, 走第二轮={reason}')
    print(f'  期望: 亥藏壬甲, 壬透→正印格')
    print()

    # 盘B: 亥月乙日主, 只透甲(比劫)不透壬
    # 造盘: 甲寅 乙亥 乙酉 丁亥 (地支寅亥酉亥)
    pattern, reason = extract_moon_structure(
        '亥', ['甲', '乙', '乙', '丁'], '乙',
        ['寅', '亥', '酉', '亥']
    )
    print(f'盘B(只透甲): 正格={pattern}, 走第二轮={reason}')
    print(f'  期望: 甲比劫跳过, 壬不透→④TODO→走第二轮')
