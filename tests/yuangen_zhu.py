# -*- coding: utf-8 -*-
"""按原典要件造盘器 —— 让矩阵断言不依赖手写柱(手写柱易错十神, 致断言失真).

用法: mk(dm='甲', month_tg='正官', gan_tgs=('正印','偏财')) -> '乙丑 戊子 甲子 戊辰' 形态的柱串
  dm        : 日干
  month_tg  : 月令十神(决定月支)
  gan_tgs  : 年/月/时干十神(按顺序; None=该位留同干)
  zhi_hint : 各支地支(默认按月令同五行组内择, 保证不引刑冲)
"""
from engines.common.l0_fact_builder import ten_god

# 月支 -> 本气干(与引擎 HIDDEN[月][0] 一致)
_ZHI_BEN = {'子': '癸', '丑': '己', '寅': '甲', '卯': '乙', '辰': '戊', '巳': '丙',
             '午': '丁', '未': '己', '申': '庚', '酉': '辛', '戌': '戊', '亥': '壬'}
# 月令十神 -> 候选月支(按引擎月令本气十神推出的月支)
_MONTH_BY_TG = {
    '比肩': ['寅', '午', '戌', '丑', '未', '卯', '辰'],   # 阳干禄/阳干刃/阴干同五行
    '劫财': ['寅', '午', '戌', '卯', '辰', '丑', '未', '酉'],   # 酉中辛=庚之劫财(阳刃位)
    # 阳干羊刃位(PZZQ/DTS 阳刃格): 甲刃卯/丙刃午/戊刃午/庚刃酉/壬刃子
    '阳刃': ['卯', '午', '酉', '子'],
    '食神': ['午', '巳', '申', '辰', '戌', '丑', '未'],
    '伤官': ['巳', '午', '寅', '戌', '丑', '未', '辰'],
    '偏财': ['未', '戌', '辰', '丑', '申', '巳', '午'],
    '正财': ['丑', '未', '辰', '戌', '酉', '未', '巳'],
    '七杀': ['子', '午', '申', '戌', '寅', '巳', '亥'],
    '正官': ['酉', '子', '丑', '未', '辰', '戌', '卯'],
    '偏印': ['子', '午', '申', '戌', '寅', '巳', '亥'],
    '正印': ['亥', '子', '丑', '未', '辰', '戌', '卯'],
}


def gan_for_tg(dm, tg):
    """找与日干构成指定十神的天干."""
    for g in '甲乙丙丁戊己庚辛壬癸':
        if ten_god(dm, g) == tg:
            return g
    return None


def zhi_for_tg(dm, tg, used=()):
    """找与日干构成指定十神、且本气为该十神的地支(月令用)."""
    for z in _MONTH_BY_TG.get(tg, []):
        if z in used:
            continue
        if ten_god(dm, _ZHI_BEN[z]) == tg:
            return z
    return None


# 六冲对(用于造盘时避开冲破——PZZQ L1113「又无刑冲破害」方成格)
_CHONG = [('子', '午'), ('午', '子'), ('丑', '未'), ('未', '丑'), ('寅', '申'),
          ('申', '寅'), ('卯', '酉'), ('酉', '卯'), ('辰', '戌'), ('戌', '辰'),
          ('巳', '亥'), ('亥', '巳')]


def _safe_with(z, used):
    """z 与 used 中任一支不构成六冲方可."""
    for u in used:
        if (z, u) in _CHONG:
            return False
    return True


def mk_raw(bz):
    """直接由四柱串造盘(用于需精确指定干支者)."""
    ps = bz.split()
    p = {'year': [ps[0][0], ps[0][1]], 'month': [ps[1][0], ps[1][1]],
         'day': [ps[2][0], ps[2][1]], 'hour': [ps[3][0], ps[3][1]]}
    return bz, p


def mk(dm='甲', month_tg='正官', gan_tgs=('正印', None, '偏财'), zhis=None, day_zhi=None):
    """按要件造盘. 返回 (bazi字符串, pillars dict).
    gan_tgs: (年干十神, 月干十神, 时干十神) —— 月干默认与年干同.
    zhis    : (年支, 月支, 日支, 时支) —— None 则按月令同组择(避刑冲).
    ★ 造盘须避六冲(PZZQ L1113「又无刑冲破害, 官格成也」) —— 冲则不成格, 断言方有效.
    """
    mz = None
    # month_tg='阳刃' 为伪键: 阳刃位以支论(戊刃午/庚刃酉...), 非月支本气十神
    if month_tg == '阳刃':
        _dmyan = {'甲': '卯', '丙': '午', '戊': '午', '庚': '酉', '壬': '子'}
        mz = _dmyan.get(dm)
        if mz is None:
            raise ValueError("日干 %s 无阳刃位" % dm)
    else:
        for z in _MONTH_BY_TG.get(month_tg, []):
            if ten_god(dm, _ZHI_BEN[z]) == month_tg:
                mz = z
                break
    # zhis 显式指定时, 以指定的月支为准(十神须与 month_tg 一致, 不一致则报错; 阳刃位除外)
    if zhis:
        _mz_spec = zhis[1]
        if month_tg == '阳刃':
            mz = _mz_spec
        else:
            _tg_spec = ten_god(dm, _ZHI_BEN[_mz_spec])
            if _tg_spec != month_tg:
                raise ValueError("指定月支 %s 对 %s 为 %s, 与要件 %s 不符" % (
                    _mz_spec, dm, _tg_spec, month_tg))
            mz = _mz_spec
    if mz is None:
        raise ValueError("无月支可作 %s 之 %s" % (dm, month_tg))
    y_g = gan_for_tg(dm, gan_tgs[0]) or dm
    m_g = gan_for_tg(dm, gan_tgs[1]) if gan_tgs[1] else y_g
    h_g = gan_for_tg(dm, gan_tgs[2]) or dm
    if zhis:
        y_z, _, d_z, h_z = zhis
    else:
        pool = [z for z in _MONTH_BY_TG.get(month_tg, []) if z != mz]
        # 日支: 不与月支相冲
        d_z = next((z for z in pool if _safe_with(z, (mz,))), mz)
        rest = [z for z in pool if z != d_z]
        y_z = next((z for z in rest if _safe_with(z, (mz, d_z))), mz)
        rest2 = [z for z in rest if z != y_z]
        h_z = next((z for z in rest2 if _safe_with(z, (mz, d_z, y_z))), mz)
    if day_zhi:
        d_z = day_zhi
    bz = "%s%s %s%s %s%s %s%s" % (y_g, y_z, m_g, mz, dm, d_z, h_g, h_z)
    p = {'year': [y_g, y_z], 'month': [m_g, mz], 'day': [dm, d_z], 'hour': [h_g, h_z]}
    return bz, p
