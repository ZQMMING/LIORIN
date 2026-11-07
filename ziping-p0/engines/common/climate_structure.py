# -*- coding: utf-8 -*-
"""气候结构事实层(寒暖燥湿) · task#49

只做客观干支结构判定, 不做调候用神/吉凶/强弱总裁决:
  - 季节(月令) + 火(暖)/水(寒)/燥土(戌未)/湿土(辰丑) 的客观计数;
  - 寒/暖/燥/湿 四性离散枚举(无/微/成势/极), 多态可共存(矛盾共存不裁);
  - 结构标签: 虚湿寒土(湿泥寒冻反从旺水)、火炎土燥、金寒水冷 等。

边界:
  - 调候"应取何干/干在何位"已由 qtbj_climate_candidates/presence 负责, 本层不重复查表;
  - 程度阈值为离散结构归类(# PCT-MARK), 非连续评分; 不输出 score/百分比/STRONG/WEAK/用神/吉凶;
  - 虚湿/燥烈只标结构前提, 是否翻转格局由 special_pattern 从严读为 CANDIDATE, 本层不下从格结论。

原典依据:
  《穷通宝鉴》十干十二月令以寒暖燥湿定调候先后;
  《滴天髓·寒暖燥湿论》"天道有寒暖, 发育万物, 人道得之, 不可过也";
  湿土(辰丑)寒冻不生、燥土(戌未)燥烈不润; 虚湿寒土无火反从旺水(任注"一见火则财多身弱")。
"""
from typing import Any, Dict, List

GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
          '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
BRANCH_WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火', '午': '火',
             '申': '金', '酉': '金', '辰': '土', '戌': '土', '丑': '土', '未': '土'}
# 地支本气干
BRANCH_BEN_GAN = {'子': '癸', '丑': '己', '寅': '甲', '卯': '乙', '辰': '戊', '巳': '丙',
                  '午': '丁', '未': '己', '申': '庚', '酉': '辛', '戌': '戊', '亥': '壬'}
WINTER = ('亥', '子', '丑')
SUMMER = ('巳', '午', '未')
SPRING = ('寅', '卯', '辰')
AUTUMN = ('申', '酉', '戌')
SHI_TU = ('辰', '丑')   # 湿土(寒/湿)
ZAO_TU = ('戌', '未')   # 燥土(燥/暖)
HUO_BEN = ('巳', '午')  # 火本气支
SHUI_BEN = ('亥', '子')  # 水本气支
PILLAR_KEYS = ('year', 'month', 'day', 'hour')

# 离散程度
NONE_LV = '无'
LIGHT_LV = '微'
STRONG_LV = '成势'
EXTREME_LV = '极'


def build_climate_structure(pillars: Dict[str, list], facts: Dict[str, Any] = None,
                            tian_he: Dict[str, Any] = None) -> Dict[str, Any]:
    """只读四柱客观判定寒暖燥湿结构。facts/tian_he 可选(用于三会三合水/火局)。"""
    facts = facts or {}
    dm = facts.get('day_stem') or pillars['day'][0]
    dm_wx = GAN_WX.get(dm)
    mb = facts.get('month_branch') or pillars['month'][1]

    if mb in WINTER:
        season = '冬'
    elif mb in SUMMER:
        season = '夏'
    elif mb in SPRING:
        season = '春'
    else:
        season = '秋'

    branches = [pillars[k][1] for k in PILLAR_KEYS]
    stems = [pillars[k][0] for k in ('year', 'month', 'hour')]  # 透干(不含日干)

    huo_ben = sum(1 for z in branches if z in HUO_BEN)          # 火本气支(巳午)
    shui_ben = sum(1 for z in branches if z in SHUI_BEN)        # 水本气支(亥子)
    huo_stem = sum(1 for g in stems if GAN_WX.get(g) == '火')   # 丙丁透
    shui_stem = sum(1 for g in stems if GAN_WX.get(g) == '水')  # 壬癸透
    zao_tu = sum(1 for z in branches if z in ZAO_TU)            # 戌未
    shi_tu = sum(1 for z in branches if z in SHI_TU)            # 辰丑

    # 三会/三合水/火局(化神寒暖)
    ju_water = ju_fire = False
    cf = facts.get('combination_facts', {}) or {}
    for it in (cf.get('sanhe', []) or []) + (cf.get('sanhui', []) or []):
        s = str(it)
        if s.endswith('水') or ('水' in s and ('合水' in s or '会水' in s)):
            ju_water = True
        if s.endswith('火') or ('火' in s and ('合火' in s or '会火' in s)):
            ju_fire = True
    if tian_he:
        for ju in (tian_he.get('sanhe_ju', []) or []) + (tian_he.get('sanhui_ju', []) or []):
            w = ju.get('wuxing') if isinstance(ju, dict) else None
            if w == '水':
                ju_water = True
            if w == '火':
                ju_fire = True

    huo_wu = (huo_ben == 0 and huo_stem == 0)     # 火全无(本气支+透干)
    shui_wu = (shui_ben == 0 and shui_stem == 0)  # 水全无
    huo_cheng = ju_fire or huo_ben >= 2 or (season == '夏' and (huo_ben >= 1 or huo_stem >= 1))
    shui_cheng = ju_water or shui_ben >= 2 or (season == '冬' and (shui_ben >= 1 or shui_stem >= 1))

    def lv(cheng, ji, you):
        if ji:
            return EXTREME_LV
        if cheng:
            return STRONG_LV
        if you:
            return LIGHT_LV
        return NONE_LV

    # 寒: 冬令/水成势; 极=水成势而火全无
    cold = lv(shui_cheng or season == '冬',
              shui_cheng and huo_wu,
              shui_ben >= 1 or shui_stem >= 1 or season == '冬')
    # 暖(热): 夏令/火成势; 极=火成势而水全无
    hot = lv(huo_cheng or season == '夏',
             huo_cheng and shui_wu,
             huo_ben >= 1 or huo_stem >= 1 or season == '夏')
    # 燥: 火+燥土; 成势=火成势且燥土>=1且水微/无
    dry_you = (huo_ben + huo_stem + zao_tu) >= 1
    dry_cheng = huo_cheng and zao_tu >= 1 and shui_ben == 0
    dry = lv(dry_cheng, dry_cheng and shui_wu, dry_you)
    # 湿: 水+湿土; 成势=水成势且湿土>=1且火微/无
    damp_you = (shui_ben + shui_stem + shi_tu) >= 1
    damp_cheng = shui_cheng and shi_tu >= 1 and huo_ben == 0
    damp = lv(damp_cheng, damp_cheng and huo_wu, damp_you)

    flags: List[str] = []
    detail: Dict[str, Any] = {}
    # 虚湿寒土: 日主土, 冬令/湿土当令, 水成势(财), 火全无(印绝) -> 湿泥寒冻不生、反从旺水(假从财前提)
    # 须无戌未燥土(火库藏丁丙能暖土); 原典'戌为火库,日主临之不致寒冻', 戌中丁火印在则财不能破印, 不假从
    if (dm_wx == '土' and (season == '冬' or mb in SHI_TU)
            and shui_cheng and huo_wu and shi_tu >= 1 and zao_tu == 0):
        flags.append('XU_SHI_HAN_TU')
        detail['XU_SHI_HAN_TU'] = {
            'name': '虚湿寒土(湿泥寒冻)',
            'condition': '日主土、冬令或辰丑湿土当令、水成势而火(印)全无',
            'effect_hint': '土虚湿寒冻不能用, 反顺旺水(财); 见火暖则土能任财转为财多身弱(条件性假从, 交special判CANDIDATE)',
        }
    # 火炎土燥: 火成势+燥土, 水全无 -> 偏枯须水润
    if huo_cheng and zao_tu >= 1 and shui_wu:
        flags.append('HUO_YAN_TU_ZAO')
        detail['HUO_YAN_TU_ZAO'] = {
            'name': '火炎土燥',
            'condition': '火成势、戌未燥土、水(润)全无',
            'effect_hint': '燥烈不润, 须水济; 只标结构, 用神交QTBJ',
        }
    # 金寒水冷: 日主金, 冬令, 水成势, 火全无 -> 金沉水冷须火暖
    if dm_wx == '金' and season == '冬' and shui_cheng and huo_wu:
        flags.append('JIN_HAN_SHUI_LENG')
        detail['JIN_HAN_SHUI_LENG'] = {
            'name': '金寒水冷',
            'condition': '日主金、冬令、水成势(泄气寒)、火(暖)全无',
            'effect_hint': '金寒水冷须火暖; 只标结构, 用神交QTBJ',
        }

    return {
        'module': 'CLIMATE_STRUCTURE',
        'patch': 'P160-CLIMATE-STRUCT',
        'namespace': 'climate.structure',
        'day_stem': dm,
        'daymaster_element': dm_wx,
        'month_branch': mb,
        'season': season,
        'sizhu': {'cold': cold, 'hot': hot, 'dry': dry, 'damp': damp},
        'counts': {
            'huo_ben_branch': huo_ben, 'huo_stem': huo_stem,
            'shui_ben_branch': shui_ben, 'shui_stem': shui_stem,
            'zao_tu_branch': zao_tu, 'shi_tu_branch': shi_tu,
            'ju_water': ju_water, 'ju_fire': ju_fire,
        },
        'structure_flags': flags,
        'flag_detail': detail,
        'judgment_status': 'CLIMATE_STRUCTURE_ONLY',
        'boundary_note': (
            '客观寒暖燥湿结构事实(季节+火水燥湿土计数+四性离散枚举+虚湿/燥烈/金寒标签); '
            '程度为离散归类(# PCT-MARK)非连续评分; 矛盾共存不裁; '
            '不判调候用神(交QTBJ)/身强弱/吉凶/从格成败(虚湿假从交special判CANDIDATE); 不接 production_entry'
        ),
    }
