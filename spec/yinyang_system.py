# -*- coding: utf-8 -*-
"""
阴阳类型系统 - 地基模块

四张表：
1. 天干阴阳表
2. 十神派生规则
3. 天干五合表
4. 通根阴阳对应表
"""

# ============ 第一步：天干阴阳表 ============

YANG_STEMS = {'甲', '丙', '戊', '庚', '壬'}
YIN_STEMS = {'乙', '丁', '己', '辛', '癸'}

STEM_WUXING = {
    '甲': '木', '乙': '木',
    '丙': '火', '丁': '火',
    '戊': '土', '己': '土',
    '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}

def stem_yang(stem):
    """判断天干阴阳：True=阳，False=阴"""
    return stem in YANG_STEMS


# ============ 第二步：十神派生规则 ============
# 不硬编码十行表，用规则派生

SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
SHENG_ME = {v: k for k, v in SHENG.items()}
KE_ME = {v: k for k, v in KE.items()}


def get_shishen(day_stem, other_stem):
    """
    计算十神（派生规则，不硬编码表）
    
    规则：
    生我者: 同阴阳→偏印(枭), 异阴阳→正印
    我生者: 同阴阳→伤官, 异阴阳→食神
    克我者: 同阴阳→七杀, 异阴阳→正官
    我克者: 同阴阳→偏财, 异阴阳→正财
    同我者: 同阴阳→比肩, 异阴阳→劫财
    """
    day_wx = STEM_WUXING[day_stem]
    other_wx = STEM_WUXING[other_stem]
    
    day_yang = stem_yang(day_stem)
    other_yang = stem_yang(other_stem)
    same_yin_yang = (day_yang == other_yang)
    
    # 同我者
    if day_wx == other_wx:
        return '比肩' if same_yin_yang else '劫财'
    
    # 生我者（印）
    if SHENG_ME[day_wx] == other_wx:
        return '偏印' if same_yin_yang else '正印'
    
    # 我生者（食伤）
    if SHENG[day_wx] == other_wx:
        return '伤官' if same_yin_yang else '食神'
    
    # 克我者（官杀）
    if KE_ME[day_wx] == other_wx:
        return '七杀' if same_yin_yang else '正官'
    
    # 我克者（财）
    if KE[day_wx] == other_wx:
        return '偏财' if same_yin_yang else '正财'
    
    return '?'


# ============ 第三步：天干五合表 ============

TIANGAN_WUHE = {
    ('甲', '己'): '土',
    ('己', '甲'): '土',
    ('乙', '庚'): '金',
    ('庚', '乙'): '金',
    ('丙', '辛'): '水',
    ('辛', '丙'): '水',
    ('丁', '壬'): '木',
    ('壬', '丁'): '木',
    ('戊', '癸'): '火',
    ('癸', '戊'): '火',
}


def get_wuhe(stem1, stem2):
    """
    查天干五合
    返回：合化五行，或None
    """
    return TIANGAN_WUHE.get((stem1, stem2))


# ============ 第四步：通根阴阳对应表 ============

# 按十干列：禄、刃、长生、库
# 验收：壬禄在亥不在子；乙长生在午不是亥
TONGGEN_TABLE = {
    '甲': {
        '禄': ['寅'],
        '刃': ['卯'],
        '长生': ['亥'],
        '库': ['未'],
    },
    '乙': {
        '禄': ['卯'],
        '中气': ['寅'],  # 寅中甲木中气，对乙来说是中气根
        '长生': ['午'],
        '库': ['未'],
    },
    '丙': {
        '禄': ['巳'],
        '刃': ['午'],
        '长生': ['寅'],
        '库': ['戌'],
    },
    '丁': {
        '禄': ['午'],
        '中气': ['巳'],
        '长生': ['酉'],
        '库': ['戌'],
    },
    '戊': {
        '禄': ['巳'],
        '长生': ['寅'],
        '库': ['戌'],
    },
    '己': {
        '禄': ['午'],
        '长生': ['酉'],
        '库': ['丑'],
    },
    '庚': {
        '禄': ['申'],
        '刃': ['酉'],
        '长生': ['巳'],
        '库': ['丑'],
    },
    '辛': {
        '禄': ['酉'],
        '中气': ['申'],
        '长生': ['子'],
        '库': ['丑'],
    },
    '壬': {
        '禄': ['亥'],
        '刃': ['子'],
        '长生': ['申'],
        '库': ['辰'],
    },
    '癸': {
        '禄': ['子'],
        '长生': ['卯'],
        '库': ['辰'],
    },
}


def get_tonggen_strength(stem, branch):
    """
    查天干在某地支的通根强度
    
    返回：禄刃 / 本气 / 中气 / 长生 / 库 / 无根
    """
    if stem not in TONGGEN_TABLE:
        return '无根'
    
    table = TONGGEN_TABLE[stem]
    
    if branch in table.get('禄', []) or branch in table.get('刃', []):
        return '禄刃'
    if branch in table.get('本气', []):
        return '本气'
    if branch in table.get('中气', []):
        return '中气'
    if branch in table.get('长生', []):
        return '长生'
    if branch in table.get('库', []):
        return '库'
    
    return '无根'


# ============ 验收测试 ============

if __name__ == '__main__':
    print('=== 阴阳类型系统验收 ===')
    print()
    
    # 1. 天干阴阳表
    print('【1. 天干阴阳表】')
    print(f'阳干: {YANG_STEMS}')
    print(f'阴干: {YIN_STEMS}')
    print()
    
    # 2. 十神派生规则验收
    print('【2. 十神派生规则验收】')
    
    # 对乙日主查壬 → 正印
    result = get_shishen('乙', '壬')
    expected = '正印'
    print(f'乙见壬: {result} (预期: {expected}) {"✅" if result == expected else "❌"}')
    
    # 对乙日主查癸 → 偏印(枭)
    result = get_shishen('乙', '癸')
    expected = '偏印'
    print(f'乙见癸: {result} (预期: {expected}) {"✅" if result == expected else "❌"}')
    
    # 对甲日主查庚 → 七杀
    result = get_shishen('甲', '庚')
    expected = '七杀'
    print(f'甲见庚: {result} (预期: {expected}) {"✅" if result == expected else "❌"}')
    
    # 对甲日主查辛 → 正官
    result = get_shishen('甲', '辛')
    expected = '正官'
    print(f'甲见辛: {result} (预期: {expected}) {"✅" if result == expected else "❌"}')
    
    print()
    
    # 3. 天干五合表验收
    print('【3. 天干五合表验收】')
    
    # 乙庚合金
    result = get_wuhe('乙', '庚')
    expected = '金'
    print(f'乙庚合: {result} (预期: {expected}) {"✅" if result == expected else "❌"}')
    
    # 甲己合土
    result = get_wuhe('甲', '己')
    expected = '土'
    print(f'甲己合: {result} (预期: {expected}) {"✅" if result == expected else "❌"}')
    
    print()
    
    # 4. 通根阴阳对应表验收
    print('【4. 通根阴阳对应表验收】')
    
    # 壬禄在亥
    result = get_tonggen_strength('壬', '亥')
    expected = '禄刃'
    print(f'壬@亥: {result} (预期: {expected}) {"✅" if result == expected else "❌"}')
    
    # 壬禄不在子
    result = get_tonggen_strength('壬', '子')
    expected = '禄刃'  # 子是刃
    print(f'壬@子: {result} (预期: {expected}) {"✅" if result == expected else "❌"}')
    
    # 乙长生在午
    result = get_tonggen_strength('乙', '午')
    expected = '长生'
    print(f'乙@午: {result} (预期: {expected}) {"✅" if result == expected else "❌"}')
    
    # 乙长生不在亥
    result = get_tonggen_strength('乙', '亥')
    expected = '无根'
    print(f'乙@亥: {result} (预期: {expected}) {"✅" if result == expected else "❌"}')
    
    print()
    print('=== 验收完成 ===')
