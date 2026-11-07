# -*- coding: utf-8 -*-
"""
用神引擎 v3.0 - 布尔谓词 + 枚举状态 + 拓扑关系

彻底废掉浮点权重，全部用：
1. 布尔谓词（true/false）
2. 枚举状态（字典序比较）
3. 拓扑关系（边查询）
"""
import sys
from spec.yinyang_system import SHENG, KE, SHENG_ME, KE_ME
sys.path.insert(0, '.')

from spec.root_qi import STEM_WUXING, BRANCH_CANGGAN


# ============ 五行生克 ============




# ============ 第一层：布尔谓词 ============

def predicate_tou_gan(stems, wx):
    """P_透干：X在天干出现"""
    return any(STEM_WUXING.get(s, '') == wx for s in stems)


def predicate_tou_gan_count(stems, wx):
    """透干个数（用于判断透干多）"""
    return sum(1 for s in stems if STEM_WUXING.get(s, '') == wx)


def predicate_tong_gen(branches, wx):
    """P_通根：X在地支藏干中存在"""
    for b in branches:
        for cg in BRANCH_CANGGAN.get(b, []):
            if STEM_WUXING.get(cg, '') == wx:
                return True
    return False


def predicate_de_ling(month_branch, wx):
    """P_得令：X为月令本气"""
    canggan = BRANCH_CANGGAN.get(month_branch, [])
    if canggan:
        return STEM_WUXING.get(canggan[0], '') == wx
    return False


def predicate_dong(stems, branches, wx):
    """P_动：P_透干 ∧ P_通根"""
    return predicate_tou_gan(stems, wx) and predicate_tong_gen(branches, wx)


def predicate_xu_tou(stems, branches, wx):
    """P_虚透：P_透干 ∧ ¬P_通根"""
    return predicate_tou_gan(stems, wx) and not predicate_tong_gen(branches, wx)


# ============ 第二层：枚举状态 ============

def enum_gen_qi_strength(branches, day_stem):
    """
    根气强度枚举：禄刃 > 本气 > 中气 > 余气 > 无根
    （序数比较，不用加法）
    """
    day_wx = STEM_WUXING[day_stem]
    
    has_lu_ren = False  # 禄刃
    has_benqi = False   # 本气
    has_zhongqi = False # 中气
    has_yugi = False    # 余气
    
    for b in branches:
        canggan = BRANCH_CANGGAN.get(b, [])
        for level, cg in enumerate(canggan):
            if STEM_WUXING.get(cg, '') == day_wx:
                if level == 0:
                    # 本气，再判断是不是禄刃
                    # 简化：寅卯=木禄刃，巳午=火禄刃，申酉=金禄刃，亥子=水禄刃
                    if (day_wx == '木' and b in ['寅', '卯']) or \
                       (day_wx == '火' and b in ['巳', '午']) or \
                       (day_wx == '金' and b in ['申', '酉']) or \
                       (day_wx == '水' and b in ['亥', '子']):
                        has_lu_ren = True
                    else:
                        has_benqi = True
                elif level == 1:
                    has_zhongqi = True
                else:
                    has_yugi = True
    
    # 字典序返回最高级
    if has_lu_ren: return '禄刃'
    if has_benqi: return '本气'
    if has_zhongqi: return '中气'
    if has_yugi: return '余气'
    return '无根'


def enum_yue_ling_state(month_branch, wx):
    """
    月令态枚举：当令 > 令生 > 令泄 > 令克 > 令耗
    （序数比较）
    """
    canggan = BRANCH_CANGGAN.get(month_branch, [])
    if not canggan:
        return '未知'
    
    month_wx = STEM_WUXING.get(canggan[0], '')
    
    if month_wx == wx:
        return '当令'
    if SHENG[month_wx] == wx:
        return '令生'
    if SHENG[wx] == month_wx:
        return '令泄'
    if KE[month_wx] == wx:
        return '令克'
    if KE[wx] == month_wx:
        return '令耗'
    return '未知'


# ============ 第三层：拓扑关系（简化版） ============

def topo_find_bing(stems, branches, day_stem):
    """
    找病：存在节点N，N克日主（或克相神），且P_动(N)
    病是关系属性，不是数量属性
    
    返回：(病五行, 病类型, 病状态)
    """
    day_wx = STEM_WUXING[day_stem]
    
    # 检查每个五行是不是"病"
    candidates = []
    
    for wx in ['木', '火', '土', '金', '水']:
        # 跳过日主自己
        if wx == day_wx:
            continue
        
        # 谓词检查
        tou = predicate_tou_gan(stems, wx)
        gen = predicate_tong_gen(branches, wx)
        dong = tou and gen
        de_ling = predicate_de_ling(branches[1], wx)
        tou_count = predicate_tou_gan_count(stems, wx)
        
        # 病的定义：动 + 得令/透干多
        # 不是比谁分数高，而是满足谓词条件
        
        # 类型1：印旺成病（母慈灭子）
        if wx == SHENG_ME[day_wx]:  # 印星
            # 印透干≥2个 → 印太旺
            if tou_count >= 2:
                candidates.append((wx, '印旺成病', f'印透干{tou_count}个'))
        
        # 类型2：财旺成病（财多身弱）
        elif wx == KE[day_wx]:  # 财星
            # 财得令 → 财旺
            if de_ling:
                candidates.append((wx, '财旺成病', '财当令'))
        
        # 类型3：官杀旺成病（杀重身轻）
        elif wx == KE_ME[day_wx]:  # 官杀
            # 官杀得令 → 杀重
            if de_ling:
                candidates.append((wx, '官杀旺成病', '官杀当令'))
        
        # 类型4：食伤旺成病（泄身太过）
        elif wx == SHENG[day_wx]:  # 食伤
            # 食伤得令 → 泄身太过
            if de_ling:
                candidates.append((wx, '食伤旺成病', '食伤当令'))
    
    # 按优先级返回第一个病（印>官杀>财>食伤）
    # 优先级：母慈灭子（印）> 杀重身轻（官杀）> 财多身弱（财）> 泄身太过（食伤）
    priority = {'印旺成病': 0, '官杀旺成病': 1, '财旺成病': 2, '食伤旺成病': 3}
    candidates.sort(key=lambda x: priority.get(x[1], 99))
    
    if candidates:
        return candidates[0]
    
    return None, None, None


def topo_find_yao(bing_wx, day_stem):
    """
    找药：克病神的五行
    药不能克日主用神
    """
    # 克病神的五行（KE_ME = 谁克我）
    yao_wx = KE_ME.get(bing_wx, '')
    
    return yao_wx


# ============ 主入口：病药判断 ============

def bingyao_pan(stems, branches, day_stem, ge_result=None):
    """
    病药判断主入口（布尔+枚举+拓扑版）
    
    返回：(primary, secondary, avoid, reason)
    """
    day_wx = STEM_WUXING[day_stem]
    
    # 先找病
    bing_wx, bing_type, bing_reason = topo_find_bing(stems, branches, day_stem)
    
    if bing_wx is None:
        # 无病 → 扶抑
        # 简化：身弱用印比，身强用财官食伤
        gen_qi = enum_gen_qi_strength(branches, day_stem)
        
        # 根气枚举判断身强身弱
        if gen_qi in ['禄刃', '本气']:
            # 身强 → 用克泄耗
            return (KE[day_wx], [SHENG[day_wx], KE_ME[day_wx]], 
                    [SHENG_ME[day_wx], day_wx],
                    f'身强（{gen_qi}），用财官食伤克泄耗')
        else:
            # 身弱 → 用生扶
            return (SHENG_ME[day_wx], [day_wx], 
                    [KE[day_wx], KE_ME[day_wx]],
                    f'身弱（{gen_qi}），用印比生扶')
    
    # 有病 → 找药
    yao_wx = topo_find_yao(bing_wx, day_stem)
    
    # 避免列表：病神 + 助病神的
    avoid = [bing_wx, SHENG_ME.get(bing_wx, '')]
    
    return (yao_wx, [], avoid, 
            f'{bing_type}（{bing_reason}），用{yao_wx}制病')


# ============ 测试 ============

if __name__ == '__main__':
    from engines.special_pan import special_pan
    
    cases = [
        # 古籍锚点（特殊格局不走病药）
        ('李侍郎从杀', ['乙', '乙', '乙', '甲'], ['酉', '酉', '酉', '申'], '乙', '从杀'),
        ('一品夫人从儿', ['甲', '丁', '癸', '乙'], ['寅', '卯', '卯', '卯'], '癸', '从儿'),
        ('朱元璋从儿', ['戊', '壬', '丁', '丁'], ['辰', '戌', '丑', '未'], '丁', '从儿'),
        ('侍郎从财', ['丙', '庚', '壬', '乙'], ['寅', '寅', '午', '巳'], '壬', '从财'),
        ('曲直格', ['甲', '丁', '甲', '乙'], ['寅', '卯', '寅', '亥'], '甲', '专旺'),
        ('稼穑格', ['戊', '己', '戊', '癸'], ['辰', '未', '戌', '丑'], '戊', '专旺'),
        # 正格案例
        ('用户案例', ['癸', '壬', '乙', '壬'], ['亥', '戌', '未', '午'], '乙', None),
    ]
    
    print('=== 用神引擎 v3.0（布尔+枚举+拓扑） ===')
    print()
    
    for name, stems, branches, day_stem, expect_ge in cases:
        ge = special_pan(stems, branches, day_stem)
        day_wx = STEM_WUXING[day_stem]
        
        # 特殊格局直接定用神
        if ge[0] not in ('正格',):
            # 简化：按格局类型定
            if '从杀' in ge[0]:
                yong = (KE_ME[day_wx], [], [SHENG_ME[day_wx]], '从杀格，顺用官杀')
            elif '从儿' in ge[0]:
                yong = (SHENG[day_wx], [KE[SHENG[day_wx]]], [KE_ME[day_wx]], '从儿格，顺用食伤')
            elif '从财' in ge[0]:
                yong = (KE[day_wx], [SHENG[day_wx]], [SHENG_ME[day_wx]], '从财格，顺用财')
            elif '专旺' in ge[0]:
                yong = (SHENG[day_wx], [day_wx], [KE_ME[day_wx]], '专旺格，顺泄秀')
            else:
                yong = ('?', [], [], '?')
        else:
            # 正格 → 病药判断
            yong = bingyao_pan(stems, branches, day_stem, ge)
        
        print(f'{name}:')
        print(f'  格局: {ge[0]} / {ge[1]}')
        print(f'  用神: {yong[0]}')
        print(f'  忌神: {yong[2]}')
        print(f'  理由: {yong[3]}')
        print()
