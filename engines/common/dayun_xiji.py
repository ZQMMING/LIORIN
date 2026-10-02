# -*- coding: utf-8 -*-
"""大运喜忌结构层 V4.65（已冻结）

【大运分看多模式标注】
六部经典对大运干支分看存在四种互补模式，本层默认采用模式C（滴天髓十年一体），
其他模式保留为后续独立刀，不强行统一：

  模式A（渊海子平）：大运重支轻干，流年重干轻支，不分前后五年
  模式B（三命通会）：前五年干兼支，后五年弃干看支
  模式C（滴天髓）  ：十年一体，盖头截脚修正
  模式D（命理约言）：否定分看

注意：《渊海子平》原书主张"大运重支轻干"，并非"前五年天干后五年地支"。
"前五年干兼支、后五年弃干"是《三命通会》的说法，两者不可混淆。

未来接入真实八字排盘引擎处理用户真实案例时，需实现模式B（干支分看）。
当前用原著案例学习调试时暂采用模式C（十年一体）。
"""

from typing import Dict, List, Any
from spec.yinyang_system import SHENG, KE, SHENG_ME, KE_ME
import re

WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}




# 五合表 (天干 -> 合化五行)
WU_HE = {
    '甲': ('土', '己'), '己': ('土', '甲'),
    '乙': ('金', '庚'), '庚': ('金', '乙'),
    '丙': ('水', '辛'), '辛': ('水', '丙'),
    '丁': ('木', '壬'), '壬': ('木', '丁'),
    '戊': ('火', '癸'), '癸': ('火', '戊'),
}

# 三合表 (每个三合局: (地支1, 地支2, 地支3, 合化五行))
SAN_HE = [
    ('亥', '卯', '未', '木'),
    ('寅', '午', '戌', '火'),
    ('申', '子', '辰', '水'),
    ('巳', '酉', '丑', '金'),
]

# 三会表 (每个三会局: (地支1, 地支2, 地支3, 合化五行))
SAN_HUI = [
    ('寅', '卯', '辰', '木'),
    ('巳', '午', '未', '火'),
    ('申', '酉', '戌', '金'),
    ('亥', '子', '丑', '水'),
]

# 半合表 (每个半合局: (地支1, 地支2, 合化五行))
BAN_HE = [
    ('申', '子', '水'), ('子', '辰', '水'),
    ('寅', '午', '火'), ('午', '戌', '火'),
    ('亥', '卯', '木'), ('卯', '未', '木'),
    ('巳', '酉', '金'), ('酉', '丑', '金'),
]

# 六害表
LIU_HAI = {
    '子': '未', '未': '子',
    '丑': '午', '午': '丑',
    '寅': '巳', '巳': '寅',
    '卯': '辰', '辰': '卯',
    '申': '亥', '亥': '申',
    '酉': '戌', '戌': '酉',
}

# 三刑表 (地支 -> 刑的地支列表)
SAN_XING = {
    '寅': ['巳', '申'], '巳': ['寅', '申'], '申': ['寅', '巳'],
    '丑': ['戌', '未'], '戌': ['丑', '未'], '未': ['丑', '戌'],
    '子': ['卯'], '卯': ['子'],
    '辰': ['午', '酉', '亥'], '午': ['辰', '酉', '亥'],
    '酉': ['辰', '午', '亥'], '亥': ['辰', '午', '酉'],
}

# 六冲表
LIU_CHONG = {
    '子':'午', '午':'子',
    '丑':'未', '未':'丑',
    '寅':'申', '申':'寅',
    '卯':'酉', '酉':'卯',
    '辰':'戌', '戌':'辰',
    '巳':'亥', '亥':'巳',
}

# 六合表 (地支 -> (合化五行, 合化地支对))
LIU_HE = {
    '子': ('土', '丑'), '丑': ('土', '子'),
    '寅': ('木', '亥'), '亥': ('木', '寅'),
    '卯': ('火', '戌'), '戌': ('火', '卯'),
    '辰': ('金', '酉'), '酉': ('金', '辰'),
    '巳': ('水', '申'), '申': ('水', '巳'),
    '午': ('土', '未'), '未': ('土', '午'),
}

# 2026-09-30: 藏干表改读 LIORIN 权威源（engines.l0_paipan），本仓不再维护独立副本。
from engines.l0_paipan import branch_hidden_stems as _bhs

# 地支藏干表 (地支 -> 藏干列表, 按本气/中气/余气顺序)
# 2026-09-30: 改读 LIORIN 权威源（engines.l0_paipan）。
#   原硬编码 '巳':['丙','庚','戊'] 中气/余气颠倒（应 丙本/戊中/庚余）。
HIDDEN_STEMS = _bhs()

# 十神映射 (日主五行 -> 十神)
def get_ten_god(dm_gan: str, gz: str) -> str:
    """根据日主天干和大运干支, 返回十神(中文)."""
    dmw = WX[dm_gan]
    gan = gz[0]
    gan_wx = WX[gan]
    dm_yang = dm_gan in '甲丙戊庚壬'
    gan_yang = gan in '甲丙戊庚壬'
    if gan_wx == dmw:
        return '比肩' if (dm_yang == gan_yang) else '劫财'
    elif SHENG.get(gan_wx) == dmw:
        return '正印' if (dm_yang != gan_yang) else '偏印'
    elif SHENG.get(dmw) == gan_wx:
        return '伤官' if (dm_yang != gan_yang) else '食神'
    elif KE.get(dmw) == gan_wx:
        return '正财' if (dm_yang != gan_yang) else '偏财'
    elif KE_ME.get(dmw) == gan_wx:
        return '正官' if (dm_yang != gan_yang) else '七杀'
    return '未知'


def build_dayun_xiji(
    pillars: Dict[str, list],
    yongshen_result: Dict[str, Any],
    dayun_list: List[str],
    wpo: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """大运应期喜忌结构层.
    
    输入:
        pillars: 原局四柱
        yongshen_result: 用神引擎输出 (含primary/secondary/avoid)
        dayun_list: 大运列表 ['丙申','乙未',...]
    
    输出:
        per_step: 每个大运的喜忌结构
        boundary_note: 边界说明
    """
    dm = pillars['day'][0]
    dmw = WX[dm]
    
    primary = yongshen_result.get('yongshen_primary') or ''
    secondary = yongshen_result.get('yongshen_secondary') or []
    avoid = yongshen_result.get('yongshen_avoid') or []
    climate_stem_candidates = yongshen_result.get('climate_stem_candidates') or []  # V7.23 PATCH: 十干级调候候选
    
    # V3.3: 计算用神的十神类型(通过日主天干和用神五行)
    primary_ten_god_type = ''
    if primary and dm:
        dmw = WX.get(dm, '')
        primary_wx = primary
        dm_yang = dm in '甲丙戊庚壬'
        if primary_wx == dmw:
            primary_ten_god_type = '比劫'
        elif SHENG.get(primary_wx) == dmw:
            primary_ten_god_type = '印'
        elif SHENG.get(dmw) == primary_wx:
            primary_ten_god_type = '食伤'
        elif KE.get(dmw) == primary_wx:
            primary_ten_god_type = '财'
        elif KE_ME.get(dmw) == primary_wx:
            primary_ten_god_type = '官杀'
    
    # V2.7: 用神强弱布尔枚举(替代评分加权primary_power_ratio)
    # 用神弱 = 用神无根 且 用神无透干 (原典: 无根无透则力弱)
    primary_weak_bool = False
    if wpo and 'wuxing_power' in wpo and primary:
        wp = wpo['wuxing_power']
        pdata = wp.get(primary, {})
        primary_has_root = pdata.get('ben_n', 0) + pdata.get('zhong_n', 0) + pdata.get('yu_n', 0) > 0
        primary_has_stem = pdata.get('stem_n', 0) > 0
        primary_weak_bool = (not primary_has_root) and (not primary_has_stem)
    
    # V3.8: 格局层面喜忌判断 (基于子平真诠各格局取运规则)
    # 判断伤官佩印格: 月令伤官 + 印星透干有根
    month_branch_main = pillars['month'][1]
    month_hidden = HIDDEN_STEMS.get(month_branch_main, [])
    # 月令本气对应的十神
    dm_wx_local = WX.get(dm, '')
    month_benqi = month_hidden[0] if month_hidden else ''
    month_benqi_wx = WX.get(month_benqi, '')
    # 判断月令是否是伤官(日主生的异性五行)
    is_shangguan_month = False
    if month_benqi_wx and dm_wx_local:
        # 伤官: 日主生的异性五行 (如甲木生丁火=伤官, 甲木生丙火=食神)
        if SHENG.get(dm_wx_local) == month_benqi_wx:
            dm_yang = dm in '甲丙戊庚壬'
            mb_yang = month_benqi in '甲丙戊庚壬'
            if dm_yang != mb_yang:  # 异性=伤官
                is_shangguan_month = True
    # 判断印星是否透干有根
    yin_stems = []
    yin_wx = SHENG_ME.get(dm_wx_local, '')  # 生日主的五行=印
    for pos in ['year', 'month', 'day', 'hour']:
        stem = pillars[pos][0]
        if WX.get(stem, '') == yin_wx:
            yin_stems.append(stem)
    # 印星有根: 地支中有印星五行的藏干
    yin_has_root = False
    for pos in ['year', 'month', 'day', 'hour']:
        branch = pillars[pos][1]
        hidden = HIDDEN_STEMS.get(branch, [])
        for h in hidden:
            if WX.get(h, '') == yin_wx:
                yin_has_root = True
                break
        if yin_has_root:
            break
    is_shangguan_peiyin = is_shangguan_month and len(yin_stems) > 0 and yin_has_root
    
    # V4.2: 从格喜忌判断 (基于滴天髓从象: 从格喜顺势, 忌生扶日主)
    # 从格类型: 从财格/从杀格/从官格/从儿格/从势格
    special_name = yongshen_result.get('special', '') or ''
    is_cong_ge = any(cong_type in special_name for cong_type in ['从财格', '从杀格', '从官格', '从儿格', '从势格'])
    # V4.3: 专旺格喜忌判断 (基于滴天髓一行得气: 专旺格喜顺势, 忌克泄)
    # 专旺格类型: 曲直格(木)/炎上格(火)/稼穡格(土)/从革格(金)/润下格(水)
    zhuanwang_names = {'曲直格': '木', '炎上格': '火', '稼穡格': '土', '从革格': '金', '润下格': '水'}
    zhuanwang_wx = ''
    for zn_name, zn_wx in zhuanwang_names.items():
        if zn_name in special_name:
            zhuanwang_wx = zn_wx
            break
    is_zhuanwang = bool(zhuanwang_wx)
    is_huaqi_ge = '化气格' in special_name
    # V4.4: 化气格喜忌判断 (基于滴天髓化象: 化气格喜化神旺地, 忌克化神)
    # 化气格类型: 化土气格/化金气格/化水气格/化木气格/化火气格
    huaqi_match = re.search(r'化([金木水火土])气格', special_name)
    huaqi_wx = huaqi_match.group(1) if huaqi_match else ''
    is_huaqi = bool(huaqi_wx)
    # V4.5: 两气格喜忌判断 (基于滴天髓两气成象: 两气格喜两行旺地, 忌克泄两行)
    # 两气格类型: 两气成象(木火)/两气成象(火土)/两气成象(土金)/两气成象(金水)/两气成象(水木)
    liangqi_match = re.search(r'两气成象\(([金木水火土])([金木水火土])\)', special_name)
    liangqi_wuxing = [liangqi_match.group(1), liangqi_match.group(2)] if liangqi_match else []
    is_liangqi = len(liangqi_wuxing) == 2
    # 两气格喜忌: 喜两行的五行, 忌克两行的五行
    # 化气格喜忌: 喜化神五行+生化神的五行, 忌克化神的五行+化神克的五行
    # 专旺格喜忌: 喜专旺五行+生专旺的五行, 忌克专旺的五行+专旺克的五行
    # 从格喜忌: 喜从神的旺地, 忌生扶日主的运(比劫+印)
    # 从财格: 喜财+食伤, 忌比劫+印
    # 从杀格/从官格: 喜官杀+财, 忌比劫+印
    # 从儿格: 喜食伤+财, 忌印+比劫
    # 从势格: 喜顺势(最旺的五行), 忌比劫+印
    
    # V3.9: 其他格局判断 (基于子平真诠取运规则)
    # 正官格: 月令本气是正官(克日主的异性五行)
    is_zhengguan_month = False
    guan_wx = KE_ME.get(dm_wx_local, '')  # 克日主的五行=官杀
    if month_benqi_wx == guan_wx:
        dm_yang = dm in '甲丙戊庚壬'
        mb_yang = month_benqi in '甲丙戊庚壬'
        if dm_yang != mb_yang:  # 异性=正官
            is_zhengguan_month = True
    # 正官格用财: 财星透干有根
    cai_wx = KE.get(dm_wx_local, '')  # 日主克的五行=财
    cai_stems = []
    for pos in ['year', 'month', 'day', 'hour']:
        stem = pillars[pos][0]
        if WX.get(stem, '') == cai_wx:
            cai_stems.append(stem)
    cai_has_root = False
    for pos in ['year', 'month', 'day', 'hour']:
        branch = pillars[pos][1]
        hidden = HIDDEN_STEMS.get(branch, [])
        for h in hidden:
            if WX.get(h, '') == cai_wx:
                cai_has_root = True
                break
        if cai_has_root:
            break
    is_zhengguan_yongcai = is_zhengguan_month and len(cai_stems) > 0 and cai_has_root
    
    # 食神格: 月令本气是食神(日主生的同性五行)
    is_shishen_month = False
    if SHENG.get(dm_wx_local) == month_benqi_wx:
        dm_yang = dm in '甲丙戊庚壬'
        mb_yang = month_benqi in '甲丙戊庚壬'
        if dm_yang == mb_yang:  # 同性=食神
            is_shishen_month = True
    is_shishen_shengcai = is_shishen_month and len(cai_stems) > 0 and cai_has_root
    
    # 财格: 月令本气是财
    is_cai_month = (month_benqi_wx == cai_wx)
    # 财格生官: 官星透干有根
    guan_stems = []
    for pos in ['year', 'month', 'day', 'hour']:
        stem = pillars[pos][0]
        if WX.get(stem, '') == guan_wx:
            guan_stems.append(stem)
    guan_has_root = False
    for pos in ['year', 'month', 'day', 'hour']:
        branch = pillars[pos][1]
        hidden = HIDDEN_STEMS.get(branch, [])
        for h in hidden:
            if WX.get(h, '') == guan_wx:
                guan_has_root = True
                break
        if guan_has_root:
            break
    is_cai_shengguan = is_cai_month and len(guan_stems) > 0 and guan_has_root
    
    # 印格: 月令本气是印
    is_yin_month = (month_benqi_wx == yin_wx)
    # 印格用官: 官星透干有根
    is_yin_yongguan = is_yin_month and len(guan_stems) > 0 and guan_has_root
    
    # 阳刃格: 月令是阳刃(阳干的帝旺位)
    YANG_REN = {'甲':'卯', '丙':'午', '戊':'午', '庚':'酉', '壬':'子'}
    is_yangren_month = (dm in YANG_REN and month_branch_main == YANG_REN[dm])
    
    # V4.1: 七杀格(偏官格)判断
    # 七杀格: 月令本气是七杀(克日主的同性五行)
    is_qisha_month = False
    if month_benqi_wx == guan_wx:
        dm_yang = dm in '甲丙戊庚壬'
        mb_yang = month_benqi in '甲丙戊庚壬'
        if dm_yang == mb_yang:  # 同性=七杀
            is_qisha_month = True
    # 七杀格用食制: 食神透干有根
    shi_wx = SHENG.get(dm_wx_local, '')  # 日主生的五行=食伤
    shi_stems = []
    for pos in ['year', 'month', 'day', 'hour']:
        stem = pillars[pos][0]
        if WX.get(stem, '') == shi_wx:
            shi_stems.append(stem)
    shi_has_root = False
    for pos in ['year', 'month', 'day', 'hour']:
        branch = pillars[pos][1]
        hidden = HIDDEN_STEMS.get(branch, [])
        for h in hidden:
            if WX.get(h, '') == shi_wx:
                shi_has_root = True
                break
        if shi_has_root:
            break
    is_qisha_yongshi = is_qisha_month and len(shi_stems) > 0 and shi_has_root
    
    # 七杀格用印化: 印星透干有根
    is_qisha_yongyin = is_qisha_month and len(yin_stems) > 0 and yin_has_root
    
    # V4.1: 建禄月劫格判断
    # 建禄: 月令是日主的临官位
    LU_POS = {'甲':'寅', '乙':'卯', '丙':'巳', '丁':'午', '戊':'巳', '己':'午', '庚':'申', '辛':'酉', '壬':'亥', '癸':'子'}
    is_jianlu_month = (month_branch_main == LU_POS.get(dm, ''))
    # 月劫: 月令是日主的劫财位(阴干的帝旺位或阳干的禄位)
    JIE_POS = {'甲':'卯', '乙':'寅', '丙':'午', '丁':'巳', '戊':'午', '己':'巳', '庚':'酉', '辛':'申', '壬':'子', '癸':'亥'}
    is_yuejie_month = (month_branch_main == JIE_POS.get(dm, '')) and not is_jianlu_month
    is_jianlu_yuejie = is_jianlu_month or is_yuejie_month
    # 建禄月劫格用官: 官星透干有根
    is_jianlu_yongguan = is_jianlu_yuejie and len(guan_stems) > 0 and guan_has_root
    # 建禄月劫格用财: 财星透干有根 + 食伤透干
    is_jianlu_yongcai = is_jianlu_yuejie and len(cai_stems) > 0 and cai_has_root and len(shi_stems) > 0
    
    per_step = []
    for gz in dayun_list:
        gan = gz[0]
        zhi = gz[1]
        gan_wx = WX[gan]
        zhi_wx = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}.get(zhi, '')
        
        ten_god = get_ten_god(dm, gz)
        
        # 与用神/喜神/忌神的关系
        relations = []
        
        # 天干五行关系 (V3.6修复: 改为多个独立if判断, 允许同时具有多种关系属性)
        if gan_wx == primary:
            relations.append('GAN_PRIMARY')
        if gan_wx in secondary:
            relations.append('GAN_SECONDARY')
        if gan_wx in avoid:
            relations.append('GAN_AVOID')
        if SHENG.get(gan_wx) == primary:
            relations.append('GAN_SHENG_PRIMARY')  # 大运生用神
        if SHENG_ME.get(gan_wx) == primary:
            relations.append('GAN_PRIMARY_SHENG')  # 用神生大运(泄用神)
        if KE.get(gan_wx) == primary:
            relations.append('GAN_KE_PRIMARY')  # 大运克用神
        
        # V7.25 PATCH: 调候轨门控——从格/专旺格/化气格不调候
        # 原著依据: 《滴天髓》从象/专旺/化象章
        # 规则: 凡从格/专旺格/化气格, 以顺其气势为第一义, 调候轨不适用
        enable_tiaohou = not (is_cong_ge or is_zhuanwang or is_huaqi_ge)

        # V7.23 PATCH: 十干级调候匹配(EXACT_STEM vs ELEMENT_MATCH)
        stem_match_type = 'NONE'
        if climate_stem_candidates and enable_tiaohou:
            for c in climate_stem_candidates:
                if gan == c.get('stem'):
                    stem_match_type = 'EXACT_STEM'
                    relations.append('GAN_QTBJ_EXACT_STEM')
                    break
                elif gan_wx == c.get('element'):
                    stem_match_type = 'ELEMENT_MATCH'
                    relations.append('GAN_QTBJ_ELEMENT_MATCH')
                    # 不break, 继续检查是否有更精确的EXACT_STEM
        
        # 地支五行关系 (V3.6修复: 改为多个独立if判断)
        if zhi_wx == primary:
            relations.append('ZHI_PRIMARY')
        if zhi_wx in secondary:
            relations.append('ZHI_SECONDARY')
        if zhi_wx in avoid:
            relations.append('ZHI_AVOID')
        
        # V2.0: 大运藏干判断 (区分本气/中气/余气权重)
        zhi_hidden = HIDDEN_STEMS.get(zhi, [])
        zhi_hidden_wx = [WX.get(s, '') for s in zhi_hidden]
        # 本气(第1个)权重最高, 中气(第2个)次之, 余气(第3个)最小
        if len(zhi_hidden_wx) >= 1 and zhi_hidden_wx[0] == primary:
            relations.append('ZHI_HIDDEN_BENQI_PRIMARY')  # 大运藏干本气是用神, 喜(强)
        elif len(zhi_hidden_wx) >= 2 and zhi_hidden_wx[1] == primary:
            relations.append('ZHI_HIDDEN_ZHONGQI_PRIMARY')  # 大运藏干中气是用神, 喜(中)
        elif len(zhi_hidden_wx) >= 3 and zhi_hidden_wx[2] == primary:
            relations.append('ZHI_HIDDEN_YUQI_PRIMARY')  # 大运藏干余气是用神, 喜(弱)
        if avoid:
            if len(zhi_hidden_wx) >= 1 and zhi_hidden_wx[0] == avoid[0]:
                relations.append('ZHI_HIDDEN_BENQI_AVOID')  # 大运藏干本气是忌神, 忌(强)
            elif len(zhi_hidden_wx) >= 2 and zhi_hidden_wx[1] == avoid[0]:
                relations.append('ZHI_HIDDEN_ZHONGQI_AVOID')  # 大运藏干中气是忌神, 忌(中)
            elif len(zhi_hidden_wx) >= 3 and zhi_hidden_wx[2] == avoid[0]:
                relations.append('ZHI_HIDDEN_YUQI_AVOID')  # 大运藏干余气是忌神, 忌(弱)
        
        # V4.43: 截脚/盖头判断 (原典: 忌神被截脚无力反转为喜, 用神被盖头无力反转为忌)
        # 改调统一边表判定函数（收编：单一定义源）
        from spec.node_system import is_gaitou, is_jiejiao as _is_jiejiao
        is_jiejiao = _is_jiejiao(gan_wx, zhi_wx)
        is_gaitou = is_gaitou(gan_wx, zhi_wx)
        if is_jiejiao:
            relations.append('GAN_JIEJIAO')  # 天干被截脚, 力量大减
        if is_gaitou:
            relations.append('ZHI_GAITOU')  # 地支被盖头, 力量大减
        
        # V1.1: 五合判断 (大运天干与原局天干五合)
        wuhe_info = WU_HE.get(gan, ('', ''))
        wuhe_huashen = wuhe_info[0]
        wuhe_target = wuhe_info[1]
        original_stems = [pillars[k][0] for k in ['year', 'month', 'day', 'hour']]
        if wuhe_target and wuhe_target in original_stems:
            relations.append(f'GAN_WUHE_{wuhe_target}')
            if wuhe_huashen == primary:
                relations.append('WUHE_PRIMARY')  # 合化用神, 喜
        
        # V1.2: 三合判断 (大运地支与原局两个地支形成三合局)
        original_branches = [pillars[k][1] for k in ['year', 'month', 'day', 'hour']]
        for sanhe in SAN_HE:
            b1, b2, b3, huashen = sanhe
            sanhe_branches = {b1, b2, b3}
            # 大运地支是否在三合局中
            if zhi in sanhe_branches:
                # 原局地支是否包含另外两个
                other_two = sanhe_branches - {zhi}
                if other_two.issubset(set(original_branches)):
                    relations.append(f'ZHI_SANHE_{b1}{b2}{b3}')
                    if huashen == primary:
                        relations.append('SANHE_PRIMARY')  # 三合化用神, 喜
        
        # V2.2: 三会判断 (大运地支与原局两个地支形成三会局)
        for sanhui in SAN_HUI:
            b1, b2, b3, huashen = sanhui
            sanhui_branches = {b1, b2, b3}
            if zhi in sanhui_branches:
                other_two = sanhui_branches - {zhi}
                if other_two.issubset(set(original_branches)):
                    relations.append(f'ZHI_SANHUI_{b1}{b2}{b3}')
                    if huashen == primary:
                        relations.append('SANHUI_PRIMARY')  # 三会化用神, 喜
        
        # V2.3: 半合判断 (大运地支与原局一个地支形成半合)
        for banhe in BAN_HE:
            b1, b2, huashen = banhe
            banhe_branches = {b1, b2}
            if zhi in banhe_branches:
                other_one = banhe_branches - {zhi}
                if other_one.issubset(set(original_branches)):
                    relations.append(f'ZHI_BANHE_{b1}{b2}')
                    if huashen == primary:
                        relations.append('BANHE_PRIMARY')  # 半合化用神, 喜
        
        # V2.4: 六害四支判断 (大运地支与原局任意地支六害)
        year_branch = pillars['year'][1]
        month_branch = pillars['month'][1]
        day_branch = pillars['day'][1]
        hour_branch = pillars['hour'][1]
        hai_target = LIU_HAI.get(zhi, '')
        for pos_name, pos_branch in [('YEAR', year_branch), ('MONTH', month_branch), ('DAY', day_branch), ('HOUR', hour_branch)]:
            if hai_target == pos_branch:
                relations.append(f'ZHI_HAI_{pos_name}')
                pos_branch_wx = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}.get(pos_branch, '')
                if pos_branch_wx == primary:
                    relations.append(f'HAI_{pos_name}_PRIMARY')  # 害该支用神根, 忌
        
        # V2.6: 三刑四支判断 (大运地支与原局任意地支三刑)
        xing_targets = SAN_XING.get(zhi, [])
        for pos_name, pos_branch in [('YEAR', year_branch), ('MONTH', month_branch), ('DAY', day_branch), ('HOUR', hour_branch)]:
            if pos_branch in xing_targets:
                relations.append(f'ZHI_XING_{pos_name}')
                pos_branch_wx = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}.get(pos_branch, '')
                if pos_branch_wx == primary:
                    relations.append(f'XING_{pos_name}_PRIMARY')  # 刑该支用神根, 忌
        
        # V1.4: 冲月令判断 (月令是最重要的地支, 冲月令影响大)
        month_branch = pillars['month'][1]
        chong_month_target = LIU_CHONG.get(zhi, '')
        if chong_month_target == month_branch:
            relations.append('ZHI_CHONG_MONTH')
            # 月令五行如果是用神, 冲月令则忌; 如果是忌神, 冲月令则喜
            month_branch_wx = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}.get(month_branch, '')
            if month_branch_wx == primary:
                relations.append('CHONG_MONTH_PRIMARY')  # 冲月令用神, 忌
            if avoid and month_branch_wx == avoid[0]:
                relations.append('CHONG_MONTH_AVOID')  # 冲月令忌神, 喜
        
        # V1.6: 冲日支判断 (日支是日主的根, 冲日支影响日主力量)
        day_branch = pillars['day'][1]
        chong_day_target = LIU_CHONG.get(zhi, '')
        if chong_day_target == day_branch:
            relations.append('ZHI_CHONG_DAY')
            day_branch_wx = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}.get(day_branch, '')
            if day_branch_wx == primary:
                relations.append('CHONG_DAY_PRIMARY')  # 冲日支用神根, 忌
            if avoid and day_branch_wx == avoid[0]:
                relations.append('CHONG_DAY_AVOID')  # 冲日支忌神根, 喜
        
        # V1.7: 冲年支/时支判断
        year_branch = pillars['year'][1]
        hour_branch = pillars['hour'][1]
        for pos_name, pos_branch in [('YEAR', year_branch), ('HOUR', hour_branch)]:
            chong_target = LIU_CHONG.get(zhi, '')
            if chong_target == pos_branch:
                relations.append(f'ZHI_CHONG_{pos_name}')
                pos_branch_wx = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}.get(pos_branch, '')
                if pos_branch_wx == primary:
                    relations.append(f'CHONG_{pos_name}_PRIMARY')  # 冲该支用神根, 忌
                if avoid and pos_branch_wx == avoid[0]:
                    relations.append(f'CHONG_{pos_name}_AVOID')  # 冲该支忌神根, 喜
        
        # V2.1: 六合四支判断 (大运地支与原局任意地支六合)
        he_info = LIU_HE.get(zhi, ('', ''))
        he_huashen = he_info[0]
        he_target = he_info[1]
        for pos_name, pos_branch in [('YEAR', year_branch), ('MONTH', month_branch), ('DAY', day_branch), ('HOUR', hour_branch)]:
            if he_target == pos_branch:
                relations.append(f'ZHI_HE_{pos_name}')
                if he_huashen == primary:
                    relations.append(f'HE_{pos_name}_PRIMARY')  # 合该支化用神, 喜
                if avoid and he_huashen == avoid[0]:
                    relations.append(f'HE_{pos_name}_AVOID')  # 合该支化忌神, 忌
        
        # 综合喜忌标签 (结构判断, 非吉凶)
        chong_primary_any = any('CHONG_' in r and '_PRIMARY' in r for r in relations)
        chong_avoid_any = any('CHONG_' in r and '_AVOID' in r for r in relations)
        hidden_primary_any = any('ZHI_HIDDEN_' in r and '_PRIMARY' in r for r in relations)
        hidden_avoid_any = any('ZHI_HIDDEN_' in r and '_AVOID' in r for r in relations)
        he_primary_any = any('HE_' in r and '_PRIMARY' in r for r in relations)
        he_avoid_any = any('HE_' in r and '_AVOID' in r for r in relations)
        hai_primary_any = any('HAI_' in r and '_PRIMARY' in r for r in relations)
        xing_primary_any = any('XING_' in r and '_PRIMARY' in r for r in relations)
        
        # V3.3: 十神关系判断 - 大运十神与用神十神的生克关系
        # V6.3: avoid优先级最高 - 大运五行在avoid中时不触发ten_god_xi(如L1808丙午火财在avoid中, 财生官杀不应判喜)
        ten_god_xi = False
        ten_god_ji = False
        _in_avoid_now = (gan_wx in avoid) or (zhi_wx in avoid)
        if primary_ten_god_type and ten_god != '未知' and not _in_avoid_now:
            # 十神生克关系: 比劫生食伤, 食伤生财, 财生官杀, 官杀生印, 印生比劫
            sheng_chain = {'比劫': '食伤', '食伤': '财', '财': '官杀', '官杀': '印', '印': '比劫'}
            ke_chain = {'比劫': '财', '财': '印', '印': '食伤', '食伤': '官杀', '官杀': '比劫'}
            # 大运十神生用神十神 -> 喜
            if sheng_chain.get(ten_god) == primary_ten_god_type:
                ten_god_xi = True
            # 大运十神克用神十神 -> 忌
            if ke_chain.get(ten_god) == primary_ten_god_type:
                ten_god_ji = True
        
        # V3.2: 多标签输出 - 一个大运可能同时具有多种喜忌属性
        # V3.8: 伤官佩印格中官星为喜 (官杀生印→印生身, 流通有情)
        shangguan_peiyin_guanxi = False
        if is_shangguan_peiyin:
            if gan_wx == guan_wx or zhi_wx == guan_wx:
                shangguan_peiyin_guanxi = True
        
        # V3.9: 其他格局层面喜忌判断
        pattern_xi = False
        pattern_ji = False
        # 正官格用财: 食伤为忌(食伤克官星)
        if is_zhengguan_yongcai:
            shishang_wx = SHENG.get(dm_wx_local, '')
            if gan_wx == shishang_wx or zhi_wx == shishang_wx:
                pattern_ji = True
        # 食神格生财: 官煞为忌(官煞克食神)
        if is_shishen_shengcai:
            if gan_wx == guan_wx or zhi_wx == guan_wx:
                pattern_ji = True
        # 财格生官: 七煞伤官为忌
        if is_cai_shengguan:
            shishang_wx = SHENG.get(dm_wx_local, '')
            if gan_wx == shishang_wx or zhi_wx == shishang_wx:
                pattern_ji = True
        # 印格用官: 财运反吉(财生官→官生印), 包括大运藏干中的财
        if is_yin_yongguan:
            if gan_wx == cai_wx or zhi_wx == cai_wx:
                pattern_xi = True
            else:
                # 检查大运藏干中是否有财
                for h in zhi_hidden:
                    if WX.get(h, '') == cai_wx:
                        pattern_xi = True
                        break
        # 阳刃格: 财乡为喜(财生官煞制刃), 包括大运藏干中的财
        if is_yangren_month:
            if gan_wx == cai_wx or zhi_wx == cai_wx:
                pattern_xi = True
            else:
                # 检查大运藏干中是否有财
                for h in zhi_hidden:
                    if WX.get(h, '') == cai_wx:
                        pattern_xi = True
                        break
        
        # V4.5: 两气格喜忌判断
        if is_liangqi:
            # 两气格喜: 两行的五行
            for lw in liangqi_wuxing:
                if gan_wx == lw or zhi_wx == lw:
                    pattern_xi = True
            # 两气格忌: 克两行的五行
            for lw in liangqi_wuxing:
                ke_lw = KE_ME.get(lw, '')
                if ke_lw and (gan_wx == ke_lw or zhi_wx == ke_lw):
                    pattern_ji = True
        
        # V4.4: 化气格喜忌判断
        if is_huaqi:
            # 化气格喜: 化神五行+生化神的五行
            if gan_wx == huaqi_wx or zhi_wx == huaqi_wx:
                pattern_xi = True
            # 生化神的五行
            sheng_huaqi = ''
            for k, v in SHENG.items():
                if v == huaqi_wx:
                    sheng_huaqi = k
                    break
            if sheng_huaqi and (gan_wx == sheng_huaqi or zhi_wx == sheng_huaqi):
                pattern_xi = True
            # 化气格忌: 克化神的五行+化神克的五行
            ke_huaqi = KE_ME.get(huaqi_wx, '')
            if ke_huaqi and (gan_wx == ke_huaqi or zhi_wx == ke_huaqi):
                pattern_ji = True
            huaqi_ke = KE.get(huaqi_wx, '')
            if huaqi_ke and (gan_wx == huaqi_ke or zhi_wx == huaqi_ke):
                pattern_ji = True
        
        # V4.3: 专旺格喜忌判断
        if is_zhuanwang:
            # 专旺格喜: 专旺五行+生专旺的五行
            if gan_wx == zhuanwang_wx or zhi_wx == zhuanwang_wx:
                pattern_xi = True
            # 生专旺的五行
            sheng_zhuanwang = ''
            for k, v in SHENG.items():
                if v == zhuanwang_wx:
                    sheng_zhuanwang = k
                    break
            if sheng_zhuanwang and (gan_wx == sheng_zhuanwang or zhi_wx == sheng_zhuanwang):
                pattern_xi = True
            # 专旺格忌: 克专旺的五行+专旺克的五行
            ke_zhuanwang = KE_ME.get(zhuanwang_wx, '')
            if ke_zhuanwang and (gan_wx == ke_zhuanwang or zhi_wx == ke_zhuanwang):
                pattern_ji = True
            zhuanwang_ke = KE.get(zhuanwang_wx, '')
            if zhuanwang_ke and (gan_wx == zhuanwang_ke or zhi_wx == zhuanwang_ke):
                pattern_ji = True
        
        # V4.2: 从格喜忌判断
        if is_cong_ge:
            # 从格忌生扶日主的运(比劫+印)
            if gan_wx == dmw or zhi_wx == dmw:  # 比劫运
                pattern_ji = True
            if gan_wx == yin_wx or zhi_wx == yin_wx:  # 印运
                pattern_ji = True
            # 从格喜从神的旺地
            if '从财格' in special_name:
                if gan_wx == cai_wx or zhi_wx == cai_wx:  # 财运
                    pattern_xi = True
                if gan_wx == shi_wx or zhi_wx == shi_wx:  # 食伤运
                    pattern_xi = True
            elif '从杀格' in special_name or '从官格' in special_name:
                if gan_wx == guan_wx or zhi_wx == guan_wx:  # 官杀运
                    pattern_xi = True
                if gan_wx == cai_wx or zhi_wx == cai_wx:  # 财运
                    pattern_xi = True
            elif '从儿格' in special_name:
                if gan_wx == shi_wx or zhi_wx == shi_wx:  # 食伤运
                    pattern_xi = True
                if gan_wx == cai_wx or zhi_wx == cai_wx:  # 财运
                    pattern_xi = True
        
        # V4.1: 七杀格用食制: 印运为喜(印制食伤扶身), 财运为忌(财生杀)
        if is_qisha_yongshi:
            if gan_wx == yin_wx or zhi_wx == yin_wx:
                pattern_xi = True
            if gan_wx == cai_wx or zhi_wx == cai_wx:
                pattern_ji = True
        
        # 七杀格用印化: 印运为喜, 财运为忌(财破印)
        if is_qisha_yongyin:
            if gan_wx == yin_wx or zhi_wx == yin_wx:
                pattern_xi = True
            if gan_wx == cai_wx or zhi_wx == cai_wx:
                pattern_ji = True
        
        # 建禄月劫格用官: 财运为喜(财生官), 食伤为忌(食伤克官)
        if is_jianlu_yongguan:
            if gan_wx == cai_wx or zhi_wx == cai_wx:
                pattern_xi = True
            if gan_wx == shi_wx or zhi_wx == shi_wx:
                pattern_ji = True
        
        # 建禄月劫格用财: 食伤运为喜(食伤生财), 比劫为忌(比劫夺财)
        if is_jianlu_yongcai:
            if gan_wx == shi_wx or zhi_wx == shi_wx:
                pattern_xi = True
            bijie_wx = dmw  # 比劫五行=日主五行
            if gan_wx == bijie_wx or zhi_wx == bijie_wx:
                pattern_ji = True
        
        # V4.1: 地支需要引动判断 (基于子平真诠论喜忌干支有别)
        # 天干主动直接体现, 地支主静需要引动(冲/合/会)才作祸福
        # 如果只有ZHI_PRIMARY(地支是用神)但没有引动关系, 则地支用神力量减弱
        zhi_primary_only = ('ZHI_PRIMARY' in relations and 'GAN_PRIMARY' not in relations 
                            and 'GAN_SHENG_PRIMARY' not in relations and 'WUHE_PRIMARY' not in relations
                            and 'SANHE_PRIMARY' not in relations and 'SANHUI_PRIMARY' not in relations
                            and 'BANHE_PRIMARY' not in relations and not chong_avoid_any and not he_primary_any
                            and not hidden_primary_any)
        # 地支忌神同样需要引动
        zhi_avoid_only = ('ZHI_AVOID' in relations and 'GAN_AVOID' not in relations 
                          and 'GAN_KE_PRIMARY' not in relations and 'GAN_PRIMARY_SHENG' not in relations
                          and not chong_primary_any and not he_avoid_any and not hidden_avoid_any
                          and not hai_primary_any and not xing_primary_any)
        
        # V4.43: 截脚/盖头修正 (原典: 忌神被截脚无力反转为喜, 用神被盖头无力反转为忌)
        # 忌神被截脚且地支是用神 -> 取消has_ji (忌神无力, 用神得地)
        jiejiao_cancel_ji = ('GAN_AVOID' in relations and 'GAN_JIEJIAO' in relations and 'ZHI_PRIMARY' in relations)
        # 用神被截脚且地支是忌神 -> 取消has_xi (用神无力, 忌神得地)
        jiejiao_cancel_xi = ('GAN_PRIMARY' in relations and 'GAN_JIEJIAO' in relations and 'ZHI_AVOID' in relations)
        # 地支用神被盖头且天干是忌神 -> 取消has_xi (用神无力, 忌神透干)
        gaitou_cancel_xi = ('ZHI_PRIMARY' in relations and 'ZHI_GAITOU' in relations and 'GAN_AVOID' in relations)
        # 地支忌神被盖头且天干是用神 -> 取消has_ji (忌神无力, 用神透干)
        gaitou_cancel_ji = ('ZHI_AVOID' in relations and 'ZHI_GAITOU' in relations and 'GAN_PRIMARY' in relations)
        
        has_xi = ('GAN_PRIMARY' in relations or 'ZHI_PRIMARY' in relations or 'GAN_SHENG_PRIMARY' in relations 
                  or 'WUHE_PRIMARY' in relations or 'SANHE_PRIMARY' in relations or 'SANHUI_PRIMARY' in relations 
                  or 'BANHE_PRIMARY' in relations or hidden_primary_any or he_primary_any
                  or ten_god_xi or 'MONTH_ROOT_SHENG' in relations or shangguan_peiyin_guanxi or pattern_xi)
        # V4.47: 取消V4.43截脚/盖头修正(太激进, 原典截脚只是减弱不是完全取消)
        # if jiejiao_cancel_xi or gaitou_cancel_xi:
        #     has_xi = False
        has_ji = ('GAN_AVOID' in relations or 'ZHI_AVOID' in relations or 'GAN_KE_PRIMARY' in relations 
                  or 'GAN_PRIMARY_SHENG' in relations or hidden_avoid_any or chong_primary_any or he_avoid_any or hai_primary_any or xing_primary_any
                  or ten_god_ji or 'MONTH_ROOT_KE' in relations or pattern_ji)
        # V4.47: 取消V4.43截脚/盖头修正
        # if jiejiao_cancel_ji or gaitou_cancel_ji:
        #     has_ji = False
        xiji_labels = []
        if has_xi:
            xiji_labels.append('SUPPORT_USE_GOD')
        if has_ji:
            xiji_labels.append('SUPPRESS_USE_GOD')
        if 'GAN_SECONDARY' in relations or 'ZHI_SECONDARY' in relations:
            xiji_labels.append('SUPPORT_XI_SHEN')
        if not xiji_labels:
            xiji_labels.append('NEUTRAL')
        
        # V2.7: 用神强弱布尔枚举(替代评分加权): 用神无根无透干则弱
        primary_weak = primary_weak_bool
        
        # V4.8: 天干忌神透干优先判断 (天干主动直接体现, 力量大于地支)
        # 如果天干是忌神(透干直接克用神/生忌神), 即使地支有喜神, 整体也偏忌
        gan_avoid_strong = ('GAN_AVOID' in relations or 'GAN_KE_PRIMARY' in relations or 'GAN_PRIMARY_SHENG' in relations)
        # 身旺食伤泄秀为喜: 原局身旺, 大运食伤透干泄秀, 即使食伤克官用神, 也为喜
        # 需要判断原局是否身旺 (消费wang_shuai+qiang_ruo布尔枚举, 替代LEGACY spectrum)
        _ws = yongshen_result.get('wang_shuai', {})
        _qr = yongshen_result.get('qiang_ruo', {})
        _in_season = _ws.get('in_season', False) if isinstance(_ws, dict) else False
        _has_heavy = _qr.get('has_heavy_root', False) if isinstance(_qr, dict) else False
        _support_n = _qr.get('support_stem_count', 0) if isinstance(_qr, dict) else 0
        is_shenwang = _has_heavy and (_in_season or _support_n >= 2)
        shishang_wx = SHENG.get(dm_wx_local, '')  # 食伤五行
        gan_shishang = (gan_wx == shishang_wx)
        shenwang_shishang_xiexiu = (is_shenwang and gan_shishang and primary and KE.get(shishang_wx, '') == primary)
        
        # V4.45: 比劫夺财 - 大运天干比劫坐财星且财星是用神/喜神时, 判忌(原典: 比劫夺财, 比劫坐财为忌)
        _cai_wx = KE.get(dm_wx_local, '')
        bijie_duocai = (gan_wx == dm_wx_local and zhi_wx == _cai_wx 
                        and ('ZHI_PRIMARY' in relations or 'ZHI_SECONDARY' in relations or 'GAN_PRIMARY' in relations))
        # V4.45: 官杀克身 - 大运干支皆官杀且身弱时, 判忌(原典: 官杀克身, 身弱忌官杀)
        _guansha_wx = KE_ME.get(dm_wx_local, '')
        guansha_keshen_shenruo = (gan_wx == _guansha_wx and zhi_wx == _guansha_wx and not is_shenwang)
        # V4.45: 食伤泄秀太过 - 大运干支皆食伤且身弱时, 判忌(原典: 食伤泄气太过, 身弱忌食伤)
        _shishang_wx = SHENG.get(dm_wx_local, '')
        shishang_xiexiu_taiguo = (gan_wx == _shishang_wx and zhi_wx == _shishang_wx and not is_shenwang)
        
        # V4.46: 天干用神优先 - 天干透用神且天干不是忌神时, 优先判喜(原典: 天干主动力量大于地支)
        gan_primary_strong = ('GAN_PRIMARY' in relations and 'GAN_AVOID' not in relations 
                               and 'GAN_KE_PRIMARY' not in relations and 'GAN_PRIMARY_SHENG' not in relations)
        # V4.46: 比劫盖头用神 - 天干比劫+地支用神时, 判忌(原典: 比劫盖头, 用神无力)
        bijie_gaitou_primary = (gan_wx == dm_wx_local and 'ZHI_PRIMARY' in relations 
                                 and 'GAN_PRIMARY' not in relations and 'GAN_AVOID' not in relations)
        # V4.48: 身衰极官杀克身 - 日主衰时, 官杀克身即使官杀是用神也判忌(原典: 身衰不能承受官杀)
        # 布尔枚举: 无根 且 (失令 或 食伤财官透干>=2)
        _has_root_local = _qr.get('has_root', False) if isinstance(_qr, dict) else False
        _root_class_local = _qr.get('root_class', 'NONE') if isinstance(_qr, dict) else 'NONE'
        _oppose_n_local = _qr.get('oppose_stem_count', 0) if isinstance(_qr, dict) else 0
        is_shenshuai = (_root_class_local == 'NONE') and ((not _in_season) or _oppose_n_local >= 2)
        _guansha_wx_local = KE_ME.get(dm_wx_local, '')
        shenshuai_guansha_keshen = (is_shenshuai and 
                                     (gan_wx == _guansha_wx_local or zhi_wx == _guansha_wx_local) and
                                     ('GAN_PRIMARY' in relations or 'ZHI_PRIMARY' in relations or 'GAN_SHENG_PRIMARY' in relations))
        # V4.49: 身旺食伤泄秀为喜 - 身旺/旺极时, 大运干支皆食伤判喜(原典: 身旺喜食伤泄秀)
        # V4.54: 收紧 - 只有大运干支不在avoid列表中时才判喜(忌神大运即使身旺喜泄也不判喜)
        # V4.59: 放松 - 身旺极时即使食伤在avoid列表中也判喜
        # V4.62: 放松 - 身旺(包括旺/旺极/太旺)时即使食伤在avoid列表中也判喜
        # 原典:身旺食伤泄秀是扶抑层面的喜,不能被调候avoid覆盖,如壬辰壬子壬子癸卯乙卯运
        _shishang_wx_local = SHENG.get(dm_wx_local, '')
        shenwang_shishang_xiexiu_v2 = (is_shenwang and gan_wx == _shishang_wx_local and zhi_wx == _shishang_wx_local)
        # V4.49: 身衰比劫帮身为喜 - 身衰/衰极时, 大运干支皆比劫判喜(原典: 身衰喜比劫帮身)
        # V4.54: 收紧 - 只有大运干支不在avoid列表中时才判喜
        # V4.55: 身衰极时放松avoid检查(原典:身衰极喜比劫帮身,扶抑喜神优先级高于调候忌神)
        # V4.61: 放松 - 身衰(包括衰/衰极/太衰)时即使比劫在avoid列表中也判喜
        # 原典:身衰比劫帮身是扶抑层面的喜,不能被调候avoid覆盖,如壬申甲辰丙寅丙申丙午运
        # 身衰极: 无根 且 失令 且 食伤财官透干>=3
        is_shenshuai_ji = (_root_class_local == 'NONE') and (not _in_season) and (_oppose_n_local >= 3)
        shenshuai_bijie_bangshen = (is_shenshuai and gan_wx == dm_wx_local and zhi_wx == dm_wx_local)
        # V4.65: 身衰食伤+比劫为喜 - 身衰时, 大运天干食伤+地支比劫(比劫帮身为主,食伤泄秀为辅), 判喜
        # 原典:身衰喜比劫帮身,即使天干是食伤也不影响比劫帮身的喜,如癸亥癸亥丙辰甲午戊午运
        _shishang_wx_local3 = SHENG.get(dm_wx_local, '')
        shenshuai_shishang_bijie = (is_shenshuai and gan_wx == _shishang_wx_local3 and zhi_wx == dm_wx_local)
        # V4.55: 身衰极食伤泄秀为喜 - 身衰极时, 大运干支皆食伤也判喜(原典:身衰极食伤生财财生官杀官杀生印印生身,流通有情)
        _shishang_wx_local3 = SHENG.get(dm_wx_local, '')
        shenshuai_shishang_xiexiu = (is_shenshuai_ji and gan_wx == _shishang_wx_local3 and zhi_wx == _shishang_wx_local3)
        # V4.50: 身衰财多身弱 - 身衰/衰极时, 大运干支皆财, 即使财星是用神/喜神也判忌(原典: 财多身弱)
        _cai_wx_local = KE.get(dm_wx_local, '')
        shenshuai_cai_duo_shen_ruo = (is_shenshuai and gan_wx == _cai_wx_local and zhi_wx == _cai_wx_local)
        # V4.51: 身旺财生官杀 - 身旺时, 大运天干财+地支官杀(财生官杀制比劫), 判喜(原典: 身旺喜财官)
        # V4.57: 收紧 - 只有大运干支不在avoid列表中时才判喜
        # V4.64: 放松 - 身旺时即使财和官杀在avoid列表中也判喜
        # 原典:身旺财生官杀是扶抑层面的喜,不能被调候avoid覆盖,如丙戌辛丑己卯甲子壬寅运
        _guansha_wx_local = KE_ME.get(dm_wx_local, '')
        shenwang_cai_sheng_guansha = (is_shenwang and gan_wx == _cai_wx_local and zhi_wx == _guansha_wx_local)
        # V4.51: 身旺比劫+食伤 - 身旺时, 大运天干比劫+地支食伤(比劫帮身+食伤泄秀), 判喜
        # V4.54: 收紧 - 只有大运干支不在avoid列表中时才判喜
        # V4.63: 放松 - 身旺时即使比劫和食伤在avoid列表中也判喜
        # 原典:身旺比劫帮身+食伤泄秀是扶抑层面的喜,不能被调候avoid覆盖,如己丑丙子辛酉壬辰癸酉运
        _shishang_wx_local2 = SHENG.get(dm_wx_local, '')
        shenwang_bijie_shishang = (is_shenwang and gan_wx == dm_wx_local and zhi_wx == _shishang_wx_local2)
        
        if has_xi and has_ji:
            # V4.45: 比劫夺财优先判忌
            if bijie_duocai:
                xiji_label = 'SUPPRESS_USE_GOD'
            # V4.46: 比劫盖头用神判忌
            elif bijie_gaitou_primary:
                xiji_label = 'SUPPRESS_USE_GOD'
            # V4.48: 身衰极官杀克身判忌
            elif shenshuai_guansha_keshen:
                xiji_label = 'SUPPRESS_USE_GOD'
            # V4.49: 身旺食伤泄秀为喜
            elif shenwang_shishang_xiexiu_v2:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.49: 身衰比劫帮身为喜
            elif shenshuai_bijie_bangshen:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.65: 身衰食伤+比劫为喜
            elif shenshuai_shishang_bijie:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.55: 身衰极食伤泄秀为喜
            elif shenshuai_shishang_xiexiu:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.50: 身衰财多身弱判忌
            elif shenshuai_cai_duo_shen_ruo:
                xiji_label = 'SUPPRESS_USE_GOD'
            # V4.51: 身旺财生官杀为喜
            elif shenwang_cai_sheng_guansha:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.51: 身旺比劫+食伤为喜
            elif shenwang_bijie_shishang:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.45: 官杀克身(身弱)优先判忌
            elif guansha_keshen_shenruo:
                xiji_label = 'SUPPRESS_USE_GOD'
            # V4.45: 食伤泄秀太过(身弱)优先判忌
            elif shishang_xiexiu_taiguo:
                xiji_label = 'SUPPRESS_USE_GOD'
            # V4.46: 天干用神优先判喜(天干透用神力量大于地支忌神)
            elif gan_primary_strong:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.8: 身旺食伤泄秀为喜优先
            elif shenwang_shishang_xiexiu:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.8: 天干忌神透干优先 (天干主动力量大)
            elif gan_avoid_strong:
                xiji_label = 'SUPPRESS_USE_GOD'
            # V4.41: 生扶和克泄同时存在时, 克泄优先(原典中克泄用神的运通常为忌, 生扶仅在用神极弱时为喜)
            elif primary_weak:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.53: 地支用神得地+天干非忌神时判喜(原典:地支用神得地,天干不克用神则喜)
            elif ('ZHI_PRIMARY' in relations and 'GAN_AVOID' not in relations 
                  and 'GAN_KE_PRIMARY' not in relations and 'GAN_PRIMARY_SHENG' not in relations):
                xiji_label = 'SUPPORT_USE_GOD'
            else:
                xiji_label = 'SUPPRESS_USE_GOD'
        elif has_xi:
            # V4.45: 比劫夺财即使只有喜也判忌
            if bijie_duocai:
                xiji_label = 'SUPPRESS_USE_GOD'
            # V4.46: 比劫盖头用神即使只有喜也判忌
            elif bijie_gaitou_primary:
                xiji_label = 'SUPPRESS_USE_GOD'
            # V4.48: 身衰极官杀克身即使只有喜也判忌
            elif shenshuai_guansha_keshen:
                xiji_label = 'SUPPRESS_USE_GOD'
            else:
                xiji_label = 'SUPPORT_USE_GOD'
        elif has_ji:
            # V4.49: 身旺食伤泄秀为喜(即使只有忌也可能判喜)
            if shenwang_shishang_xiexiu_v2:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.49: 身衰比劫帮身为喜
            elif shenshuai_bijie_bangshen:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.65: 身衰食伤+比劫为喜
            elif shenshuai_shishang_bijie:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.55: 身衰极食伤泄秀为喜
            elif shenshuai_shishang_xiexiu:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.51: 身旺财生官杀为喜
            elif shenwang_cai_sheng_guansha:
                xiji_label = 'SUPPORT_USE_GOD'
            # V4.51: 身旺比劫+食伤为喜
            elif shenwang_bijie_shishang:
                xiji_label = 'SUPPORT_USE_GOD'
            else:
                # V4.37: 只有克泄直接判忌, 移除'用神强时克泄为喜'的激进逻辑(原典中克泄用神的运通常为忌)
                xiji_label = 'SUPPRESS_USE_GOD'
        elif 'GAN_SECONDARY' in relations or 'ZHI_SECONDARY' in relations:
            xiji_label = 'SUPPORT_XI_SHEN'  # 生扶喜神
        else:
            xiji_label = 'NEUTRAL'  # 中性
        
        # V4.6: 语义类型标记 - 区分"大运提供"与"大运互动"
        # DAYUN_PROVISION: 大运透干/通根直接提供了命局所需 (天干是用神/地支是用神/藏干是用神)
        # DAYUN_INTERACTION: 大运通过冲/合/刑/害等互动关系影响命局 (冲用神/合用神/刑用神)
        # MIXED: 同时存在提供和互动
        provision_relations = ['GAN_PRIMARY', 'ZHI_PRIMARY', 'GAN_SHENG_PRIMARY', 'ZHI_HIDDEN_BENQI_PRIMARY', 
                                'ZHI_HIDDEN_ZHONGQI_PRIMARY', 'ZHI_HIDDEN_YUQI_PRIMARY', 'GAN_SECONDARY', 'ZHI_SECONDARY']
        interaction_relations = ['CHONG_', 'HE_', 'HAI_', 'XING_', 'PO_', 'WUHE_', 'SANHE_', 'SANHUI_', 'BANHE_', 'LIUHE_']
        has_provision = any(any(pr in r for pr in provision_relations) for r in relations)
        has_interaction = any(any(ir in r for ir in interaction_relations) for r in relations)
        if has_provision and has_interaction:
            semantic_type = 'MIXED'
        elif has_provision:
            semantic_type = 'DAYUN_PROVISION'
        elif has_interaction:
            semantic_type = 'DAYUN_INTERACTION'
        else:
            semantic_type = 'NEUTRAL'
        
        # 大运提供了哪些命局所需
        dayun_provides = []
        if 'GAN_PRIMARY' in relations:
            dayun_provides.append(f'天干透{primary}')
        if 'ZHI_PRIMARY' in relations:
            dayun_provides.append(f'地支坐{primary}')
        if hidden_primary_any:
            dayun_provides.append(f'地支藏{primary}')
        if 'GAN_SECONDARY' in relations or 'ZHI_SECONDARY' in relations:
            dayun_provides.append('提供喜神')
        
        # 大运破坏了哪些命局所需
        dayun_suppresses = []
        if chong_primary_any:
            dayun_suppresses.append(f'冲{primary}')
        if he_primary_any:
            dayun_suppresses.append(f'合{primary}')
        if hai_primary_any:
            dayun_suppresses.append(f'害{primary}')
        if xing_primary_any:
            dayun_suppresses.append(f'刑{primary}')
        if 'GAN_KE_PRIMARY' in relations:
            dayun_suppresses.append(f'天干克{primary}')
        if 'GAN_PRIMARY_SHENG' in relations:
            dayun_suppresses.append(f'{primary}生天干(泄)')
        
        # V4.58: 确保xiji_labels包含xiji_label(修复主标签和多标签不一致的bug)
        if xiji_label not in xiji_labels:
            xiji_labels.insert(0, xiji_label)
        
        # V7.18: 冲突保留输出 - 元素级+互动级并行, 冲突时不裁决
        _element_xi = (gan_wx in secondary or zhi_wx in secondary)
        _element_ji = (gan_wx in avoid or zhi_wx in avoid)
        if _element_xi and not _element_ji: _element_result = '喜'
        elif _element_ji and not _element_xi: _element_result = '忌'
        else: _element_result = '中性'
        _interaction_types = [r for r in relations if any(k in r for k in ['WUHE','SANHE','SANHUI','BANHE','CHONG','XING','HAI','PO','HE_'])]
        _has_interaction = len(_interaction_types) > 0
        _interaction_may_xi = any('PRIMARY' in r for r in _interaction_types) if _has_interaction else False
        _interaction_may_ji = any(('AVOID' in r or 'KE_PRIMARY' in r or 'PRIMARY_SHENG' in r) for r in _interaction_types) if _has_interaction else False
        _has_conflict = False
        _conflict_type = ''
        if _has_interaction:
            if _element_result == '喜' and _interaction_may_ji:
                _has_conflict = True; _conflict_type = '元素级喜 vs 互动级可能忌'
            elif _element_result == '忌' and _interaction_may_xi:
                _has_conflict = True; _conflict_type = '元素级忌 vs 互动级可能喜'
        
        # V7.20: 大运分前五后五判断逻辑(渊海模式: 前5年天干+地支联合, 后5年地支独立)
        _gan_xi = gan_wx in secondary
        _gan_ji = gan_wx in avoid
        _zhi_xi = zhi_wx in secondary
        _zhi_ji = zhi_wx in avoid
        # 十神辅助: 比劫透干且原局财星成势时比劫为忌(夺财)
        _gan_is_bijie = (gan_wx == dmw)
        _cai_chengshi = (primary == KE.get(dm,'')) and any('ZHI_PRIMARY' in r for r in relations)
        if _gan_is_bijie and _cai_chengshi and not _gan_xi: _gan_ji = True
        # 前期: 天干主导, 地支辅助
        if _gan_xi and not _gan_ji: _f5 = '喜'
        elif _gan_ji and not _gan_xi: _f5 = '忌'
        elif _zhi_xi and not _zhi_ji: _f5 = '喜'
        elif _zhi_ji and not _zhi_xi: _f5 = '忌'
        else: _f5 = '中性'
        # 后期: 地支独立, 弃天干
        if _zhi_xi and not _zhi_ji: _l5 = '喜'
        elif _zhi_ji and not _zhi_xi: _l5 = '忌'
        else: _l5 = '中性'
        per_step.append({
            'ganzhi': gz,
            'gan': gan,
            'zhi': zhi,
            'gan_wuxing': gan_wx,
            'zhi_wuxing': zhi_wx,
            'ten_god': ten_god,
            'relations': relations,
            'xiji_label': xiji_label,
            'xiji_labels': xiji_labels,
            'semantic_type': semantic_type,  # 语义类型: DAYUN_PROVISION/DAYUN_INTERACTION/MIXED/NEUTRAL
            'stem_match_type': stem_match_type,  # V7.23 PATCH: 十干级调候匹配类型(EXACT_STEM/ELEMENT_MATCH/NONE)
            'dayun_provides': dayun_provides,  # 大运提供了哪些命局所需
            'dayun_suppresses': dayun_suppresses,  # 大运破坏了哪些命局所需
            # V7.18: 冲突保留输出 - 元素级+互动级并行, 冲突时不裁决
            'element_judgment': {'result': _element_result, 'in_fav': _element_xi, 'in_avoid': _element_ji},
            'interaction_judgment': {'has_interaction': _has_interaction, 'types': _interaction_types, 'may_xi': _interaction_may_xi, 'may_ji': _interaction_may_ji},
            'conflict': {'has_conflict': _has_conflict, 'type': _conflict_type, 'resolution': '保留多解不裁决' if _has_conflict else ''},
            'first_5': {'gan': gan, 'gan_wx': gan_wx, 'result': _f5, 'gan_xi': _gan_xi, 'gan_ji': _gan_ji, 'zhi_xi': _zhi_xi, 'zhi_ji': _zhi_ji},
            'last_5': {'zhi': zhi, 'zhi_wx': zhi_wx, 'result': _l5},
            'overall': {'result': xiji_label, 'mode': 'YUANHAI_FENKAN'},
        })
    
    # V4.7: 冲突保留输出 - 多源透明, 保留理论分歧
    # 获取用神引擎的理论来源标签
    theory_source = yongshen_result.get('theory_source', 'THEORY_ZIPING')
    # 获取所有候选用神及其理论来源
    yongshen_candidates = yongshen_result.get('yongshen_candidates', [])
    
    return {
        'module': 'DAYUN_XIJI_V4.8',
        'namespace': 'dayun_xiji_structure',
        'day_master': dm,
        'daymaster_wuxing': dmw,
        'yongshen_primary': primary,
        'yongshen_secondary': secondary,
        'yongshen_avoid': avoid,
        'theory_source': theory_source,  # 理论来源标签 (ZIPING/QIONGTONG/SHENFENG)
        'yongshen_candidates': yongshen_candidates,  # 所有候选用神(多源透明)
        'per_step': per_step,
        'judgment_status': 'DAYUN_XIJI_STRUCTURE_ONLY',
        'boundary_note': '大运喜忌结构层V4.7: 冲突保留输出-多源透明保留理论分歧; 区分原局喜忌与大运喜忌; semantic_type标记DAYUN_PROVISION/DAYUN_INTERACTION/MIXED; theory_source标记ZIPING/QIONGTONG/SHENFENG; 不强行裁决唯一答案, 保留多源结论; 非吉凶裁决; 吉凶前端拦截',
    }



