# -*- coding: utf-8 -*-
"""160-E 十干作用机制矩阵 V1.0

十干级完整作用关系: 生/克/合/冲/化, 区分阴阳干作用力度.

原典依据:
- 阳生阳力大, 阴生阴力大(同气相生); 阳生阴力小, 阴生阳力小(异气相生)
- 阳克阳力大, 阴克阴力大(同气相克); 阳克阴力大, 阴克阳力小(异气相克)
- 天干五合: 甲己合土, 乙庚合金, 丙辛合水, 丁壬合木, 戊癸合火
- 天干四冲: 甲庚冲, 乙辛冲, 丙壬冲, 丁癸冲(戊己居中无冲)

不评分/不权重/不裁决, 只输出结构关系和力度枚举.
"""

from typing import Dict, Optional, Tuple

# 十干列表
GAN_LIST = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']

# 十干五行
GAN_WUXING = {
    '甲': '木', '乙': '木',
    '丙': '火', '丁': '火',
    '戊': '土', '己': '土',
    '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}

# 十干阴阳
GAN_YINYANG = {
    '甲': '阳', '丙': '阳', '戊': '阳', '庚': '阳', '壬': '阳',
    '乙': '阴', '丁': '阴', '己': '阴', '辛': '阴', '癸': '阴',
}

# 五行生: 我生
WUXING_SHENG = {
    '木': '火', '火': '土', '土': '金', '金': '水', '水': '木',
}

# 五行克: 我克
WUXING_KE = {
    '木': '土', '土': '水', '水': '火', '火': '金', '金': '木',
}

# 天干五合: (干1, 干2) → 化神
GAN_HE = {
    frozenset(('甲', '己')): '土',
    frozenset(('乙', '庚')): '金',
    frozenset(('丙', '辛')): '水',
    frozenset(('丁', '壬')): '木',
    frozenset(('戊', '癸')): '火',
}

# 天干五合名称
GAN_HE_NAME = {
    frozenset(('甲', '己')): '中正之合',
    frozenset(('乙', '庚')): '仁义之合',
    frozenset(('丙', '辛')): '威制之合',
    frozenset(('丁', '壬')): '淫匿之合',
    frozenset(('戊', '癸')): '无情之合',
}

# 天干四冲: (干1, 干2)
GAN_CHONG = {
    frozenset(('甲', '庚')),
    frozenset(('乙', '辛')),
    frozenset(('丙', '壬')),
    frozenset(('丁', '癸')),
}

# 作用力度枚举(有序)
STRENGTH_LEVEL = ['FORCE_STRONG', 'FORCE_NORMAL', 'FORCE_WEAK', 'FORCE_NONE']


def get_sheng_relation(gan1: str, gan2: str) -> Optional[Dict]:
    """查询gan1是否生gan2. 返回生的关系和力度.

    力度规则:
    - 同气相生(阳生阳/阴生阴): FORCE_STRONG
    - 异气相生(阳生阴/阴生阳): FORCE_NORMAL
    - 不生: None

    原典: 阳生阳力大, 阴生阴力大(同气相求)
    """
    if gan1 not in GAN_WUXING or gan2 not in GAN_WUXING:
        return None
    wx1 = GAN_WUXING[gan1]
    wx2 = GAN_WUXING[gan2]
    if WUXING_SHENG.get(wx1) != wx2:
        return None  # gan1不生gan2
    yy1 = GAN_YINYANG[gan1]
    yy2 = GAN_YINYANG[gan2]
    if yy1 == yy2:
        force = 'FORCE_STRONG'  # 同气相生力大
    else:
        force = 'FORCE_NORMAL'  # 异气相生力正常
    return {
        'relation': 'SHENG',
        'from': gan1,
        'to': gan2,
        'force': force,
        'same_yinyang': yy1 == yy2,
        'description': f'{gan1}({yy1}{wx1})生{gan2}({yy2}{wx2}), {force}',
    }


def get_ke_relation(gan1: str, gan2: str) -> Optional[Dict]:
    """查询gan1是否克gan2. 返回克的关系和力度.

    力度规则:
    - 同气相克(阳克阳/阴克阴): FORCE_STRONG
    - 阳克阴: FORCE_STRONG(阳克阴力大)
    - 阴克阳: FORCE_WEAK(阴克阳力小)

    原典: 阳克阳力大, 阴克阴力大; 阳克阴力大, 阴克阳力小
    """
    if gan1 not in GAN_WUXING or gan2 not in GAN_WUXING:
        return None
    wx1 = GAN_WUXING[gan1]
    wx2 = GAN_WUXING[gan2]
    if WUXING_KE.get(wx1) != wx2:
        return None  # gan1不克gan2
    yy1 = GAN_YINYANG[gan1]
    yy2 = GAN_YINYANG[gan2]
    if yy1 == yy2:
        force = 'FORCE_STRONG'  # 同气相克力大
    elif yy1 == '阳' and yy2 == '阴':
        force = 'FORCE_STRONG'  # 阳克阴力大
    else:
        force = 'FORCE_WEAK'  # 阴克阳力小
    return {
        'relation': 'KE',
        'from': gan1,
        'to': gan2,
        'force': force,
        'same_yinyang': yy1 == yy2,
        'description': f'{gan1}({yy1}{wx1})克{gan2}({yy2}{wx2}), {force}',
    }


def get_he_relation(gan1: str, gan2: str) -> Optional[Dict]:
    """查询gan1和gan2是否天干五合. 返回合的关系和化神."""
    key = frozenset((gan1, gan2))
    if key not in GAN_HE:
        return None
    huashen = GAN_HE[key]
    he_name = GAN_HE_NAME.get(key, '')
    return {
        'relation': 'HE',
        'gan1': gan1,
        'gan2': gan2,
        'huashen': huashen,
        'he_name': he_name,
        'description': f'{gan1}{gan2}合({he_name}), 化{huashen}',
    }


def get_chong_relation(gan1: str, gan2: str) -> Optional[Dict]:
    """查询gan1和gan2是否天干相冲."""
    key = frozenset((gan1, gan2))
    if key not in GAN_CHONG:
        return None
    return {
        'relation': 'CHONG',
        'gan1': gan1,
        'gan2': gan2,
        'description': f'{gan1}{gan2}相冲',
    }


def get_full_relation(gan1: str, gan2: str) -> Dict:
    """查询两个天干之间的完整关系(生/克/合/冲)."""
    relations = []
    # gan1生gan2
    sheng_12 = get_sheng_relation(gan1, gan2)
    if sheng_12:
        relations.append(sheng_12)
    # gan2生gan1
    sheng_21 = get_sheng_relation(gan2, gan1)
    if sheng_21:
        relations.append(sheng_21)
    # gan1克gan2
    ke_12 = get_ke_relation(gan1, gan2)
    if ke_12:
        relations.append(ke_12)
    # gan2克gan1
    ke_21 = get_ke_relation(gan2, gan1)
    if ke_21:
        relations.append(ke_21)
    # 合
    he = get_he_relation(gan1, gan2)
    if he:
        relations.append(he)
    # 冲
    chong = get_chong_relation(gan1, gan2)
    if chong:
        relations.append(chong)
    return {
        'gan1': gan1,
        'gan2': gan2,
        'relations': relations,
        'relation_count': len(relations),
    }


def get_best_yao_gan(bing_gan: str, yao_wx: str) -> Optional[str]:
    """根据病干和药的五行, 选择最佳药干(同气相克力大原则).

    原典: 阳干病用阳干药(阳克阳力大), 阴干病用阴干药(阴克阴力大)
    """
    if bing_gan not in GAN_YINYANG or yao_wx not in WUXING_SHENG.values():
        return None
    bing_yy = GAN_YINYANG[bing_gan]
    # 找药五行中对应阴阳的天干
    for gan in GAN_LIST:
        if GAN_WUXING[gan] == yao_wx and GAN_YINYANG[gan] == bing_yy:
            return gan
    # 如果找不到同阴阳的, 找第一个
    for gan in GAN_LIST:
        if GAN_WUXING[gan] == yao_wx:
            return gan
    return None


def get_best_yin_gan(yin_wx: str, prefer: str = '阴') -> Optional[str]:
    """选择最佳印干. 默认优先阴印(正印,温和生身), 阳印(偏印)力猛易枭神夺食.

    原典: 阴印正印温和生身, 阳印偏印力猛易枭神夺食
    """
    if yin_wx not in WUXING_SHENG.values():
        return None
    # 优先选指定阴阳的印干
    for gan in GAN_LIST:
        if GAN_WUXING[gan] == yin_wx and GAN_YINYANG[gan] == prefer:
            return gan
    # 找不到就选第一个
    for gan in GAN_LIST:
        if GAN_WUXING[gan] == yin_wx:
            return gan
    return None
