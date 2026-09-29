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
    "STEM_NEXT",
    "BRANCH_NEXT3",
    # 八字引擎四柱纳音 (单源 60 甲子表)
    "NAYIN_60",


    "EVIDENCE_IDS",
]
