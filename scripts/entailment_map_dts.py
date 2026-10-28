# -*- coding: utf-8 -*-
"""DTS 语义蕴含映射表 v1.

纪律:
  · 每条带 pattern -> target(field,value) -> strength -> ref(刘注本 MD 行号) -> quote.
  · 无条文号条目不入库.
  · 仅 MUST 进主命中率; LIKELY 单独桶; COMPATIBLE 只观察不进分母.
  · "身旺/身弱/身强/身轻"综合结论一律不进本表, 只进对照桶.
  · 命例=任铁樵阐微本(旁参); 判据=刘基原注本(准). ref 行号指
    registries/source/raw/DTS_滴天髓_京图撰刘基原注.md.

target 取值:
  ('de_ling', bool) / ('de_di', bool) / ('heavy', bool) /
  ('event', 'root_ba'|'he'|'chong') / ('stem', bool) / ('dang_duo', bool)
need_role=True: 命中句须含日主角色词(日主/日干/日元/身/我), 排除他神主语.
"""

MAP = [
    # ===== 当令 / 失令 (MUST) =====
    dict(name="日主得令",
         pattern=r"(日主|日干|日元|身|我)[^，。；]{0,4}(得令|当令|秉令|得时|当权)",
         target=("de_ling", True), strength="MUST", need_role=True,
         ref="L225", quote="气象得令者吉，喜神得令者吉"),
    dict(name="他神当令->日主失令",
         # X当令/秉令/司令, X 非日主且不生日主 -> de_ling=False (主语在回放时按五行判)
         pattern=r"(?P<x>[木火土金水财官煞杀食伤])[^，。；]{0,2}(当令|秉令|司令|当权|旺提纲)",
         target=("de_ling", False), strength="MUST", need_role=False, subject="x",
         ref="L235", quote="旺则宜泄宜伤，衰则喜帮喜助"),
    dict(name="生于不得令",
         pattern=r"(生于|生)?[^，。；]{0,2}不得令|失令|不逢令",
         target=("de_ling", False), strength="MUST", need_role=False,
         ref="L235", quote="衰则喜帮喜助"),

    # ===== 根 (MUST) =====
    dict(name="日主无根",
         pattern=r"(日主|日干|日元|本身|日元)(真)?无根|身(真)?无根|我身无根",
         target=("de_di", False), strength="MUST", need_role=False,
         ref="L119", quote="不论有根无根，俱要天覆地载"),
    dict(name="不为无根=有根",
         pattern=r"不为无根|非无根|岂无根|何得无根|不为无依",
         target=("de_di", True), strength="MUST", need_role=False,
         ref="L119", quote="不论有根无根，俱要天覆地载"),
    dict(name="日主地支无根",
         pattern=r"地支无根|地支并无根|四柱无根|干支无根|根株全无",
         target=("de_di", False), strength="MUST", need_role=False,
         ref="L119/L420", quote="日主孤立无气，无地人元，绝无一毫生扶之意"),
    dict(name="日坐禄/长生",
         pattern=r"日坐禄|坐下禄支|日坐禄支|日坐长生|坐下长生|日逢时禄|日坐刃|坐下逢禄|日坐禄旺",
         target=("de_di", True), strength="MUST", need_role=False,
         ref="L139/L115", quote="皆长生日主…皆自生日主"),
    dict(name="日主通根/坐禄",
         pattern=r"(日主|日干|日元|身|我)[^，。；]{0,4}(通根|得地|有根|根深|根重|坐禄|得根)",
         target=("de_di", True), strength="MUST", need_role=True,
         ref="L139", quote="如主衰逢冲，则根拔而祸更甚"),
    dict(name="根被冲拔",
         pattern=r"根拔|根已拔|冲去禄|拔根|禄神冲去|冲拔",
         target=("event", "root_ba"), strength="MUST", need_role=False,
         ref="L137/L139/L108",
         quote="地生天者，天衰怕冲…主衰逢冲，则根拔而祸更甚；旺者冲衰衰者拔"),

    # ===== 冲合 (MUST) =====
    dict(name="冲去/冲坏",
         pattern=r"冲去|冲坏|冲拔|冲破|逢冲",
         target=("event", "chong"), strength="MUST", need_role=False,
         ref="L100", quote="支神只以冲为重"),
    dict(name="合去/合住",
         pattern=r"合去|合住|被合|合化",
         target=("event", "he"), strength="MUST", need_role=False,
         ref="L143", quote="天合地者，地旺喜静…财官若旺，则宜静不宜冲"),

    # ===== 透藏 (MUST) =====
    dict(name="透干",
         pattern=r"干透|透干|透出|干头",
         target=("stem", True), strength="MUST", need_role=False,
         ref="L206", quote="月支之神，透于天干也"),
    dict(name="藏支不透",
         pattern=r"藏于支|伏藏|藏支|不透|暗藏",
         target=("stem", False), strength="MUST", need_role=False,
         ref="L206", quote="以散乱之天干，而寻其得所附于提纲，非格也"),

    # ===== 党众 (LIKELY, 单独桶, 不进主分母) =====
    dict(name="党众成群",
         pattern=r"重重|叠叠|成群|成林|党众|林立|众多|太多",
         target=("dang_duo", True), strength="LIKELY", need_role=False,
         ref="L308/L235", quote="强众而敌寡者，势在去其寡；党众为强"),
]

# 对照桶(不进映射): 身旺/身弱/身强/身轻/身衰 —— 仅供交叉验证/象限分析.
CONTROL_BUCKET_PATTERN = r"身旺|身弱|身强|身轻|身衰|日主旺|日主弱"

# 理论/假设/否定/岁运句排除(回放前置, 同探针 v4 口径)
EXCLUDE_SEG = r"则|云|凡|为贵|为贱|所谓|故曰|故云|若|如[^何]|不得令|不逢令|不逢时|大运|流年|岁运|行运|运中|至[^。；]{0,4}运|^运|，运|[子丑寅卯辰巳午未申酉戌亥甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]?运|交[春夏秋金庚丙戊己壬癸子丑寅卯辰巳午未申酉戌亥]|年中|行至|运到|，年|岁中|至[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]"
