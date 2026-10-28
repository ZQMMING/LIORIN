# -*- coding: utf-8 -*-
"""160-E 大运应期喜忌结构层 V3.0 (纯布尔枚举)
基于原局用神/喜神/忌神与大运干支的关系, 输出结构判断(非吉凶裁决)。
V3.0: 纯布尔枚举, 0浮点, 0打分。
"""
from typing import Dict, List, Any
from spec.yinyang_system import SHENG, KE, SHENG_ME, KE_ME

WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}

LIU_CHONG = {
    '子':'午', '午':'子',
    '丑':'未', '未':'丑',
    '寅':'申', '申':'寅',
    '卯':'酉', '酉':'卯',
    '辰':'戌', '戌':'辰',
    '巳':'亥', '亥':'巳',
}

LIU_HE = {
    '子': ('土', '丑'), '丑': ('土', '子'),
    '寅': ('木', '亥'), '亥': ('木', '寅'),
    '卯': ('火', '戌'), '戌': ('火', '卯'),
    '辰': ('金', '酉'), '酉': ('金', '辰'),
    '巳': ('水', '申'), '申': ('水', '巳'),
    '午': ('土', '未'), '未': ('土', '午'),
}

def get_ten_god(dm_gan: str, gz: str) -> str:
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


def _get_branch_hidden_wuxing(branch: str, hidden_stems: Dict) -> List[str]:
    stems = hidden_stems.get(branch, [])
    return [WX.get(s, '') for s in stems if s in WX]


def build_dayun_xiji(
    pillars: Dict[str, list],
    yongshen_result: Dict[str, Any],
    dayun_list: List[str],
    facts: Dict[str, Any] = None,
) -> Dict[str, Any]:
    dm = pillars['day'][0]
    dmw = WX[dm]

    primary = yongshen_result.get('yongshen_primary') or ''
    secondary = yongshen_result.get('yongshen_secondary') or []
    avoid = yongshen_result.get('yongshen_avoid') or []

    original_branches = [pillars[k][1] for k in ['year', 'month', 'day', 'hour']]
    hidden_stems = {}
    if facts and 'hidden_stems' in facts:
        for k in ['year', 'month', 'day', 'hour']:
            branch = pillars[k][1]
            hidden_stems[branch] = facts['hidden_stems'].get(k, [])

    per_step = []
    for gz in dayun_list:
        gan = gz[0]
        zhi = gz[1]
        gan_wx = WX[gan]
        zhi_wx = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}.get(zhi, '')

        ten_god = get_ten_god(dm, gz)
        relations = []

        # 天干五行关系 (布尔)
        if gan_wx == primary:
            relations.append('GAN_PRIMARY')
        elif gan_wx in secondary:
            relations.append('GAN_SECONDARY')
        elif gan_wx in avoid:
            relations.append('GAN_AVOID')
        elif SHENG.get(gan_wx) == primary:
            relations.append('GAN_SHENG_PRIMARY')
        elif SHENG_ME.get(gan_wx) == primary:
            relations.append('GAN_PRIMARY_SHENG')
        elif KE.get(gan_wx) == primary:
            relations.append('GAN_KE_PRIMARY')

        # 地支五行关系 (布尔)
        if zhi_wx == primary:
            relations.append('ZHI_PRIMARY')
        elif zhi_wx in secondary:
            relations.append('ZHI_SECONDARY')
        elif zhi_wx in avoid:
            relations.append('ZHI_AVOID')

        # 六冲判断 (布尔)
        chong_target = LIU_CHONG.get(zhi, '')
        if chong_target and chong_target in original_branches:
            relations.append(f'ZHI_CHONG_{chong_target}')
            chong_hidden = _get_branch_hidden_wuxing(chong_target, hidden_stems)
            if primary in chong_hidden:
                relations.append('CHONG_PRIMARY_ROOT')
            if avoid and avoid[0] in chong_hidden:
                relations.append('CHONG_AVOID_ROOT')

        # 六合判断 (布尔)
        he_info = LIU_HE.get(zhi, ('', ''))
        he_huashen = he_info[0]
        he_target = he_info[1]
        if he_target and he_target in original_branches:
            relations.append(f'ZHI_HE_{he_target}')
            if he_huashen == primary:
                relations.append('HE_PRIMARY')
            if avoid and he_huashen == avoid[0]:
                relations.append('HE_AVOID')

        # 喜忌标签 (纯布尔枚举, 0浮点)
        has_support = any(r in ['GAN_PRIMARY', 'ZHI_PRIMARY', 'GAN_SHENG_PRIMARY', 'HE_PRIMARY'] for r in relations)
        has_suppress = any(r in ['GAN_AVOID', 'ZHI_AVOID', 'GAN_KE_PRIMARY', 'CHONG_PRIMARY_ROOT', 'HE_AVOID'] for r in relations)
        has_xi_support = any(r in ['GAN_SECONDARY', 'ZHI_SECONDARY'] for r in relations)

        if has_support and not has_suppress:
            xiji_label = 'SUPPORT_USE_GOD'
        elif has_suppress and not has_support:
            xiji_label = 'SUPPRESS_USE_GOD'
        elif has_xi_support:
            xiji_label = 'SUPPORT_XI_SHEN'
        else:
            xiji_label = 'NEUTRAL'

        per_step.append({
            'ganzhi': gz,
            'gan': gan,
            'zhi': zhi,
            'gan_wuxing': gan_wx,
            'zhi_wuxing': zhi_wx,
            'ten_god': ten_god,
            'relations': relations,
            'xiji_label': xiji_label,
        })

    return {
        'module': 'DAYUN_XIJI_V3',
        'namespace': 'dayun_xiji_structure',
        'day_master': dm,
        'daymaster_wuxing': dmw,
        'yongshen_primary': primary,
        'yongshen_secondary': secondary,
        'yongshen_avoid': avoid,
        'per_step': per_step,
        'judgment_status': 'DAYUN_XIJI_STRUCTURE_ONLY',
        'boundary_note': '大运喜忌结构层V3: 纯布尔枚举, 0浮点, 0打分',
    }
