"""tongshu.facts.bazi_facts — 八字基础事实表 (P0-FNDR-03)

设计原则:
- 本模块是「事实层」(facts layer), 无任何上层业务依赖
- 不 import tongshu.engines, tongshu.reasoning, tongshu.canonical 等
- 只定义原子事实常量 (天干→五行、天干→阴阳、地支→五行、五行生克、地支藏干)
- 上层模块 (bazi_ten_gods, bazi_engine, zi_ping_* 等) 均从此处导入事实

依赖方向 (User 第七轮审计要求):
  facts (本模块)
    ↓
  reasoning.bazi_ten_gods (canonical 十神引擎)
    ↓
  engines.bazi_engine (八字计算)

禁止反向依赖: bazi_engine / bazi_ten_gods 不得被本模块 import。

Evidence Sources:
- 《渊海子平·论五行所属》(E-YHZP-001~012) — 天干/地支五行
- 《子平真诠·论阴阳生克》(E-ZQ-051-001) — 五行生克
- 《子平真诠·论用神》(E-ZQ-052-001) — 十神命名（事实层只提供映射, 命名由 bazi_ten_gods 负责）
- 《渊海子平·论地支藏干》(E-YHZP-013~024) — 地支藏干主气/中气/余气
"""

from __future__ import annotations

# ============================================================================
# 天干基础事实
# ============================================================================

# 10 Heavenly Stems (天干)
HEAVENLY_STEMS = (
    "JIA", "YI", "BING", "DING", "WU", "JI", "GENG", "XIN", "REN", "GUI",
)

# 12 Earthly Branches (地支)
EARTHLY_BRANCHES = (
    "ZI", "CHOU", "YIN", "MAO", "CHEN", "SI",
    "WU", "WEI", "SHEN", "YOU", "XU", "HAI",
)

# Element of each stem (天干五行映射)
STEM_ELEMENT = {
    "JIA": "WOOD", "YI": "WOOD",
    "BING": "FIRE", "DING": "FIRE",
    "WU": "EARTH", "JI": "EARTH",
    "GENG": "METAL", "XIN": "METAL",
    "REN": "WATER", "GUI": "WATER",
}

# Yin/Yang of each stem (天干阴阳)
STEM_POLARITY = {
    "JIA": "YANG", "YI": "YIN",
    "BING": "YANG", "DING": "YIN",
    "WU": "YANG", "JI": "YIN",
    "GENG": "YANG", "XIN": "YIN",
    "REN": "YANG", "GUI": "YIN",
}


# ============================================================================
# 地支基础事实
# ============================================================================

# Element of each branch (地支五行映射)
BRANCH_ELEMENT = {
    # WATER 子亥
    "ZI":   "WATER",
    "HAI":  "WATER",
    # WOOD 寅卯
    "YIN":  "WOOD",
    "MAO":  "WOOD",
    # FIRE 巳午
    "SI":   "FIRE",
    "WU":   "FIRE",
    # METAL 申酉
    "SHEN": "METAL",
    "YOU":  "METAL",
    # EARTH 辰戌丑未 (四季土)
    "CHEN": "EARTH",
    "XU":   "EARTH",
    "CHOU": "EARTH",
    "WEI":  "EARTH",
}

# 地支藏干 (主气 first). Standard table.
# Each branch maps to ordered list of (stem, role) tuples.
# role ∈ {"main" (本气), "middle" (中气), "residual" (余气)}
BRANCH_HIDDEN_STEMS = {
    "ZI":   [("GUI", "main")],
    "CHOU": [("JI", "main"), ("GUI", "middle"), ("XIN", "residual")],
    "YIN":  [("JIA", "main"), ("BING", "middle"), ("WU", "residual")],
    "MAO":  [("YI", "main")],
    "CHEN": [("WU", "main"), ("YI", "middle"), ("GUI", "residual")],
    "SI":   [("BING", "main"), ("WU", "middle"), ("GENG", "residual")],
    "WU":   [("DING", "main"), ("JI", "middle")],
    "WEI":  [("JI", "main"), ("DING", "middle"), ("YI", "residual")],
    "SHEN": [("GENG", "main"), ("REN", "middle"), ("WU", "residual")],
    "YOU":  [("XIN", "main")],
    "XU":   [("WU", "main"), ("XIN", "middle"), ("DING", "residual")],
    "HAI":  [("REN", "main"), ("JIA", "middle")],
}

# Season by month-branch (季节 by 月支)
SEASON_BY_BRANCH = {
    "YIN": "SPRING", "MAO": "SPRING", "CHEN": "SPRING",
    "SI": "SUMMER", "WU": "SUMMER", "WEI": "SUMMER",
    "SHEN": "AUTUMN", "YOU": "AUTUMN", "XU": "AUTUMN",
    "HAI": "WINTER", "ZI": "WINTER", "CHOU": "WINTER",
}

# 杂气月 (辰戌丑未) — 《论杂气如何取用》专题处理
ZAGI_BRANCHES = {"CHEN", "XU", "CHOU", "WEI"}


# ============================================================================
# 五行关系事实
# ============================================================================

# 五行相生链 (X 生 GENERATES[X])
GENERATES = {
    "WOOD": "FIRE",
    "FIRE": "EARTH",
    "EARTH": "METAL",
    "METAL": "WATER",
    "WATER": "WOOD",
}

# 五行相克链 (X 克 CONTROLS[X])
CONTROLS = {
    "WOOD": "EARTH",
    "EARTH": "WATER",
    "WATER": "FIRE",
    "FIRE": "METAL",
    "METAL": "WOOD",
}


# ============================================================================
# 地支关系事实表 (12 地支六冲/六合/三合/三会/三刑 — 标准子平固定数据)
# ============================================================================

# P0-FNDR-05 (R-11 ⑨ 地支关系 audit fix): 关系事实表迁移到 facts 层
# 之前 bazi_engine 内部硬编码, 违反 single source of truth.
# 注意: 这些是"关系存在"事实表, 不含化气/刑义/五行属性等辨层属性.
# 化气/刑义由 bazi_ten_gods 引擎层 evaluate_*_transformation 单独判定.

# 地支六冲表 (six clashes) — 对称配对
BRANCH_CLASH = {
    "ZI": "WU", "WU": "ZI",
    "CHOU": "WEI", "WEI": "CHOU",
    "YIN": "SHEN", "SHEN": "YIN",
    "MAO": "YOU", "YOU": "MAO",
    "CHEN": "XU", "XU": "CHEN",
    "SI": "HAI", "HAI": "SI",
}
BRANCH_CLASH_PAIRS = (
    frozenset({"ZI", "WU"}),
    frozenset({"CHOU", "WEI"}),
    frozenset({"YIN", "SHEN"}),
    frozenset({"MAO", "YOU"}),
    frozenset({"CHEN", "XU"}),
    frozenset({"SI", "HAI"}),
)

# 地支六害表 (six harms) — 对称配对
BRANCH_HARM = {
    "ZI": "WEI", "WEI": "ZI",
    "CHOU": "WU", "WU": "CHOU",
    "YIN": "SI", "SI": "YIN",
    "MAO": "CHEN", "CHEN": "MAO",
    "SHEN": "HAI", "HAI": "SHEN",
    "YOU": "XU", "XU": "YOU",
}
BRANCH_HARM_PAIRS = (
    frozenset({"ZI", "WEI"}),
    frozenset({"CHOU", "WU"}),
    frozenset({"YIN", "SI"}),
    frozenset({"MAO", "CHEN"}),
    frozenset({"SHEN", "HAI"}),
    frozenset({"YOU", "XU"}),
)

# 地支六合(六组) — 关系存在事实, 化气五行由 evaluate_he_transformation 独立判定
# 子丑, 寅亥, 卯戌, 辰酉, 巳申, 午未
BRANCH_HE = (
    frozenset({"ZI", "CHOU"}),
    frozenset({"YIN", "HAI"}),
    frozenset({"MAO", "XU"}),
    frozenset({"CHEN", "YOU"}),
    frozenset({"SI", "SHEN"}),
    frozenset({"WU", "WEI"}),
)

# 地支三合局(四组) — 关系存在事实, 化气由 evaluate_sanhe_transformation 判定
# 申子辰, 亥卯未, 寅午戌, 巳酉丑
BRANCH_SANHE = (
    frozenset({"SHEN", "ZI", "CHEN"}),
    frozenset({"HAI", "MAO", "WEI"}),
    frozenset({"YIN", "WU", "XU"}),
    frozenset({"SI", "YOU", "CHOU"}),
)

# 地支三会局(四组) — 关系存在事实, 五行属性由 evaluate_sanhui_transformation 判定
# 寅卯辰东方木, 巳午未南方火, 申酉戌西方金, 亥子丑北方水
BRANCH_SANHUI = (
    frozenset({"YIN", "MAO", "CHEN"}),
    frozenset({"SI", "WU", "WEI"}),
    frozenset({"SHEN", "YOU", "XU"}),
    frozenset({"HAI", "ZI", "CHOU"}),
)

# 地支三刑(四组) — 关系存在事实, 刑义由 evaluate_xing_type 判定
# 注意: 三刑有三种结构:
#   1. 三支齐全刑: 寅巳申(无恩), 丑戌未(恃势)
#   2. 二支齐全刑: 子卯(无礼)
#   3. 自刑: 辰午酉亥同一支出现两次以上
BRANCH_SANXING_TRIPLE = (
    frozenset({"YIN", "SI", "SHEN"}),   # 寅巳申三刑
    frozenset({"CHOU", "XU", "WEI"}),   # 丑戌未三刑
)
BRANCH_SANXING_DOUBLE = (
    frozenset({"ZI", "MAO"}),            # 子卯二支刑
)
BRANCH_SANXING_SELF = frozenset({"CHEN", "WU", "YOU", "HAI"})  # 自刑地支集合


# ============================================================================
# 起运常量 — P0-FNDR-08 (R-14 ⑫ 起运 audit fix) 迁移
# ============================================================================
# 节气搜索窗口 (天): 安全上界, 任意两"节"之间的最大间隔 < 33 天.
# 用于 _calc_start_age 在 33 天内找到下一个/上一个"节".
MAX_JIEQI_SEARCH_DAYS = 33

# 3 天 = 1 岁 (传统命理起运换算规则).
# 这是当前顺天八字 Calculation Core 锁定的 canonical rule.
# 注意: 不同流派在"几日一岁"细节上可能略有差异, 当前采用 3 天/1 岁.
DAYS_PER_YEAR_OF_START_AGE = 3


# ============================================================================
# 空亡旬表 (六甲旬) — P0-FNDR-06 (R-12 ⑩ 空亡 audit fix) 迁移
# ============================================================================
# 60 甲子分 6 旬, 每旬 10 个干支. 旬内用掉 10 地支, 剩 2 个就是该旬空亡.
# 甲子旬(序号0-9)   空 戌 亥
# 甲戌旬(序号10-19) 空 申 酉
# 甲申旬(序号20-29) 空 午 未
# 甲午旬(序号30-39) 空 辰 巳
# 甲辰旬(序号40-49) 空 寅 卯
# 甲寅旬(序号50-59) 空 子 丑
KONG_WANG_BY_XUN = {
    0: ("XU", "HAI"),    # 甲子旬
    1: ("SHEN", "YOU"),  # 甲戌旬
    2: ("WU", "WEI"),    # 甲申旬
    3: ("CHEN", "SI"),   # 甲午旬
    4: ("YIN", "MAO"),   # 甲辰旬
    5: ("ZI", "CHOU"),   # 甲寅旬
}

# 60 甲子完整表 (干支对照, 用作空亡测试 Oracle 与事实表)
# 序号 0-59, (heavenly_stem, earthly_branch)
JIAZI_TABLE = (
    ("JIA", "ZI"),     # 0   甲子
    ("YI", "CHOU"),    # 1   乙丑
    ("BING", "YIN"),   # 2   丙寅
    ("DING", "MAO"),   # 3   丁卯
    ("WU", "CHEN"),    # 4   戊辰
    ("JI", "SI"),      # 5   己巳
    ("GENG", "WU"),    # 6   庚午
    ("XIN", "WEI"),    # 7   辛未
    ("REN", "SHEN"),   # 8   壬申
    ("GUI", "YOU"),    # 9   癸酉
    ("JIA", "XU"),     # 10  甲戌
    ("YI", "HAI"),     # 11  乙亥
    ("BING", "ZI"),    # 12  丙子
    ("DING", "CHOU"),  # 13  丁丑
    ("WU", "YIN"),     # 14  戊寅
    ("JI", "MAO"),     # 15  己卯
    ("GENG", "CHEN"),  # 16  庚辰
    ("XIN", "SI"),     # 17  辛巳
    ("REN", "WU"),     # 18  壬午
    ("GUI", "WEI"),    # 19  癸未
    ("JIA", "SHEN"),   # 20  甲申
    ("YI", "YOU"),     # 21  乙酉
    ("BING", "XU"),    # 22  丙戌
    ("DING", "HAI"),   # 23  丁亥
    ("WU", "ZI"),      # 24  戊子
    ("JI", "CHOU"),    # 25  己丑
    ("GENG", "YIN"),   # 26  庚寅
    ("XIN", "MAO"),    # 27  辛卯
    ("REN", "CHEN"),   # 28  壬辰
    ("GUI", "SI"),     # 29  癸巳
    ("JIA", "WU"),     # 30  甲午
    ("YI", "WEI"),     # 31  乙未
    ("BING", "SHEN"),  # 32  丙申
    ("DING", "YOU"),   # 33  丁酉
    ("WU", "XU"),      # 34  戊戌
    ("JI", "HAI"),     # 35  己亥
    ("GENG", "ZI"),    # 36  庚子
    ("XIN", "CHOU"),   # 37  辛丑
    ("REN", "YIN"),    # 38  壬寅
    ("GUI", "MAO"),    # 39  癸卯
    ("JIA", "CHEN"),   # 40  甲辰
    ("YI", "SI"),      # 41  乙巳
    ("BING", "WU"),    # 42  丙午
    ("DING", "WEI"),   # 43  丁未
    ("WU", "SHEN"),    # 44  戊申
    ("JI", "YOU"),     # 45  己酉
    ("GENG", "XU"),    # 46  庚戌
    ("XIN", "HAI"),    # 47  辛亥
    ("REN", "ZI"),     # 48  壬子
    ("GUI", "CHOU"),   # 49  癸丑
    ("JIA", "YIN"),    # 50  甲寅
    ("YI", "MAO"),     # 51  乙卯
    ("BING", "CHEN"),  # 52  丙辰
    ("DING", "SI"),    # 53  丁巳
    ("WU", "WU"),      # 54  戊午
    ("JI", "WEI"),     # 55  己未
    ("GENG", "SHEN"),  # 56  庚申
    ("XIN", "YOU"),    # 57  辛酉
    ("REN", "XU"),     # 58  壬戌
    ("GUI", "HAI"),    # 59  癸亥
)
# 60 甲子索引: (heavenly_stem, earthly_branch) -> 序号 0-59
JIAZI_INDEX = {pair: i for i, pair in enumerate(JIAZI_TABLE)}

# 空亡辅助: 旬内 10 地支集合 (不含空亡 2 个)
XUN_BRANCHES = {
    0: ("ZI", "CHOU", "YIN", "MAO", "CHEN", "SI", "WU", "WEI", "SHEN", "YOU"),  # 甲子旬
    1: ("XU", "HAI", "ZI", "CHOU", "YIN", "MAO", "CHEN", "SI", "WU", "WEI"),   # 甲戌旬
    2: ("SHEN", "YOU", "XU", "HAI", "ZI", "CHOU", "YIN", "MAO", "CHEN", "SI"), # 甲申旬
    3: ("WU", "WEI", "SHEN", "YOU", "XU", "HAI", "ZI", "CHOU", "YIN", "MAO"),  # 甲午旬
    4: ("CHEN", "SI", "WU", "WEI", "SHEN", "YOU", "XU", "HAI", "ZI", "CHOU"),  # 甲辰旬
    5: ("YIN", "MAO", "CHEN", "SI", "WU", "WEI", "SHEN", "YOU", "XU", "HAI"),  # 甲寅旬
}

# ============================================================================
# 地支阴阳 — P0-FNDR-11 (Bazi Foundation Contract 28类 Fact 补齐)
# 子平体系地支阴阳: 阳=子寅辰午申戌, 阴=丑卯巳未酉亥
# 依据: 《渊海子平·论地支阴阳所属》(与地支五行同章)
# ============================================================================
BRANCH_POLARITY = {
    "ZI":   "YANG",
    "CHOU": "YIN",
    "YIN":  "YANG",
    "MAO":  "YIN",
    "CHEN": "YANG",
    "SI":   "YIN",
    "WU":   "YANG",
    "WEI":  "YIN",
    "SHEN": "YANG",
    "YOU":  "YIN",
    "XU":   "YANG",
    "HAI":  "YIN",
}


# ============================================================================
# 天干相冲表 — P0-FNDR-11 (Bazi Foundation Contract 28类 Fact 补齐)
# 甲庚冲、乙辛冲、丙壬冲、丁癸冲; 戊己土居中央不冲。
# 依据: 《渊海子平·论干支相冲》 (E-YHZP-030-001)
# ============================================================================
STEM_CLASH = (
    frozenset({"JIA", "GENG"}),
    frozenset({"YI", "XIN"}),
    frozenset({"BING", "REN"}),
    frozenset({"DING", "GUI"}),
)


# ============================================================================
# 地支六破表 — P0-FNDR-11 (Bazi Foundation Contract 28类 Fact 补齐)
# 子酉、丑辰、寅亥、卯午、巳申、未戌 (六组, 对称)。
# 依据: 《三命通会·论地支相破》 (E-SMTH-001-001)
# ============================================================================
BRANCH_PO = {
    "ZI":   "YOU",  "YOU":  "ZI",
    "CHOU": "CHEN", "CHEN": "CHOU",
    "YIN":  "HAI",  "HAI":  "YIN",
    "MAO":  "WU",   "WU":   "MAO",
    "SI":   "SHEN", "SHEN": "SI",
    "WEI":  "XU",   "XU":   "WEI",
}
BRANCH_PO_PAIRS = (
    frozenset({"ZI", "YOU"}),
    frozenset({"CHOU", "CHEN"}),
    frozenset({"YIN", "HAI"}),
    frozenset({"MAO", "WU"}),
    frozenset({"SI", "SHEN"}),
    frozenset({"WEI", "XU"}),
)


# ============================================================================
# 神煞事实表 — P0-FNDR-11 (Bazi Foundation Contract 28类 Fact 补齐)
# 只存"查法映射"这一确定性事实; 不含任何吉凶断语。
# 口径: 天乙/文昌/羊刃/金舆 以日干查; 驿马/华盖/将星/劫煞/亡神/孤辰寡宿 以年支查;
#       桃花(咸池) 以年支查 (见 bazi_engine.PEACH_BLOSSOM_BY_YEAR, 《五行精纪·论咸池》)。
# 依据: 《渊海子平·论神煞》(E-YHZP-040-001~010)
# ============================================================================

# 天乙贵人 (以日干查): 甲戊庚牛羊, 乙己鼠猴乡, 丙丁猪鸡位, 壬癸兔蛇藏, 六辛逢马虎
TIAN_YI_BY_DAY = {
    "JIA": ("CHOU", "WEI"), "WU": ("CHOU", "WEI"), "GENG": ("CHOU", "WEI"),
    "YI":  ("ZI", "SHEN"),  "JI": ("ZI", "SHEN"),
    "BING": ("HAI", "YOU"), "DING": ("HAI", "YOU"),
    "REN": ("MAO", "SI"),   "GUI": ("MAO", "SI"),
    "XIN": ("WU", "YIN"),
}

# 文昌贵人 (以日干查): 甲巳 乙午 丙戊申 丁己酉 庚亥 辛子 壬寅 癸卯
WEN_CHANG_BY_DAY = {
    "JIA": "SI", "YI": "WU", "BING": "SHEN", "DING": "YOU",
    "WU": "SHEN", "JI": "YOU", "GENG": "HAI", "XIN": "ZI",
    "REN": "YIN", "GUI": "MAO",
}

# 羊刃 (以日干查, 取阳干帝旺; 阴干不取刃 — 主流口径)
YANG_REN_BY_DAY = {
    "JIA": "MAO", "BING": "WU", "WU": "WU", "GENG": "YOU", "REN": "ZI",
}

# 金舆 (以日干查): 甲龙乙蛇丙戊羊 丁己猴 庚犬辛猪 壬牛癸虎
JIN_YU_BY_DAY = {
    "JIA": "CHEN", "YI": "SI", "BING": "WEI", "DING": "SHEN",
    "WU": "WEI", "JI": "SHEN", "GENG": "XU", "XIN": "HAI",
    "REN": "CHOU", "GUI": "YIN",
}

# 以年支所入三合局查: 驿马/华盖/将星/劫煞/亡神 (五个神煞共用同一三合分组)
SHEN_SHA_BY_SANHE = {
    frozenset({"SHEN", "ZI", "CHEN"}): {"YI_MA": "YIN", "HUA_GAI": "CHEN", "JIANG_XING": "ZI", "JIE_SHA": "SI", "WANG_SHEN": "HAI"},
    frozenset({"YIN", "WU", "XU"}):     {"YI_MA": "SHEN", "HUA_GAI": "XU", "JIANG_XING": "WU", "JIE_SHA": "HAI", "WANG_SHEN": "SI"},
    frozenset({"SI", "YOU", "CHOU"}):   {"YI_MA": "HAI", "HUA_GAI": "CHOU", "JIANG_XING": "YOU", "JIE_SHA": "YIN", "WANG_SHEN": "SHEN"},
    frozenset({"HAI", "MAO", "WEI"}):   {"YI_MA": "SI", "HUA_GAI": "WEI", "JIANG_XING": "MAO", "JIE_SHA": "SHEN", "WANG_SHEN": "YIN"},
}

# 孤辰寡宿 (以年支查): (孤辰, 寡宿)
GU_CHEN_GU_SU_BY_YEAR = {
    frozenset({"HAI", "ZI", "CHOU"}): ("YIN", "XU"),
    frozenset({"YIN", "MAO", "CHEN"}): ("SI", "CHOU"),
    frozenset({"SI", "WU", "WEI"}): ("SHEN", "CHEN"),
    frozenset({"SHEN", "YOU", "XU"}): ("HAI", "WEI"),
}

# ===== P0 德贵神煞查表 (五行精纪卷二十 L2007-L2092 / 三命通会 L1336-L1743) =====
# 天德 (按月支查天德支, L2026 神白经"正丁二坤宫三壬四辛同五亥六是甲七癸八艮宫九丙十乙处子巳必有功庚居丑月内";
#   口诀取干名/宫名, 天德支=该干之禄: 丁→午 壬→亥 辛→酉 甲→寅 癸→子 丙→巳 乙→卯 庚→申, 坤=申 艮=寅)
# 天德 (月查干/卦, 五行精纪 L1921-1965: 正月丁 二月坤(申) 三月壬 四月辛 五月亥
#   六月甲 七月癸 八月艮(寅) 九月丙 十月乙 十一月巽(巳) 十二月庚; 三命通会
#   L1491 天德为十二干/卦之神, L3075/L3078/L3084 正印偏印论同源)
#   2026-10-21 修正: 原表误作"天德干之禄支"(如申月癸→子), 改回标准干表
TIAN_DE_BY_MONTH = {
    "YIN": "DING", "MAO": "SHEN", "CHEN": "REN", "SI": "XIN",
    "WU": "HAI", "WEI": "JIA", "SHEN": "GUI", "YOU": "YIN",
    "XU": "BING", "HAI": "YI", "ZI": "SI", "CHOU": "GENG",
}
# 月德 (按三合组月查德干, L2038 神白经"正五九月在丙二六十月在甲三七十一月在壬四八十二月在庚")
YUE_DE_GAN_BY_SANHE = {
    frozenset({"YIN", "WU", "XU"}): "BING",
    frozenset({"HAI", "MAO", "WEI"}): "JIA",
    frozenset({"SHEN", "ZI", "CHEN"}): "REN",
    frozenset({"SI", "YOU", "CHOU"}): "GENG",
}
# 天赦日 (按季查日柱, L2046"春戊寅夏甲午秋戊申冬甲子")
TIAN_SHE_DAY_BY_SEASON = {
    frozenset({"YIN", "MAO", "CHEN"}): ("WU", "YIN"),   # 春
    frozenset({"SI", "WU", "WEI"}): ("JIA", "WU"),      # 夏
    frozenset({"SHEN", "YOU", "XU"}): ("WU", "SHEN"),   # 秋
    frozenset({"HAI", "ZI", "CHOU"}): ("JIA", "ZI"),    # 冬
}
# 太极贵 (按年干查支, L2008"甲乙生人子午中丙丁卯酉定亨通戊己两干临四季庚辛寅亥禄盈丰壬巳癸申偏喜美")
TAI_JI_GUI_BY_STEM = {
    "JIA": ("ZI", "WU"), "YI": ("ZI", "WU"),
    "BING": ("MAO", "YOU"), "DING": ("MAO", "YOU"),
    "WU": ("CHEN", "XU", "CHOU", "WEI"), "JI": ("CHEN", "XU", "CHOU", "WEI"),
    "GENG": ("YIN", "HAI"), "XIN": ("YIN", "HAI"),
    "REN": ("SI",), "GUI": ("SHEN",),
}
# 文星贵 (按年干查支, L2014 林开五命"甲马乙蛇丙戊猴酉抬丁己亥辛求庚逢戊狗壬逢虎十位文星癸兔游")
WEN_XING_BY_STEM = {
    "JIA": "WU", "YI": "SI", "BING": "SHEN", "DING": "YOU",
    "WU": "SHEN", "JI": "YOU", "GENG": "XU", "XIN": "HAI",
    "REN": "YIN", "GUI": "MAO",
}
# 天印贵人 (按年干查支, L2016"甲在子寅中乙逢亥亦闻丁酉戊申位丙戊己羊宫庚辛马蛇是癸卯与壬龙")
TIAN_YIN_BY_STEM = {
    "JIA": ("ZI", "YIN"), "YI": ("HAI",), "BING": ("WEI",), "DING": ("YOU",),
    "WU": ("SHEN",), "JI": ("WEI",), "GENG": ("WU", "SI"), "XIN": ("WU", "SI"),
    "REN": ("CHEN",), "GUI": ("MAO",),
}
# 金舆 (三命通会 L1340"金舆常居禄前二辰"): 年干禄前二辰 — 与日干查法同表
JIN_YU_BY_STEM = dict(JIN_YU_BY_DAY)   # 甲辰乙巳丙未丁申戊未己申庚戌辛亥壬丑癸寅
# 德秀 (按三合组月查德干/秀干, 三命通会 L1613"寅午戌月丙丁为德戊癸为秀…")
DE_XIU_BY_SANHE = {
    frozenset({"YIN", "WU", "XU"}): ({"BING", "DING"}, {"WU", "GUI"}),
    frozenset({"SHEN", "ZI", "CHEN"}): ({"REN", "GUI", "WU", "JI"}, {"BING", "XIN", "JIA", "JI"}),
    frozenset({"SI", "YOU", "CHOU"}): ({"GENG", "XIN"}, {"YI", "GENG"}),
    frozenset({"HAI", "MAO", "WEI"}): ({"JIA", "YI"}, {"DING", "REN"}),
}
# 灾煞 (将星对冲, 三命通会 L1727"常居劫煞之前冲破将星…主血光横死")
ZAI_SHA_BY_SANHE = {
    frozenset({"SHEN", "ZI", "CHEN"}): "WU",
    frozenset({"YIN", "WU", "XU"}): "ZI",
    frozenset({"SI", "YOU", "CHOU"}): "MAO",
    frozenset({"HAI", "MAO", "WEI"}): "YOU",
}
# 天上三奇顺布 (三命通会 L1480"乙丙丁、甲戊庚…年月日时顺布为吉")
SAN_QI_TRIPLES = (("YI", "BING", "DING"), ("JIA", "WU", "GENG"))

# 地支 → 所在三合局 (供神煞查法复用)
BRANCH_SANHE_GROUP = {}
for _sanhe_group in (frozenset({"SHEN", "ZI", "CHEN"}), frozenset({"YIN", "WU", "XU"}),
                     frozenset({"SI", "YOU", "CHOU"}), frozenset({"HAI", "MAO", "WEI"})):
    for _b in _sanhe_group:
        BRANCH_SANHE_GROUP[_b] = _sanhe_group


# ============================================================================
# 胎元/胎息 顺进位映射 — P0-FNDR-11 (Bazi Foundation Contract 28类 Fact 补齐)
# 胎元 = 月柱天干进1位、月支进3位; 胎息 = 日柱天干进1位、日支进3位。
# 依据: 《三命通会·论胎元胎息》 (E-SMTH-002-001)
# ============================================================================
# 顺进 1 位 (天干): 甲→乙 → … → 癸→甲
STEM_NEXT = {
    "JIA": "YI", "YI": "BING", "BING": "DING", "DING": "WU", "WU": "JI",
    "JI": "GENG", "GENG": "XIN", "XIN": "REN", "REN": "GUI", "GUI": "JIA",
}
# 顺进 3 位 (地支): 子→卯 → … → 亥→寅
BRANCH_NEXT3 = {
    "ZI": "MAO", "CHOU": "CHEN", "YIN": "SI", "MAO": "WU", "CHEN": "WEI", "SI": "SHEN",
    "WU": "YOU", "WEI": "XU", "SHEN": "HAI", "YOU": "ZI", "XU": "CHOU", "HAI": "YIN",
}


# ============================================================================
# 十干禄元表 (干禄) — 禄命法核心 "禄马" 之首 (年本三元之干禄查法)
# 依据: 《三命通会·论十干禄》 (E-SMTH-004-001):
#       甲禄在寅, 乙禄在卯, 丙戊禄在巳, 丁己禄在午, 庚禄在申, 辛禄在酉,
#       壬禄在亥, 癸禄在子。 (戊己随丙丁, 火土同宫)
# ============================================================================
LU_BY_STEM = {
    "JIA": "YIN",   # 甲禄在寅
    "YI": "MAO",    # 乙禄在卯
    "BING": "SI",   # 丙禄在巳
    "DING": "WU",   # 丁禄在午
    "WU": "SI",     # 戊禄在巳 (火土同宫)
    "JI": "WU",     # 己禄在午 (火土同宫)
    "GENG": "SHEN", # 庚禄在申
    "XIN": "YOU",   # 辛禄在酉
    "REN": "HAI",   # 壬禄在亥
    "GUI": "ZI",    # 癸禄在子
}

# ============================================================================
# 六十甲子纳音 30 种 → 五行 (三元之"身"五行, 盲派 NAYIN_FIVE_ELEMENT 同源收编)
# 依据: 《三命通会·论纳音》 (E-SMTH-003-001), 与 NAYIN_60 同源同值。
# 收编说明: 原副本在 blind_bazi_engine (双源漂移风险), 此处为单源真相。
# ============================================================================
NAYIN_FIVE_ELEMENT = {
    '海中金': 'METAL', '剑锋金': 'METAL', '白蜡金': 'METAL', '沙中金': 'METAL',
    '金箔金': 'METAL', '钗钏金': 'METAL',
    '大林木': 'WOOD', '杨柳木': 'WOOD', '松柏木': 'WOOD', '平地木': 'WOOD',
    '桑柘木': 'WOOD', '石榴木': 'WOOD',
    '涧下水': 'WATER', '泉中水': 'WATER', '长流水': 'WATER', '天河水': 'WATER',
    '大溪水': 'WATER', '大海水': 'WATER',
    '炉中火': 'FIRE', '山头火': 'FIRE', '霹雳火': 'FIRE', '山下火': 'FIRE',
    '覆灯火': 'FIRE', '天上火': 'FIRE',
    '路旁土': 'EARTH', '城头土': 'EARTH', '屋上土': 'EARTH', '壁上土': 'EARTH',
    '大驿土': 'EARTH', '沙中土': 'EARTH',
}


# ============================================================================
# 六十甲子纳音表 — P0-FNDR-11 补充 (八字引擎四柱纳音输出)
# 依据: 《三命通会·论纳音》 (E-SMTH-003-001); 确定性固定表, 无历法歧义。
# ============================================================================
NAYIN_60 = {
    ("JIA", "ZI"): "海中金", ("YI", "CHOU"): "海中金",
    ("BING", "YIN"): "炉中火", ("DING", "MAO"): "炉中火",
    ("WU", "CHEN"): "大林木", ("JI", "SI"): "大林木",
    ("GENG", "WU"): "路旁土", ("XIN", "WEI"): "路旁土",
    ("REN", "SHEN"): "剑锋金", ("GUI", "YOU"): "剑锋金",
    ("JIA", "XU"): "山头火", ("YI", "HAI"): "山头火",
    ("BING", "ZI"): "涧下水", ("DING", "CHOU"): "涧下水",
    ("WU", "YIN"): "城头土", ("JI", "MAO"): "城头土",
    ("GENG", "CHEN"): "白蜡金", ("XIN", "SI"): "白蜡金",
    ("REN", "WU"): "杨柳木", ("GUI", "WEI"): "杨柳木",
    ("JIA", "SHEN"): "泉中水", ("YI", "YOU"): "泉中水",
    ("BING", "XU"): "屋上土", ("DING", "HAI"): "屋上土",
    ("WU", "ZI"): "霹雳火", ("JI", "CHOU"): "霹雳火",
    ("GENG", "YIN"): "松柏木", ("XIN", "MAO"): "松柏木",
    ("REN", "CHEN"): "长流水", ("GUI", "SI"): "长流水",
    ("JIA", "WU"): "沙中金", ("YI", "WEI"): "沙中金",
    ("BING", "SHEN"): "山下火", ("DING", "YOU"): "山下火",
    ("WU", "XU"): "平地木", ("JI", "HAI"): "平地木",
    ("GENG", "ZI"): "壁上土", ("XIN", "CHOU"): "壁上土",
    ("REN", "YIN"): "金箔金", ("GUI", "MAO"): "金箔金",
    ("JIA", "CHEN"): "覆灯火", ("YI", "SI"): "覆灯火",
    ("BING", "WU"): "天河水", ("DING", "WEI"): "天河水",
    ("WU", "SHEN"): "大驿土", ("JI", "YOU"): "大驿土",
    ("GENG", "XU"): "钗钏金", ("XIN", "HAI"): "钗钏金",
    ("REN", "ZI"): "桑柘木", ("GUI", "CHOU"): "桑柘木",
    ("JIA", "YIN"): "大溪水", ("YI", "MAO"): "大溪水",
    ("BING", "CHEN"): "沙中土", ("DING", "SI"): "沙中土",
    ("WU", "WU"): "天上火", ("JI", "WEI"): "天上火",
    ("GENG", "SHEN"): "石榴木", ("XIN", "YOU"): "石榴木",
    ("REN", "XU"): "大海水", ("GUI", "HAI"): "大海水",
}


EVIDENCE_IDS = {
    "STEM_ELEMENT": "E-YHZP-001~010",          # 渊海子平·论天干五行所属
    "STEM_POLARITY": "E-YHZP-001~010",          # 渊海子平·论天干阴阳
    "BRANCH_ELEMENT": "E-YHZP-001~012",         # 渊海子平·论地支五行所属
    "BRANCH_HIDDEN_STEMS": "E-YHZP-013~024",    # 渊海子平·论地支藏干
    "GENERATES": "E-ZQ-051-001",                # 子平真诠·论阴阳生克
    "CONTROLS": "E-ZQ-051-001",                 # 子平真诠·论阴阳生克
    "SEASON_BY_BRANCH": "E-YHZP-025~028",       # 渊海子平·论四时月令
    "BRANCH_CLASH": "E-YHZP-002-001",           # 渊海子平·论地支六冲
    "BRANCH_HARM": "E-YHZP-003-001",            # 渊海子平·论地支六害
    "BRANCH_HE": "E-YHZP-005-001",              # 渊海子平·论地支六合
    "BRANCH_SANHE": "E-YHZP-006-001",           # 渊海子平·论地支三合
    "BRANCH_SANHUI": "E-DTS-145-001",           # 滴天髓·论地支三会方位
    "BRANCH_SANXING": "E-YHZP-007-001",         # 渊海子平·论地支三刑
    "KONG_WANG": "E-YHZP-008-001",              # 渊海子平·论空亡旬表
    "JIAZI_TABLE": "E-YHZP-009-001",
    "BRANCH_POLARITY": "E-YHZP-001~012",         # 渊海子平·论地支阴阳所属
    "STEM_CLASH": "E-YHZP-030-001",              # 渊海子平·论干支相冲
    "BRANCH_PO": "E-SMTH-001-001",               # 三命通会·论地支相破
    "TIAN_YI": "E-YHZP-040-001",                 # 渊海子平·论天乙贵人
    "WEN_CHANG": "E-YHZP-040-002",               # 渊海子平·论文昌贵人
    "YANG_REN": "E-YHZP-040-003",                # 渊海子平·论羊刃
    "JIN_YU": "E-YHZP-040-004",                  # 渊海子平·论金舆
    "YI_MA": "E-YHZP-040-005",                   # 渊海子平·论驿马
    "HUA_GAI": "E-YHZP-040-006",                 # 渊海子平·论华盖
    "JIANG_XING": "E-YHZP-040-007",              # 渊海子平·论将星
    "JIE_SHA": "E-YHZP-040-008",                 # 渊海子平·论劫煞
    "WANG_SHEN": "E-YHZP-040-009",               # 渊海子平·论亡神
    "GU_CHEN_GU_SU": "E-YHZP-040-010",           # 渊海子平·论孤辰寡宿
    "TAI_YUAN": "E-SMTH-002-001",                # 三命通会·论胎元胎息
    "NAYIN_60": "E-SMTH-003-001",                  # 三命通会·论纳音
    "LU_BY_STEM": "E-SMTH-004-001",                # 三命通会·论十干禄
    "NAYIN_FIVE_ELEMENT": "E-SMTH-003-001",        # 三命通会·论纳音 (与 NAYIN_60 同源)

    # 禄命法引擎证据 (五行精纪; 卷次已核原文正文卷标记, 详 luming/facts.py)
    "LM_WANG_XIANG": "E-WXJ-007-001",              # 五行精纪·卷七【五行旺相囚休死例】
    "LM_SAN_YUAN": "E-WXJ-009-001",                # 五行精纪·卷九 (金书命诀)
    "LM_HUA_QI": "E-WXJ-004-001",                  # 五行精纪·卷四【论合神化气】
    "LM_GUI_REN": "E-WXJ-014-001",                 # 五行精纪·卷十四【福星天乙贵人格】
    "LM_YI_MA": "E-WXJ-016-001",                   # 五行精纪·卷十六【驿马位歌】
    "LM_TAO_HUA": "E-WXJ-026-001",                 # 五行精纪·卷廿六【论咸池】
    "LM_HUA_GAI": "E-WXJ-020-001",                 # 五行精纪·卷二十 (华盖以三合之位入墓)
    "LM_GUI_REN_JIE_SHA": "E-WXJ-014-002",         # 五行精纪·卷十四 (烛神经: 贵人并劫煞/建禄)
    "LM_HE_XIAN_CHI": "E-WXJ-018-001",             # 五行精纪·卷十八 (烛神经: 合中有杀合咸池)
    "LM_XIAN_CHI_GUI_LU": "E-WXJ-026-002",         # 五行精纪·卷廿六 (烛神经: 咸池并贵人建禄)
    "LM_ER_YUN_GUI_REN": "E-WXJ-034-001",          # 五行精纪·卷卅四【论二运】
    "LM_ER_YUN_XIAN_CHI": "E-WXJ-034-002",         # 五行精纪·卷卅四 (烛神经: 二运见咸池)
    "LM_DA_YUN_LU_MA": "E-WXJ-033-001",            # 五行精纪·卷卅三【论大运】L4318
    "LM_DA_YUN_GUI_SHEN": "E-WXJ-033-002",         # 五行精纪·卷卅三【论大运】L4320
    "LM_ER_YUN_XI_HUI": "E-WXJ-034-003",           # 五行精纪·卷卅四 (三命钤: 二运喜会九式 L4342)
    "LM_ER_YUN_E_HUI": "E-WXJ-034-004",            # 五行精纪·卷卅四 (三命钤: 二运厄会九式 L4343)
    "LM_FU_YIN_FAN_YIN": "E-WXJ-033-003",          # 五行精纪·卷卅三【论大运】L4321
    "LM_TAI_SUI_ZHAI": "E-WXJ-034-005",            # 五行精纪·卷卅四 (三命钤: 太岁入宅 L4368)
    "LM_ZHUANG_MING": "E-WXJ-034-006",             # 五行精纪·卷卅四 (广信集: 撞命杀 L4371)
    "LM_TAI_SUI_XING_DAYUN": "E-WXJ-034-007",      # 五行精纪·卷卅四 (烛神经: 太岁刑大运 L4387)
    "LM_TAI_SUI_GU_SU": "E-WXJ-034-008",           # 五行精纪·卷卅四 (金书命诀: 太岁孤辰寡宿 L4386)

    # 禄命法缺口补齐 (第三批): 纳音链/三刑/六害/文昌/拱/将星/岁运冲合
    "LM_NAYIN_QI_SHU": "E-WXJ-008-001",            # 五行精纪·卷八 (阁东叟书: 纳音天地气数 L1473)
    "LM_WEN_CHANG": "E-WXJ-013-001",               # 五行精纪·卷十三【文昌贵】L2010 (年干表)
    "LM_JIA_LU_GONG_LU": "E-WXJ-015-002",          # 五行精纪·卷十五 (王氏注: 夹禄拱禄 L2288)
    "LM_SUI_YUN_GUI_MA_HE": "E-WXJ-016-002",       # 五行精纪·卷十六 (阎东叟: 岁运贵马相合大亨快 L2396)
    "LM_MA_YU_SUI_YUN_HE": "E-WXJ-016-003",        # 五行精纪·卷十六 (三命钤: 马与岁运合并迁官得禄 L2398)
    "LM_TAI_SUI_CHONG_MA": "E-WXJ-016-004",        # 五行精纪·卷十六 (论马: 太岁冲马为鞭策 L2447)
    "LM_JIANG_XING": "E-WXJ-020-002",              # 五行精纪·卷二十【将星】马后二辰 L2893
    "LM_LU_E_CHONG": "E-WXJ-021-001",              # 五行精纪·卷廿一 (阎东叟书: 禄最恶于冲 L3041)
    "LM_XING_NIAN_YUN_SANHE_ZAI": "E-WXJ-023-001", # 五行精纪·卷廿三 (凶神例: 忌行年运并时日三合为灾 L3150)
    "LM_SAN_XING": "E-WXJ-025-001",                # 五行精纪·卷廿五【论三刑】L3392
    "LM_LIU_HAI": "E-WXJ-025-002",                 # 五行精纪·卷廿五【论六害】L3420
    "LM_KONG_WANG": "E-WXJ-025-004",               # 五行精纪·卷廿五 (L3483 空亡止以年日所在/冲破反为福; L3484 同类冲最毒)
    "LM_KONG_WANG_ZANG_TOU": "E-WXJ-025-005",      # 五行精纪·卷廿五 (广集: 藏头空亡本是祸反为福, 戊己人带之大好 L3485)
    "LM_KONG_WANG_XU_SHENG": "E-WXJ-025-006",      # 五行精纪·卷廿五 (广集: 空亡被日时或运冲刑=虚声杀, 士人飞声走誉 L3484)
    "LM_YUAN_CHEN": "E-WXJ-024-001",               # 五行精纪·卷廿四【论元辰】L3345 (阳男阴女冲前一位/阴男阳女冲后一辰) + L3346 阎东叟书 (岁运临之如物当风) + L3348 三命钤
    "LM_QI_LIN_KU": "E-WXJ-025-003",               # 五行精纪·卷廿五 (鬼谷命格: 三刑遇昼夜贵人=麒麟窟 L3404)

    # 禄命法第四批: 大运纳音生克 + 魁罡 (SMTH 单源)
    "LM_DAYUN_NAYIN": "E-WXJ-008-001",             # 五行精纪·卷八 L1473 纳音气数 (大运纳音vs年命; 行年生克吉凶则 L4356)
    "LM_KUI_GANG": "E-SMTH-013-001",               # 三命通会·论魁罡 L2735 (四魁罡日; WXJ 无专条仅'辰戌魁罡之地'L700)
    "LM_HUA_GAI_GU_GUA": "E-SMTH-014-001",         # 三命通会·论将星华盖 L1133 (华盖多主孤寡总贵亦不免孤独; WXJ 华盖章仅吉面)

    # 禄命法第五批: 大运十二宫休旺 + 大运干支五行生克 (卷卅三论大运主纲)
    "LM_DAYUN_SHIGONG": "E-WXJ-033-001",           # 五行精纪·卷卅三【论大运】L4273-4277 (长生临官帝旺吉/衰病死绝凶/沐浴败乡凶)
    "LM_DAYUN_GANZHI": "E-WXJ-034-009",            # 五行精纪·卷卅四 L4355 (珞琭子: 比合则吉战克则凶) + L4356 (生克深浅)

    # 禄命法第六批: 流年应期层 (任意太岁: 冲年/刑冲压害分柱/岁运交战/真太岁征太岁/
    #                         死绝会集/空亡咸池/犯命/天罗地网)
    "LM_TAI_CHONG_NIAN": "E-WXJ-032-001",          # 五行精纪·卷卅二杂论 L4247-4248 (沉芝源髓: 太岁冲年亦深祸)
    "LM_TAI_CHONG_XING_HAI": "E-WXJ-034-010",      # 五行精纪·卷卅四 L4423 (广信集: 太岁刑冲压害生年月日时各主其灾)
    "LM_TAI_CHONG_DAYUN": "E-SMTH-015-002",        # 三命通会 L15572 (太岁冲运其祸重, 岁冲运罢官丧母实证)
    "LM_SUI_YUN_BING_LIN": "E-SMTH-015-001",       # 三命通会·论太岁 L954 (岁运并临, 劫财羊刃灾殃立至)
    "LM_ZHEN_ZHENG_TAI_SUI": "E-SMTH-015-001",     # 三命通会·论太岁 L954 (真太岁转趾煞/征太岁)
    "LM_FAN_YIN_FU_YIN": "E-SMTH-015-001",         # 三命通会·论太岁 L968 (返吟岁运与日相对/伏吟岁运压日, 不利六亲)
    "LM_TAI_KE_SHI": "E-WXJ-034-011",              # 五行精纪·卷卅四 L4421 (神白经: 太岁克生时亦身灾)
    "LM_TAI_DEATH_MEETING": "E-WXJ-031-001",       # 五行精纪·卷卅一论寿夭 L4113 (烛神经: 二运太岁死绝会集刑克定死)
    "LM_TAI_KONG_WANG": "E-WXJ-034-012",           # 五行精纪·卷卅四 L4411 (太岁至空亡年失脱破财)
    "LM_TAI_FAN_MING": "E-WXJ-034-013",            # 五行精纪·卷卅四 L4409 (太岁犯命三才刑克主疾病官灾死丧)
    "LM_TAI_XIAN_CHI": "E-WXJ-034-014",            # 五行精纪·卷卅四 L4411 (太岁见咸池年淫乱公事)
    "LM_TAI_YA_BENMING": "E-WXJ-034-015",          # 五行精纪·卷卅四 L4411 (岁压本命年主动为稽滞不快)
    "LM_TAI_GLM_FU": "E-WXJ-034-016",              # 五行精纪·卷卅四 L4409 (太岁加本命贵人禄马一切福神之地则吉)
    "LM_TAI_CHONG_NIAN_AN": "E-WXJ-034-017",       # 五行精纪·卷卅四 L4416 珞琭子 (掩冲岁临尚不为灾, 相生则吉相克则凶; 癸亥生乙巳岁不为灾忒例)
    "LM_TAI_TIANLUO_DIWANG": "E-SMTH-015-003",     # 三命通会 L9724 (辰巳地网戌亥天罗, 岁运并临克害夭亡)

    # 禄命法第七批: 原局喜忌层 (五行精纪卷七论五行一 L1254-1270)
    "LM_XI_JI_TABLE": "E-WXJ-007-002",             # 卷七【论金】【论木】【论水】【论火】【论土】四季喜忌+太过不及
    "LM_XI_JI_COUNT": "E-WXJ-007-002",             # 同上 (纳音五行数量统计驱动太过不及判定)
    "LM_XI_JI_EXCESS": "E-WXJ-007-003",            # 卷七 L1513 (生克制化: 水生木木通则水竭/木生火火旺则木焚/
                                                    #             火生土土旺而火痊/土生金金贵则土贱/金生水水旺则金沉)
    "LM_XI_JI_ADJUST": "E-WXJ-007-002",            # 卷七论五行: 冬水寒需火暖/夏火燥需水润 (季节调候)

    # 禄命法第八批: 逐柱纳音喜忌专条 (三命通会卷01释六十甲子性质吉凶)
    "LM_NAYIN_SPECIFIC": "E-SMTH-016-001",         # L166-343 每柱简版喜忌 + 剑锋金L477/杨柳木L548/大海水L309/桑柘木L296 详版专条

    # 禄命法第九批: 原局凶格组合 (2026-10-20 五行精纪命例方向 oracle 补齐)
    "LM_DUAN_MING_SHA": "E-WXJ-041-002",           # 卷卅五·论短命杀 (神白经 L4128-4132: 生日对时人短命/生年对月亦复是;
                                                    #   鬼谷要诀 L4132 甲寅丁酉戊申甲寅不出周岁死)
    "LM_SAN_HE_LIN_GUAN": "E-WXJ-033-002",         # 卷卅三 (广录 L3342: 巳酉丑三位全又有一位在申上者必主极刑;
                                                    #   玉黼亥卯未全又见两寅/戚世显虽贵显终被极刑)
    "LM_GUI_YIN": "E-WXJ-027-002",                 # 卷廿七 (天元变化书 L2726: 水命人得土印名曰鬼印,
                                                    #   支干无交涉者使鬼印; 癸巳一水不任两土气多所以贫贱)
    "LM_CHOU_SHI": "E-WXJ-012-005",                # 卷十二 (广录 L1245: 四柱不可犯丙戊二干, 若在寅辰上名仇雠晦气,
                                                    #   主招谤怨多与人竞; 逢之灾咎及其身,
    "LM_LU_MA_SI_JUE": "E-WXJ-024-005",             # 卷廿四 (金书命诀 L2455: 马为禄绝，四十二岁果失; 三命到巳并绝，乞食至死)
    "LM_BAO_GUA_JING_QI": "E-WXJ-030-002",          # 卷三十 (玉霄宝鉴 L3079: 包裹旌旗乃拱劫杀亡神…官虽卑亦作小监司) 非时刑祸不堪论)

    # 禄命法第十批: 羊刃/天罗地网/日主无气 + 吉格组合 (2026-10-20 六书命例 oracle 补齐)
    "LM_YANG_REN_CHONG_FENG": "E-SMTH-013-002",     # 三命通会·论羊刃 L957 (羊刃倒戈…项生恶疮头将堕死; 武官贵征"又皆是武官也")
    "LM_FENG_HUANG_ZHI": "E-SMTH-029-001",          # 三命通会·芝兰并秀 L2923 (四柱纯一不杂，多居两府之贵)
    "LM_GAN_ZHI_TONG_LEI": "E-LT-008-001",          # 兰台妙选 L8 (姚尚书丙申庚寅乙酉丁亥 贵人捧印格得地)
    "LM_TIAN_LUO_DI_WANG": "E-WXJ-L3534",           # 五行精纪·卷廿五 (金书命诀 L3534: 天罗地网重并者男妨妻女妨夫并绝嗣)
    "LM_RI_GAN_WU_QI": "E-WXJ-L3861",               # 五行精纪·卷廿五 (金书命诀 L3861: 日又在无气之地虽有官至老但携匪人)

    # SMTH 四主题切片 (2026-10-20 论疾病/论性情/论女命/论六亲)
    "LM_SMTH_DISEASE": "E-SMTH-014-002",           # 三命通会·卷十四 论疾病 (L3341-3353 五行受亏主疾)
    "LM_SMTH_TEMPER": "E-SMTH-012-002",            # 三命通会·卷十二 论性情 (L3315/3321/3324 五行太过主性)
    "LM_SMTH_NV_MING": "E-SMTH-013-003",           # 三命通会·卷十三 论女命 (L3391/L3423/L3525 夫星子星/二德/总歌)
    "LM_SMTH_LIU_QIN": "E-SMTH-013-004",           # 三命通会·卷十三 论六亲 (L3568 赋: 刃煞/冲刑损亲)

    # 五行精纪·卷卅一 论寿夭 (L4112-4179)
    "LM_WXJ_SHOU_YAO": "E-WXJ-031-001~006",        # 急脚杀L4139 / 截命杀L4151 / 推命杀L4153 / 三合对冲夭寿L4164 / 鬼门忌支L4125 / 四大空亡L4178
    "LM_LT_ESHA": "E-LT-008-002~008",              # 兰台妙选中篇: 雷公煞L29 / 仇雠金煞L31 / 羊刃重L51 / 夫妻反目父子悖逆L57 / 太阳损明L55 / 寒冰冻结L63 / 飞廉L69
    "LM_WXJ_HUNYU": "E-WXJ-029-001~008",           # 五行精纪卷廿九 论夫妇/论子息: 妨夫妇L3966 / 望乡杀L3968 / 绝房杀L3973 / 时克子L3999-4006 / 狡害杀L4008
    "LM_WXJ_GUIGE": "E-WXJ-022-001~005",           # 五行精纪卷廿二 贵格: 十干大贵人例L2967 / 同旬格L2981 / 金章格L2994 / 世不及贵L2996 / 四镇格L2983
    "LM_LT_GUIGE": "E-LT-001-001~008",             # 兰台妙选上篇 L8 贵格取象: 马化龙驹 / 蛇化青龙 / 宝剑冲牛斗 / 麟逢凤沼 / 龙跃天门 / 月生沧海 / 蚌珠照月 / 金马嘶风
    "LM_WXJ_XIANYUN": "E-WXJ-033-001~004",          # 五行精纪卷卅三 限运八限: 波浪限L4307 / 天罗地网L4325 / 大小耗L4326 / 运到羊刃L4328
    "LM_LT_XIAPIAN": "E-LT-002-001~010",            # 兰台妙选下篇 L76-146 取象贵格: 日轮当表L80 / 官禄会官星L96 / 天泽仲夏L98 / 月华仲秋L100 / 日合辛卯L102 / 龙虎风云L110 / 斗牛月露L112 / 才满三峡L126 / 学富三场L128 / 甲人巳午L144
    "LM_YZHENJING": "E-YZ-001-001~006",             # 玉照定真经 L9: 丙丁亥子 / 己午庚辛 / 甲申乙酉 / 辛卯庚寅 / 水土寅卯 / 酉上逢丁
    "LM_LXZ": "E-LXZ-001-001~004",                  # 李虚中命书: 贵合L51 / 贵食L51 / 纳音水多L63 / 纳音金多L63
    "LM_LLZ": "E-LLZ-001-001~003",                  # 珞琭子赋注: 夹禄L69 / 真武当权L22 / 绝处建贵L16
    "LM_SMTH_RID": "E-SMTH-RID-001~005",            # 三命通会日德L2731(001~002) / 卷三诸神煞: 自缢003·天火004·天刑005

    # 禄命法第十一批: P0 德贵神煞查表切片 (2026-10-20, 五行精纪卷二十 L2007-2092 / 三命通会 L1340-1743)
    "LM_TIAN_DE": "E-WXJ-020-002",                  # 卷二十·天德 L2026 (正丁二坤宫…) L2028 (主登台辅之位)
    "LM_YUE_DE": "E-WXJ-020-003",                   # 卷二十·月德 L2038 (正五九月在丙…) L2040 (主学超升仕官清显)
    "LM_TIAN_SHE_DAY": "E-WXJ-020-004",             # 卷二十·天赦日 L2046 (春戊寅夏甲午秋戊申冬甲子)
    "LM_TAI_JI_GUI": "E-WXJ-020-005",               # 卷二十·太极贵 L2008 (甲乙子午丙丁卯酉戊己四季庚辛寅亥壬巳癸申)
    "LM_WEN_XING": "E-WXJ-020-006",                 # 卷二十·文星贵 L2014 (甲马乙蛇丙戊猴酉抬丁己亥辛求…)
    "LM_TIAN_YIN": "E-WXJ-020-007",                 # 卷二十·天印贵人 L2016 (甲在子寅中乙逢亥亦闻…)
    "LM_JIN_YU": "E-SMTH-010-001",                  # 三命通会卷十·论金舆 L1340 (金舆常居禄前二辰…不富即贵)
    "LM_DE_XIU": "E-SMTH-012-001",                  # 三命通会卷十二·论德秀 L1613 (寅午戌月丙丁为德戊癸为秀…)
    "LM_SAN_QI": "E-SMTH-011-001",                  # 三命通会卷十一·论三奇 L1480 (三奇要顺布…年月日时顺布为吉)
    "LM_ZAI_SHA": "E-SMTH-014-001",                 # 三命通会卷十四·论灾煞 L1727 (常居劫煞之前冲破将星…主血光横死)

             # 渊海子平·六十甲子对照表
}


__all__ = [
    "HEAVENLY_STEMS",
    "EARTHLY_BRANCHES",
    "STEM_ELEMENT",
    "STEM_POLARITY",
    "BRANCH_ELEMENT",
    "BRANCH_HIDDEN_STEMS",
    "SEASON_BY_BRANCH",
    "ZAGI_BRANCHES",
    "GENERATES",
    "CONTROLS",
    # P0-FNDR-05 (R-11 ⑨ 地支关系 audit fix): 关系事实表
    "BRANCH_CLASH",
    "BRANCH_CLASH_PAIRS",
    "BRANCH_HARM",
    "BRANCH_HARM_PAIRS",
    "BRANCH_HE",
    "BRANCH_SANHE",
    "BRANCH_SANHUI",
    "BRANCH_SANXING_TRIPLE",
    "BRANCH_SANXING_DOUBLE",
    "BRANCH_SANXING_SELF",
    # P0-FNDR-06 (R-12 ⑩ 空亡 audit fix): 空亡事实表
    "KONG_WANG_BY_XUN",
    "JIAZI_TABLE",
    "JIAZI_INDEX",
    "XUN_BRANCHES",
    # P0-FNDR-11: Bazi Foundation Contract 补齐事实表
    "BRANCH_POLARITY",
    "STEM_CLASH",
    "BRANCH_PO",
    "BRANCH_PO_PAIRS",
    "TIAN_YI_BY_DAY",
    "WEN_CHANG_BY_DAY",
    "YANG_REN_BY_DAY",
    "JIN_YU_BY_DAY",
    "SHEN_SHA_BY_SANHE",
    "GU_CHEN_GU_SU_BY_YEAR",
    "BRANCH_SANHE_GROUP",
    "TIAN_DE_BY_MONTH",
    "YUE_DE_GAN_BY_SANHE",
    "TIAN_SHE_DAY_BY_SEASON",
    "TAI_JI_GUI_BY_STEM",
    "WEN_XING_BY_STEM",
    "TIAN_YIN_BY_STEM",
    "JIN_YU_BY_STEM",
    "DE_XIU_BY_SANHE",
    "ZAI_SHA_BY_SANHE",
    "SAN_QI_TRIPLES",
    "STEM_NEXT",
    "BRANCH_NEXT3",
    # 八字引擎四柱纳音 (单源 60 甲子表)
    "NAYIN_60",
    # 禄命法基础事实: 十干禄元 + 纳音五行
    "LU_BY_STEM",
    "NAYIN_FIVE_ELEMENT",


    "EVIDENCE_IDS",
]
