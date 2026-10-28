# -*- coding: utf-8 -*-
"""
L3-3 格局成败检查实现
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import STEM_WUXING
from engines.common.pattern_rules import GOOD_SPIRIT_RULES, BAD_SPIRIT_RULES


def check_pattern_success(pattern, four_stems, day_master):
    """
    格局成败检查
    返回: (成格/败格/待定, 原因)
    """
    # 善神格: 查破格物
    if pattern in GOOD_SPIRIT_RULES:
        rule = GOOD_SPIRIT_RULES[pattern]
        po_ge = []
        for po_name in rule['破格物']:
            po_wx = _pattern_to_wx(po_name, day_master)
            if _stem_has_wx(po_wx, four_stems):
                po_ge.append(po_name)
        if po_ge:
            return '败格', f'破格物: {po_ge}'
        return '成格', rule['成格条件']

    # 恶神格: 查救应物
    if pattern in BAD_SPIRIT_RULES:
        rule = BAD_SPIRIT_RULES[pattern]
        jiu_ying = []
        for jy_name in rule['救应物']:
            jy_wx = _pattern_to_wx(jy_name, day_master)
            if _stem_has_wx(jy_wx, four_stems):
                jiu_ying.append(jy_name)
        if jiu_ying:
            return '成格', f'救应: {jiu_ying}'
        return '败格', '无制化'

    return '待定', '非八格'


def _pattern_to_wx(pattern_name, day_master):
    """十神→五行"""
    dm_wx = STEM_WUXING[day_master]
    REL = {
        '比肩': dm_wx, '劫财': dm_wx,
        '食神': {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}[dm_wx],
        '伤官': {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}[dm_wx],
        '偏财': {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}[dm_wx],
        '正财': {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}[dm_wx],
        '七杀': {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}[dm_wx],
        '正官': {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}[dm_wx],
        '偏印': {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}[dm_wx],
        '正印': {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}[dm_wx],
    }
    return REL.get(pattern_name, '')


def _stem_has_wx(target_wx, four_stems):
    """检查天干是否有某五行"""
    for stem in four_stems:
        if STEM_WUXING.get(stem) == target_wx:
            return True
    return False


if __name__ == '__main__':
    # 测试: 正官格(甲日主, 金为正官)
    # 破格: 伤官(火)
    status, reason = check_pattern_success('正官', ['甲', '丁', '戊', '壬'], '甲')
    print(f'正官格+伤官透: {status} ({reason})')

    # 七杀格(甲日主, 金为七杀)
    # 成格: 有食神(火)制杀
    status, reason = check_pattern_success('七杀', ['甲', '丙', '戊', '壬'], '甲')
    print(f'七杀格+食神透: {status} ({reason})')
