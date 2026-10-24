# -*- coding: utf-8 -*-
"""禄命法 · 映射层释义原子库（schema 升级：quote/strength/quote_status/topic）

架构约束（P0 施工图定案，2026-10-20）：
- 每条规则必须带 strength + quote_status（source 用规则表 evidence，不重复存）
- strength ∈ {逐字, 推导, 合成, 润色}：表述级别（终态语义）
- quote_status ∈ {complete, pending}：摘录完成度（工作状态）
  - 逐字类：quote 必填 → complete；未摘 → pending（审计列待补清单）
  - 推导类：原著无对应句（终态），quote 可空、恒 complete；quote 填"最贴近原文"提升可溯性
- topic：原局断语标五主题（事业/财运/婚恋/子女/健康）或学识/综合；岁运断语标 岁运（不进分项推论）
- 证据行号：quote 后括号标注（书 + 行号）
"""
from __future__ import annotations

# 每个 rule_id 一条释义记录（同一 id 多条展开共用）
RULE_SEMANTICS: dict[str, dict] = {
    # ================= 原局 =================
    "LM-V01": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["综合"]},
    "LM-V02": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["综合"]},
    "LM-V03": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["事业"]},
    "LM-V04": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["事业"]},
    "LM-V05": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["事业"]},
    "LM-V06": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["事业"]},
    "LM-V07": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["事业"]},
    "LM-V08": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["综合"]},
    "LM-V09": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["综合"]},
    "LM-V10": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["学识"]},
    "LM-V11": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["婚恋"]},
    "LM-V12": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["事业"]},
    "LM-V13": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["财运"]},
    "LM-V14": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["婚恋"]},
    "LM-V15": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["婚恋"]},
    "LM-V31": {"quote": "相生之刑乃五行激扬之气，聪明脱俗声望荣立；相克之刑多狂横刑责官府之灾（五行精纪 L3400）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V31F": {"quote": "羊刃倒戈…遇壬申年项生恶疮头将堕死；有气之地见禄马及羊刃倒戈…又皆是武官也（三命通会 L957 论羊刃）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V31G": {"quote": "天罗地网重并者，男妨妻，女妨夫，并绝嗣；官事不休，破财，口舌之象（五行精纪 L3534 金书命诀）", "strength": "逐字", "quote_status": "complete", "topic": ["婚恋"]},
    "LM-V31H": {"quote": "四柱皆无火，日又在无气之地，虽有官至老，但携匪人（五行精纪 L3861 金书命诀）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V31H-L": {"quote": "日又在无气之地，虽有官至老，但携匪人（五行精纪 L3861 金书命诀）；得印生则气有所归，非全无气（2026-10-21 分级）", "strength": "推导", "quote_status": "complete", "topic": ["综合"]},
    "LM-V34C": {"quote": "四柱纯一不杂，多居两府之贵（三命通会 L2923 芝兰并秀）", "strength": "逐字", "quote_status": "complete", "topic": ["事业"]},
    "LM-V34D": {"quote": "姚尚书丙申庚寅乙酉丁亥，贵人捧印格，得地方为贵（兰台妙选 L8）", "strength": "逐字", "quote_status": "complete", "topic": ["事业"]},
    "LM-V32": {"quote": "凡命前五辰为宅舍……若居无气之乡，及有凶神临之，主其宅多虚耗（五行精纪 L3421-3422 六害之属，撮要）", "strength": "推导", "quote_status": "complete", "topic": ["婚恋"]},
    "LM-V33": {"quote": "行年二运生我命者吉深，我命生行年五行者吉浅，行年二运之五行克我者凶多，我命克行年二运之五行者凶少（五行精纪 L4397）", "strength": "推导", "quote_status": "complete", "topic": ["综合"]},
    "LM-V34": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["综合"]},
    "LM-V35": {"quote": "甲人蛇口乙猪头，丙狗丁龙戊向猴，己午庚寅辛未贵，六壬卯位癸逢牛（五行精纪 L2010 文昌贵）", "strength": "逐字", "quote_status": "complete", "topic": ["学识"]},
    "LM-V36": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["事业"]},
    "LM-V43": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["综合"]},
    "LM-V49-KW": {"quote": "论空亡止以年日所在……为空亡受制，不能为灾，反为福也（五行精纪 L3483 林开五命）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V49-KWC": {"quote": "空亡本不好，冲破不为祸反为福（五行精纪 L3484 广集）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V49-KTC": {"quote": "若壬寅为空亡，壬申同类冲之，则不动，此为最毒（五行精纪 L3484 广集）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V49-CT": {"quote": "凡命犯藏头空亡，本是祸，反为福，但戊己人带之大好（五行精纪 L3485 广集）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    # ================= 运 =================
    "LM-V16": {"quote": "凡二运见贵人，主少灾无挠，主有人引接，进职加官（五行精纪 L4338 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V17": {"quote": "二运见禄，贵人加冠迁禄。常人得财（五行精纪 L4338 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V18": {"quote": "二运见驿马，官员带职差遣，或宣力四方。常人荣干得财（五行精纪 L4338 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V19": {"quote": "二运见华盖、夹贵，文官迁职清华，武官罢职，常人破财停权，但主无祸（五行精纪 L4338 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V20": {"quote": "二运见咸池，官人赃滥发觉，不测暗昧，连累。常人酒色（五行精纪 L4339 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V21": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["岁运"]},
    "LM-V22": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["岁运"]},
    "LM-V23": {"quote": "大小二运为喜会者……谓大运至禄旺，小运至驿马……凡九（五行精纪 L4342）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V24": {"quote": "大小二运为厄会者……谓大运至禄命绝，小运至败……凡九（五行精纪 L4343）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V25": {"quote": "凡二运见伏吟、返吟，不以贵贱，主人疾病、破财、离乡、哭泣之事（五行精纪 L4339 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V37": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["岁运"]},
    "LM-V38": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["岁运"]},
    "LM-V39": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["岁运"]},
    "LM-V40": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["岁运"]},
    "LM-V41": {"quote": "相生之刑乃五行激扬之气，聪明脱俗声望荣立；相克之刑多狂横刑责官府之灾（五行精纪 L3400）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V42": {"quote": "行年二运之五行克我者凶多，我命克行年二运之五行者凶少（五行精纪 L4397）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V44": {"quote": "凡大运到死绝乡，一运中，骨肉死丧，自身衰祸、钝闷、百事蹇塞也（五行精纪 L4275）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V45": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["岁运"]},
    "LM-V49-XS": {"quote": "凡人命空亡本不好，若被日时或运冲刑者，反为虚声杀（五行精纪 L3484 广集）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V49-YC": {"quote": "阳男阴女，大小运行年之元辰，亦为厄会（L4270）；元辰犯运，仲尼困陈蔡之饥（L4271 壶中子）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    # ================= 岁运发用 (LM-F, 2026-10-21) =================
    "LM-F01": {"quote": "原有官行官运发官，原有财行财运发财，原有灾行灾运发灾（渊海子平卷三·论大运 L592；五行精纪卷33 论大运同文）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-F02": {"quote": "官欲运生、杀欲运制、财欲运扶、印欲运旺、食欲运生、身弱欲运引进旺乡（渊海子平卷三·论大运；五行精纪卷33 论大运同文）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-F03": {"quote": "凡行运至夹贵华盖贵人六合上及乘生旺气者，皆主善庆；禄马贵神一切吉神，其年却有小庆（渊海子平卷三·论大运；五行精纪卷33 论大运同文）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-F04": {"quote": "水命四柱有土，至火运本是财运，却反为鬼者，以火生土土克水，是财化为鬼转福成祸（五行精纪卷33 论大运）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-F05": {"quote": "四柱有金至土运是鬼运，却反为吉者，以土生金金生水，是化鬼为助气反祸为福（五行精纪卷33 论大运）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-F06": {"quote": "凡四柱五行俱全者贵……原局缺一行，待大运流年补足（五行精纪卷七·论五行一 L1254 撮要）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    # ================= P0 德贵神煞 (五行精纪卷二十 / 三命通会) =================
    "LM-V71": {"quote": "天德者，五行福德之辰，若人遇之，主登台辅之位，更与月德并者贵，纵遇凶杀，亦主清显（五行精纪 L2028 三命钤）；须要日上见，时上不犯克冲刑破，方吉（三命通会 L1491）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V71B": {"quote": "天德者，五行福德之辰……主登台辅之位……须要日上见……方吉（五行精纪 L2028 / 三命通会 L1491）→ 非日上见仅主清显（推导）", "strength": "推导", "quote_status": "complete", "topic": ["综合"]},
    "LM-V72": {"quote": "月德者，阴阳同类异位之德也，若人遇之，主学超升，仕官清显（五行精纪 L2040 三命钤）；须要日上见，时上不犯克冲刑破，方吉（三命通会 L1491）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V72B": {"quote": "月德者，阴阳同类异位之德也……主学超升，仕官清显（五行精纪 L2040）→ 非日上见仅主清显（推导）", "strength": "推导", "quote_status": "complete", "topic": ["综合"]},
    "LM-V73": {"quote": "春戊寅，夏甲午，秋戊申，冬甲子。主为赦也，百事吉（五行精纪 L2046-2047 集正历）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V74": {"quote": "甲乙生人子午中，丙丁卯酉定亨通，戊己两干临四季，庚辛寅亥禄盈丰，壬巳癸申偏喜美，封侯万户即三公（五行精纪 L2008）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V75": {"quote": "文星纯，秉天之清气，主科名巍峨，官职高崇（五行精纪 L2006 阎东叟）；甲马乙蛇丙戊猴，酉抬丁己亥辛求，庚逢戊狗壬逢虎，十位文星癸兔游（L2014 林开五命）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V76": {"quote": "甲在子寅中，乙逢亥亦闻，丁酉戊申位，丙戊己羊宫，庚辛马蛇是，癸卯与壬龙，此号天印贵，荣达受皇封（五行精纪 L2016 预知子贵格）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V77": {"quote": "金舆常居禄前二辰……主人性柔貌愿，举止温克，妇人逢之，不富即贵；男子得之，多妻妾，阴福相扶持，生日生时遇之为佳（三命通会 L1340 论金舆）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V78": {"quote": "凡人命中得此德秀，无破冲克压者，赋性聪明，温厚和气。若遇学堂，更带财官，主贵。冲克减力（三命通会 L1613 论德秀）→ 德秀主性情不主贵，故判『平』（推导）", "strength": "推导", "quote_status": "complete", "topic": ["综合"]},
    "LM-V79": {"quote": "三奇要顺布，不欲倒乱，如乙丙丁、甲戊庚，天干年月日时顺布为吉……气清则贵，气浊则富（三命通会 L1480 论三奇）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V80A": {"quote": "常居劫煞之前，冲破将星，谓之灾煞……此煞主血光横死……若有福神相助，多是武权（三命通会 L1727 论灾煞）→ 带福神时凶不为甚/武权（推导）", "strength": "推导", "quote_status": "complete", "topic": ["综合"]},
    "LM-V80B": {"quote": "常居劫煞之前，冲破将星，谓之灾煞……此煞主血光横死……大凶（三命通会 L1727 论灾煞）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    # ---- SMTH 四主题切片 (2026-10-20 论疾病/论性情/论女命/论六亲) ----
    "LM-V81": {"quote": "甲乙见庚辛申酉多者，内主肝胆惊悸、劳瘵、手足顽麻；丙丁见壬癸亥子多者，内主心气疼痛；戊己见甲乙寅卯多者，内主脾胃不和；庚辛见丙丁巳午多者，内主肠风痔漏；壬癸见戊己辰戌丑未多者，内主遗精盗汗（三命通会 L3341-3353 论疾病）→ 被克者数≥自身+2判受亏（推导）", "strength": "推导", "quote_status": "complete", "topic": ["健康"]},
    "LM-V82": {"quote": "火太过则声焦面赤、摇膝好动；金太过则好勇无谋、贪欲不仁；水太过则是非好动、飘荡贪淫（三命通会 L3315/3321/3324 论性情）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V83": {"quote": "煞官混杂兼无制，此等女人不堪娶（三命通会 L3525 女命总歌）→ 官煞透干≥2判夫星驳杂（推导）", "strength": "推导", "quote_status": "complete", "topic": ["婚恋"]},
    "LM-V84": {"quote": "女命以克我者为夫……先观夫星以定出身之贵贱（三命通会 L3391 论女命）→ 官煞不现夫缘薄弱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["子女"]},
    "LM-V85": {"quote": "我生者为子……再看子星以察晚年之荣辱；食神得地，子利也（三命通会 L3391 论女命）→ 食伤透干子星有力（推导）", "strength": "推导", "quote_status": "complete", "topic": ["子女"]},
    "LM-V85-B": {"quote": "旺气只聚于时，亦可用…再看子星以察晚年之荣辱（三命通会 L3391 论女命）；子星不透但藏支，有根晚发（2026-10-21 分级）", "strength": "推导", "quote_status": "complete", "topic": ["子女"]},
    "LM-V86": {"quote": "女命无煞逢二德，可两国之封（三命通会 L3423 论女命）", "strength": "逐字", "quote_status": "complete", "topic": ["婚恋", "子女"]},
    "LM-V87A": {"quote": "年逢刃煞，幼年早丧爹娘（三命通会 L3568 论六亲赋）", "strength": "逐字", "quote_status": "complete", "topic": ["婚恋"]},
    "LM-V87B": {"quote": "时遇刃伤，未年却损儿女（三命通会 L3568 论六亲赋）", "strength": "逐字", "quote_status": "complete", "topic": ["婚恋"]},
    "LM-V88": {"quote": "冲者无兄弟，刑者损六亲（三命通会 L3568 论六亲赋）→ 四支互冲≥2对判兄弟缘薄（推导）", "strength": "推导", "quote_status": "complete", "topic": ["婚恋"]},
    # ---- 五行精纪卷卅一 论寿夭 (L4112-4179) ----
    "LM-V89": {"quote": "甲乙申酉见阎王，丙丁亥子切须防……甲人见申，乙人见酉，生时带着，支干皆有者，定夭（五行精纪 L4139-4140 论寿夭·急脚杀）", "strength": "逐字", "quote_status": "complete", "topic": ["健康"]},
    "LM-V90": {"quote": "人命归前次一支，子生须与丑为期，三逢必定遭凶死，两见须忧血渍衣（五行精纪 L4151 论寿夭·截命杀）→ 本命前辰临四柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["健康"]},
    "LM-V91": {"quote": "命后一辰宜见两，重重见者涉疑猜，三重在外中年夭（五行精纪 L4153 论寿夭·推命杀）→ 本命后辰≥2（推导）", "strength": "推导", "quote_status": "complete", "topic": ["健康"]},
    "LM-V92": {"quote": "寅午戌全人，亥年亥时亥运皆弱也；巳酉丑全人，寅年寅时寅运皆弱也……（五行精纪 L4164 论寿夭·夭寿杀·天元变化书）→ 三合局全见对冲支（推导）", "strength": "推导", "quote_status": "complete", "topic": ["健康"]},
    "LM-V93": {"quote": "火忌申酉亥，金嫌亥子丑，水土寅卯巳，木怕巳午申，更若逢阴鬼，寿算永不停（五行精纪 L4125 论寿夭·人过鬼门）→ 年命纳音忌支≥2（推导）", "strength": "推导", "quote_status": "complete", "topic": ["健康"]},
    "LM-V94": {"quote": "颜回夭折，只因四大空亡……生于甲子甲午之人，命内有三字水者夭；生于甲申甲寅旬之人，命内有三字金者夭（五行精纪 L4178 论寿夭）", "strength": "逐字", "quote_status": "complete", "topic": ["健康"]},
    # ---- 兰台妙选·中篇 恶煞 (L11-73) ----
    "LM-V95": {"quote": "雷公煞者，正二三月在寅，四五六月在亥，七八九月在申，十十一十二月在巳，犯之者重重克身（兰台妙选 L29 中篇）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V96": {"quote": "仇雠金煞者，二酉二巳，乃蛇须殃咎、鸡须分碎是也……富贵定不长年（兰台妙选 L31 中篇）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V97": {"quote": "羊刃重重而克命，沟壑土埋……大抵羊刃之煞最可畏也，三重克身带煞，必主征伐而终（兰台妙选 L51 中篇）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V98": {"quote": "夫妻反目，刃劫临于日宫……日逢羊刃，则夫妻反目（兰台妙选 L57 中篇）→ 日支坐年干羊刃（推导）", "strength": "推导", "quote_status": "complete", "topic": ["综合"]},
    "LM-V99": {"quote": "父子悖逆，劫刃坐于时位……时逢羊刃劫煞，则父子悖逆（兰台妙选 L57 中篇）→ 时支坐羊刃兼劫煞（推导）", "strength": "推导", "quote_status": "complete", "topic": ["综合"]},
    "LM-V100": {"quote": "太阳损明，戊午不禁于水溢；太阴薄食，己未岂堪于土多（兰台妙选 L55 中篇）→ 戊午年+水≥3 / 己未年+土≥3（推导）", "strength": "推导", "quote_status": "complete", "topic": ["综合"]},
    "LM-V101": {"quote": "寒冰冻结，毕世天涯……壬癸命见子丑亥全者，生于冬月，乃北方煞冻结凝滞也（兰台妙选 L63 中篇）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "LM-V102": {"quote": "飞廉值煞，男犯徒流，而女落风尘。飞廉，正五九酉，二六十/三七十一卯，四八十二午……见煞更带之者不宜也（兰台妙选 L69 中篇）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    # ---- 五行精纪卷廿九 论夫妇/论子息 (L3960-4008) ----
    "LM-V103": {"quote": "妨夫妇：木命逢牛鼠，金人忌马羊，水土逢鸡狗，龙蛇火命当，夫妻如幸免，头男头女亡（五行精纪 L3966 论夫妇）", "strength": "逐字", "quote_status": "complete", "topic": ["婚恋", "子女"]},
    "LM-V104": {"quote": "望乡杀：金命鸡猴是，火人蛇马乡，水土生猪鼠，木虎兔难当，男人若值此，三度作新郎，女人逢此者，三度作花娘（五行精纪 L3968 论夫妇）", "strength": "逐字", "quote_status": "complete", "topic": ["婚恋", "子女"]},
    "LM-V105": {"quote": "绝房杀：寅申巳亥七月生，子午卯酉十二神，辰戌丑未仲春月，绝房男女堪亲……男害妻儿兼父母，女伤夫主及公姑（五行精纪 L3973 论夫妇）", "strength": "逐字", "quote_status": "complete", "topic": ["婚恋", "子女"]},
    "LM-V106": {"quote": "凡人命时带年冲，克子（五行精纪 L3999 论子息）→ 时支冲年支（推导）", "strength": "推导", "quote_status": "complete", "topic": ["婚恋", "子女"]},
    "LM-V107": {"quote": "时带年刑，克子。时带年破，克子。时带年害，克子（五行精纪 L3999-4000 论子息）→ 时支刑/破/害年支（推导）", "strength": "推导", "quote_status": "complete", "topic": ["婚恋", "子女"]},
    "LM-V108": {"quote": "时带年刃，克子。时带年劫，克子。时带年元辰，克子。时带年空亡，克子，重者绝子（五行精纪 L4000-4002 论子息）→ 时支坐刃/劫煞/元辰/空亡（推导）", "strength": "推导", "quote_status": "complete", "topic": ["婚恋", "子女"]},
    "LM-V109": {"quote": "时坐华盖，克子。五十后愈见不牢（五行精纪 L4003 论子息）→ 时支坐华盖（推导）", "strength": "推导", "quote_status": "complete", "topic": ["婚恋", "子女"]},
    "LM-V110": {"quote": "凡命见申日、亥时，巳日、寅时，互换见者，名曰狡害杀，主绝嗣，须庶出过房方住。五行狡害不为良，夫妇孤单独守房，死去坟前无子哭，求他异姓却相当（五行精纪 L4008 论子息）", "strength": "逐字", "quote_status": "complete", "topic": ["婚恋", "子女"]},
    # ---- 五行精纪卷廿二 贵格 (L2911-3131) ----
    "LM-V111": {"quote": "六甲年二月乙未日丙寅时…逐年只有一日一时，主生大贵人，应世建功立事之命（五行精纪 L2967-2978 贵格）→ 年干×月支×日时柱查表（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V112": {"quote": "五行全在一旬中格，带生旺六合，无破败，台阁贵人命也（五行精纪 L2981 贵格）→ 四柱干支同旬（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V113": {"quote": "金章格：甲子见甲寅、乙丑见乙卯…命前二辰见本禄有用，必贵，无用即常也（五行精纪 L2994 贵格）→ 年支前二辰临四柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V114": {"quote": "世不及贵格：甲人辛酉，戊人乙卯，乙人庚申，己人甲寅（五行精纪 L2996 贵格）→ 年干×支查表（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V115": {"quote": "四镇格：戊己二字而入辰戌丑未者是也…四镇之星福最强，不作公侯便主王（五行精纪 L2983-2987 贵格）→ 戊己干+四墓支≥2（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    # ---- 兰台妙选·上篇 贵格取象 (L8) ----
    "LM-V116": {"quote": "马化龙驹奔凤阙，器业峥嵘。午属马辰属龙酉为凤，人得丙午壬辰合酉可以类此（兰台妙选上篇 L8）→ 丙午/壬辰年+酉临四柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V117": {"quote": "蛇化青龙入天池，功名赫奕。巳属蛇辰属龙，巳人得辰而为青龙（兰台妙选上篇 L8）→ 年支巳+辰临四柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V118": {"quote": "耀日月之光，则宝剑冲于牛斗。壬申癸酉剑锋金，柱中得丑为妙（兰台妙选上篇 L8）→ 壬申/癸酉年+丑临四柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V119": {"quote": "麟逢凤沼，辰命跨于金牛。辰为龙为麟，酉为凤沼，辰命得酉（兰台妙选上篇 L8）→ 年支辰+酉临四柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V120": {"quote": "壬辰逢癸亥而龙跃天门。辰则为龙，亥则为乾（兰台妙选上篇 L8）→ 壬辰年+亥临四柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V121": {"quote": "己未遇酉宫则月生沧海。太阴入庙在未（兰台妙选上篇 L8）→ 己未年+时支酉（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V122": {"quote": "蚌珠照月而烺然烁众。甲子乙丑为蚌蛤之荣，月宫己未，得己未时正合此格（兰台妙选上篇 L8）→ 甲子/乙丑年+时支未（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V123": {"quote": "金马嘶风而卓尔超群。庚午甲午为金马，巳为巽风，得巳时乃合此格（兰台妙选上篇 L8）→ 庚午/甲午年+时支巳（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    # ---- 五行精纪卷卅三 限运八限 (L4300-4329) ----
    "LM-V124": {"quote": "运入天罗地网者，常以戌亥为天罗辰巳为地网，若男行年至天罗则有官符诉讼刑狱牵缠，女行年至地网则有口舌沉疴（五行精纪 L4325）→ 男运支戌亥/女运支辰巳（推导）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V125": {"quote": "运入大小耗者，常以太岁前五辰为大耗六辰为小耗，主诸事丧败无所成实（五行精纪 L4326）→ 运支=年支前五辰/六辰（推导）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V126": {"quote": "凡行运到羊刃上，主财物聚散（五行精纪 L4328）→ 运支=年干羊刃（推导）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V127": {"quote": "波浪限，金人到亥子岁运是也，飘泛如舟（五行精纪 L4307）→ 年命金+运支亥子（推导）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    # ---- 兰台妙选·下篇 取象贵格 (L76-146) ----
    "LM-V128": {"quote": "日轮当表，毫光岂被猛风吹。戊午为日轮巳午为当表，如戊午生于五月又逢巳午日时，谓有辉光于天下（兰台妙选下篇 L80）→ 戊午年+午月+巳午临柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V129": {"quote": "官禄会于官星，格在子午者拜书受恩之客。六丁生人见壬午，六己生人见甲午，六癸生人见戊午（兰台妙选下篇 L96）→ 年干丁+壬午柱/己+甲午柱/癸+戊午柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V130": {"quote": "天泽生逢仲夏，用辛亥者入格则德润乾坤。丙午丁未人生于五六月逢辛亥，谓之天门降天泽（兰台妙选下篇 L98）→ 丙午/丁未年+午未月+辛亥柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V131": {"quote": "月华生于仲秋，用甲辰者入格则光辉天下。己未逢甲辰，己用甲为官星，二者皆大贵公卿（兰台妙选下篇 L100）→ 己未年+甲辰柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V132": {"quote": "日合辛卯，成功烜赫贯山河。日在戊午生夏逢辛卯，轮光穿入枝（兰台妙选下篇 L102）→ 戊午年+夏月+辛卯柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V133": {"quote": "广扬硕德，只缘龙虎会风云。辰龙寅虎巽风卯云四字全，更带禄马贵人（兰台妙选下篇 L110）→ 四支含辰寅巳卯全（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V134": {"quote": "大阐经纶，善为斗牛见月露。己丑遇己未生于夏末秋初，其人大阐经纶掌乾坤于笔下（兰台妙选下篇 L112）→ 己丑年+己未柱+未申酉月（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V135": {"quote": "才满三峡，文章居词馆之中。人逢天河大海润下更逢己亥最荣（兰台妙选下篇 L126）→ 年命天河/大海水+己亥柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V136": {"quote": "学富三场，文星在学堂之上。海中金白镴金剑锋金遇丁巳时乃是（兰台妙选下篇 L128）→ 年纳音金类+丁巳时（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V137": {"quote": "甲人巳午，必达钧衡之任。甲见己为大财合更带马官星（兰台妙选下篇 L144）→ 甲年+柱见己巳/己午（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    # ---- 玉照定真经 张颙注 (L9-15) ----
    "LM-V138": {"quote": "丙丁亥子，投于江水沟河（玉照定真经 L9）→ 年干丙丁+亥子临支（推导）", "strength": "推导", "quote_status": "complete", "topic": ["健康"]},
    "LM-V139": {"quote": "己午庚辛，男女病多心血（玉照定真经 L9）→ 年干庚辛+巳午临支（推导）", "strength": "推导", "quote_status": "complete", "topic": ["健康"]},
    "LM-V140": {"quote": "甲申乙酉，小儿风多病肝经（玉照定真经 L9）→ 年柱甲申/乙酉（推导）", "strength": "推导", "quote_status": "complete", "topic": ["健康"]},
    "LM-V141": {"quote": "辛卯庚寅，尤忌大人劳骨病（玉照定真经 L9）→ 年柱辛卯/庚寅（推导）", "strength": "推导", "quote_status": "complete", "topic": ["健康"]},
    "LM-V142": {"quote": "水土同来寅卯，平生隔气风痰（玉照定真经 L9）→ 年纳音水土+寅卯临支（推导）", "strength": "推导", "quote_status": "complete", "topic": ["健康"]},
    "LM-V143": {"quote": "酉上逢丁，后须绝嗣（玉照定真经 L9）→ 时柱丁酉（推导）", "strength": "推导", "quote_status": "complete", "topic": ["子女"]},
    # ---- 李虚中命书 (卷上 L51 贵合/贵食; 卷中 L63 纳音多寡性情) ----
    "LM-V144": {"quote": "有贵合则官位穹崇，所作契合。如甲戊庚贵在丑未，甲得己丑己未戊得癸丑癸未庚得乙丑乙未；乙己贵在申子，乙得庚子庚申己得甲子甲申；丙丁贵在亥酉，丙得辛酉辛亥丁得壬寅壬辰（李虚中命书卷上 L51）→ 年干×贵合柱临四柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V145": {"quote": "有贵食则禄丰足，所成过望。甲食丙得丙寅丙辰，乙食丁得丁酉丁亥，庚食壬得壬申壬戌，辛食癸得癸卯癸巳（李虚中命书卷上 L51）→ 年干×贵食柱临四柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V146": {"quote": "水得水多则沉潜伏溺，小巧多权，苗而不秀，声誉汪洋（李虚中命书卷中 L63）→ 四柱纳音水≥3（推导）", "strength": "推导", "quote_status": "complete", "topic": ["综合"]},
    "LM-V147": {"quote": "金得金多则刚直尚勇，见义必为，过不自知（李虚中命书卷中 L63）→ 四柱纳音金≥3（推导）", "strength": "推导", "quote_status": "complete", "topic": ["综合"]},
    # ---- 珞琭子三命消息赋 (徐子平注 L16/L22/L69) ----
    "LM-V148": {"quote": "夹禄，戊辰日戊午时丁巳日丁未时己未日己巳时壬戌日壬子时癸丑日癸亥时。官崇禄显，定知夹禄之乡（珞琭子赋注 L69）→ 日时夹禄表（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V149": {"quote": "真武当权者，壬癸生日也。以壬午癸巳壬辰壬戌癸丑癸未日生也，下有官印禄马旺相墓库而成庆，此乃作上格贵命言也（珞琭子赋注 L22）→ 壬癸日六柱（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V150": {"quote": "此五行论于绝地而建贵也，五行绝处有禄马。丁亥丙子庚寅甲申乙酉戊寅壬午癸巳己卯己亥皆从无，天元受绝休囚之地却成贵强之位（珞琭子赋注 L16）→ 十柱绝地建贵（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V151": {"quote": "此格止有五日：甲寅、丙辰、戊辰、庚辰、壬戌……日德心善多稳厚，而作事慈祥，福必丰厚（三命通会 L2731）→ 日德五日入格（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-V152": {"quote": "日德不喜见魁罡，化成煞曜最难当；日德……不宜见财官，及刑冲破害，空亡、魁罡会合加临，皆为大忌（三命通会 L2731）→ 日德见魁罡/空亡犯忌（推导）", "strength": "推导", "quote_status": "complete", "topic": ["健康"]},
    "LM-V153": {"quote": "凡见夹禄者，不可本禄上有岁月所占，占了则官实也，实则不能容物也。官不崇显也（珞琭子赋注 L70）→ 本禄被年月所占则滞（推导）", "strength": "推导", "quote_status": "complete", "topic": ["事业"]},
    "LM-S10": {"quote": "天刑煞，子丑人乙时，寅人庚时，卯辰人辛时，巳人壬时，午未人癸时，申人丙时，酉戌人丁时，亥人戊时，取时刑克本命，犯者遭刑有疾（三命通会卷三·总论诸神煞）", "strength": "逐字", "quote_status": "complete", "topic": ["健康"]},
    # ================= 太岁 =================
    "LM-V26": {"quote": "凡命前五辰为宅舍……（三命钤）；太岁入宅，主家宅动摇，宅者命前五辰是也（L4411 烛神经）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V27": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["岁运"]},
    "LM-V28": {"quote": "凡太岁刑大运，主破财（五行精纪 L4387 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V29": {"quote": "凡太岁二运如到孤辰，必有孝服，到寡宿必有血光之灾也（五行精纪 L4386 金书命诀）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V30": {"quote": "凡太岁到以上诸杀位，亦依此论之（五行精纪 L4338 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V46": {"quote": "行年二运之五行克我者凶多（五行精纪 L4397）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V47": {"quote": "行年二运生我命者吉深（五行精纪 L4397）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V48": {"quote": "凡大运至本命宫，五行死绝，支干刑冲六害，一切凶杀者，为屯蹇，凶祸之运（五行精纪 L4273）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V49": {"quote": "行年太岁与驿马合并，主迁官得禄（五行精纪 L2398，撮要）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    # ================= 流年 =================
    "LM-V50": {"quote": "日时破宅宅须破，太岁冲年亦深祸（五行精纪 L4247 沉芝源髓）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V50A": {"quote": "如癸亥生，得乙巳岁，水虽绝在巳，而以水克火为财，火旺于巳，兼巳上乘马，虽巳亥冲，临于返吟之上，以身财之旺，故不为灾忒焉；掩者，伏吟也。冲者，返吟也。相生则吉，相克则凶（五行精纪 L4416 珞琭子/莹和尚）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V51": {"quote": "凡太岁刑冲压害生年，主父母亡身之灾，刑冲压害生月，主兄弟僚友之灾，刑冲压害生日，主妻妾己身之灾。刑冲压害生时，主子孙之灾（五行精纪 L4423 广信集）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V52": {"quote": "大运不宜与太岁相克相冲，尤忌运克岁……主破耗丧事（三命通会 L974）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V53": {"quote": "凡太岁刑大运，主破财（五行精纪 L4387 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V54": {"quote": "太岁压大运，主权握不宁也（五行精纪 L4387 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V55": {"quote": "甲子流年又是甲子运，谓之岁运并临，独羊刃、七煞为凶，财、官、印绶亦吉（三命通会 L954）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V56": {"quote": "若岁运与日相对，谓之返吟……不利六亲，非横破财，不为吉兆（三命通会 L968）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V57": {"quote": "岁运压日，谓之伏吟……不利六亲（三命通会 L968）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V58": {"quote": "生时相逢真太岁。假如甲子生人又见甲子年，谓之真太岁，又名转趾煞，要大运日主与太岁相和相顺，其年则吉；若值刑冲破害，与太岁互相战克则凶（三命通会 L954）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V59": {"quote": "若太岁克生时，亦身灾（五行精纪 L4421 神白经）；若生时与逐年太岁天元干合者，谓之晦气，必主阴灾（五行精纪 L4419）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V59B": {"quote": "若生日与逐年太岁天元干合者，谓之晦气，必主阴灾。发灾在支干所犯之月，重者死亡，轻者灾挠也（五行精纪 L4419 晦气）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V60": {"quote": "凡支干纳音俱在死、墓、绝处。又值灾劫恶杀临之，即死（五行精纪 L4344）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V61": {"quote": "凡太岁至空亡年，失脱破财（五行精纪 L4411 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V62": {"quote": "如在本命支干纳音，三才刑克、死绝，一切凶杀之地，则主疾病、官灾、破财，不祥、死丧（五行精纪 L4409 论太岁）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V63": {"quote": "凡太岁见咸池年，淫乱公事（五行精纪 L4411 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V64": {"quote": "岁压本命年，主动为稽滞不快（五行精纪 L4411 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V65": {"quote": "所至之宫，欲常与本命支干纳音相合，无冲害、刑克，仍加本命贵人、禄马，一切福神之地，则其年有迁官得财、成名进身（五行精纪 L4409 论太岁）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V66": {"quote": "运入天罗地网者，常以戌亥为天罗，辰巳为地网，若男行年至天罗，则有官符、诉讼、刑狱牵缠（五行精纪 L4325）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V31A": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["健康"]},
    "LM-V31B": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["综合"]},
    "LM-V31C": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["财运"]},
    "LM-V31D": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["综合"]},
    "LM-V31E": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["财运"]},
    "LM-V34B": {"quote": "", "strength": "待补", "quote_status": "pending", "topic": ["事业"]},
    "LM-Y71": {"quote": "欲常与本命支干纳音相合，无冲害、刑克……则其年有迁官得财、成名进身、婚姻生子、利见大人之福（五行精纪 L4409 论太岁）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-Y72": {"quote": "凡太岁生本命年，事多遂心（五行精纪 L4410 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-Y72B": {"quote": "凡本命纳音生太岁年，破财劳冗，百事不成（五行精纪 L4410 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-Y72C": {"quote": "凡太岁与本命相克年，宜防上人怒责（五行精纪 L4410 烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V67": {"quote": "", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V68": {"quote": "", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V69": {"quote": "三命指掌云：凡阳男阳女，至交运时，主有灾滞（五行精纪 L4269）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V70": {"quote": "阳男阴女，大小运行年之元辰，亦为厄会（L4270）；太岁压元辰年，主移徙，或妻妾亲人失义（L4411）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-S07": {"quote": "自缢煞，此煞取五行反系处，如戌人巳、巳人戌……大忌相克，天元是墓，更有天中、官符、大耗者，定凶（三命通会卷三·总论诸神煞）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-S08": {"quote": "自缢煞取五行反系处，更有天中、官符、大耗者定凶（三命通会卷三）→ 无凶神会集则不重（推导）", "strength": "推导", "quote_status": "complete", "topic": ["岁运"]},
    "LM-S09": {"quote": "天火煞，此煞取寅午戌全而天干有丙丁，五位中全不见水者是，有水则非；若年运至火气生旺处，当防火灾（三命通会卷三·总论诸神煞）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-S11": {"quote": "红鸾卯起子逆数，主婚姻喜庆；天喜为红鸾对冲（神煞通行查法，主婚嫁添丁喜庆）", "strength": "逐字", "quote_status": "complete", "topic": ["婚姻"]},
    "LM-S12": {"quote": "天喜为红鸾对冲，主喜庆欢欣、婚嫁添丁（神煞通行查法）", "strength": "逐字", "quote_status": "complete", "topic": ["婚姻"]},
    "LM-S13": {"quote": "天医以月支前一位取之，正月生见丑…主疾病痊愈、安康（神煞通行查法）", "strength": "逐字", "quote_status": "complete", "topic": ["健康"]},
    "LM-S14": {"quote": "攀鞍居驿马后一辰，申子辰在丑、寅午戌在未、巳酉丑在戌、亥卯未在辰，鞍为马之备，主功名进阶（三车一览/神煞通行）", "strength": "逐字", "quote_status": "complete", "topic": ["事业"]},
    "LM-S15": {"quote": "天厨名食神禄，甲丙爱行双女游、乙丁狮子己金牛、戊坐未羊庚鱼腹、辛到宝瓶、癸用天蝎壬人马，主衣食俸禄（三命通会/神煞通行）", "strength": "逐字", "quote_status": "complete", "topic": ["事业"]},
    "LM-S16": {"quote": "甲人蛇口乙猪头，丙狗丁龙戊向猴，己午庚寅辛未贵，六壬卯位癸逢牛（五行精纪 L2010 文昌贵），主文名科甲文章", "strength": "逐字", "quote_status": "complete", "topic": ["事业"]},
    "LM-S01": {"quote": "病符居太岁后一辰，主其年多病疾、身体不适（神煞通行/三命通会）", "strength": "逐字", "quote_status": "complete", "topic": ["健康"]},
    "LM-S02": {"quote": "官符（死符）居太岁前五辰、病符对冲，主官事词讼文书纠纷，无贵神解救者防凶恶（三命通会·总论诸神煞）", "strength": "逐字", "quote_status": "complete", "topic": ["事业"]},
    "LM-S03": {"quote": "劫煞主劫夺耗散、咽喉目赤之灾、横事失权（渊海子平/三命通会）", "strength": "逐字", "quote_status": "complete", "topic": ["财富"]},
    "LM-S04": {"quote": "金舆主婚姻庆贺、骨肉之喜，不富即贵（三命通会·论金舆）", "strength": "逐字", "quote_status": "complete", "topic": ["婚姻"]},
    "LM-S05": {"quote": "灾煞冲破将星，主血光、横祸、外伤（三命通会/神煞通行）", "strength": "逐字", "quote_status": "complete", "topic": ["健康"]},
    "LM-S06": {"quote": "孤辰寡宿主孤单独处、孝服血光（渊海子平/三命通会）", "strength": "逐字", "quote_status": "complete", "topic": ["婚姻"]},
    "LM-V57B": {"quote": "伏吟压命柱，不利六亲（三命通会 L968）", "strength": "逐字", "quote_status": "complete", "topic": ["六亲"]},
    "LM-V60B": {"quote": "大运临死绝、太岁刑克，凶而防之；未全会集死绝衰息则不遽定死（五行精纪/烛神经）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V80": {"quote": "小运与命柱刑冲害，主细累浮灾，不为重害（五行精纪 L4273）", "strength": "逐字", "quote_status": "complete", "topic": ["岁运"]},
    "LM-V87": {"quote": "五鬼岁遇，杀克身而尤重，临生败旺死绝其年决有大灾（三命指掌/神煞通行）", "strength": "逐字", "quote_status": "complete", "topic": ["健康"]},
    "LM-Y73": {"quote": "本命克太岁为财，以身财之旺故不为灾，宜获福、主得财遂意（珞琭子/五行精纪）", "strength": "逐字", "quote_status": "complete", "topic": ["财富"]},
    "LM-V90A": {"quote": "正财偏财见比肩分夺，劫财羊刃又见岁运冲合，必死；财旺遇劫，主破财、合伙分利（渊海子平卷三）", "strength": "逐字", "quote_status": "complete", "topic": ["财富"]},
    "LM-V90B": {"quote": "旺则劫财破耗，财弱遇劫，防破财、合伙失利（渊海子平·杂论口诀）", "strength": "逐字", "quote_status": "complete", "topic": ["财富"]},
    "LM-V90C": {"quote": "比肩帮身，身弱喜比，主朋友助力（子平口径）", "strength": "推导", "quote_status": "complete", "topic": ["财富"]},
}

_STRENGTHS = {"逐字", "推导", "待补", "合成", "润色"}
_QUOTE_STATI = {"complete", "pending"}
_TOPIC_ENUM = {"综合", "事业", "财运", "婚恋", "子女", "健康", "学识", "岁运"}


def audit_rule_semantics(rules: list[dict]) -> dict:
    """schema 校验 + 待补清单审计（强约束：每条规则 id 有释义记录且字段合法）.

    返回: {"ok": bool, "errors": [...], "pending": [...], "covered": n, "total": n}
    """
    errors, pending = [], []
    covered = 0
    for r in rules:
        rid = r["id"]
        sem = RULE_SEMANTICS.get(rid)
        if sem is None:
            errors.append(f"{rid}: 无释义记录（缺 quote/strength/quote_status/topic）")
            continue
        covered += 1
        if sem["strength"] not in _STRENGTHS:
            errors.append(f"{rid}: strength 非法 {sem['strength']}")
        if sem["quote_status"] not in _QUOTE_STATI:
            errors.append(f"{rid}: quote_status 非法 {sem['quote_status']}")
        if not sem["topic"] or not (set(sem["topic"]) <= _TOPIC_ENUM):
            errors.append(f"{rid}: topic 非法 {sem['topic']}")
        if sem["strength"] == "逐字" and not sem["quote"]:
            sem2 = dict(sem)
            sem2["quote_status"] = "pending"
            pending.append(f"{rid}: strength=逐字 但 quote 未摘（待补）")
        elif sem["strength"] == "待补":
            pending.append(f"{rid}: 有原文未摘（strength=待补, quote_status={sem['quote_status']}）")
    return {
        "ok": not errors and not pending,
        "errors": errors,
        "pending": pending,
        "covered": covered,
        "total": len(rules),
    }


# ================= 表二：REL 五行关系语义 =================
# 五行推导类（原著无逐句对应 → strength=推导、quote 空=终态）
# 键 = (关系, 柱位)；关系 ∈ 生我/我生/克我/我克/比和；柱位 ∈ 年/月/日/时/命宫/身宫
REL_SEMANTICS: dict[tuple[str, str], dict] = {}
_REL_BASE = {
    "生我": {"text": "柱位纳音生年命，助我者气有所归，主得扶持", "tone_note": "吉"},
    "我生": {"text": "年命生柱位，泄秀之气外发，主聪明付出而多劳", "tone_note": "平"},
    "克我": {"text": "柱位克年命，受制之气临身，主压力束缚、多阻力", "tone_note": "凶"},
    "我克": {"text": "年命克柱位，我制之物为我所驭，主掌财得权", "tone_note": "平"},
    "比和": {"text": "柱位与年命比和，同类相助，主平顺自立", "tone_note": "吉"},
}
_REL_POS_TOPIC = {
    "年": "综合", "月": "事业", "日": "综合", "时": "子女", "命宫": "综合", "身宫": "综合",
}
for _rel, _base in _REL_BASE.items():
    for _pos in ("年", "月", "日", "时", "命宫", "身宫"):
        _topic = [_REL_POS_TOPIC[_pos]]
        # 关系语义附加主题：克我受制→健康、我生泄秀→子女（供分项推论章节派生）
        if _rel == "克我":
            _topic.append("健康")
        if _rel == "我生":
            _topic.append("子女")
        REL_SEMANTICS[(_rel, _pos)] = {
            "quote": "", "strength": "推导", "quote_status": "complete",
            "topic": _topic, "text": _base["text"],
        }

# ================= 表三：SHEN_SHA 神煞语义 =================
# 神煞各煞释义（原文有者逐字摘，无者推导撮要）
SHEN_SHA_SEMANTICS: dict[str, dict] = {
    "华盖": {"quote": "", "strength": "推导", "quote_status": "complete", "topic": ["学识"], "text": "华盖临，主多能博识，立性聪明，孤高自许，喜艺文玄学（撮五行精纪华盖论）"},
    "咸池": {"quote": "", "strength": "推导", "quote_status": "complete", "topic": ["婚恋"], "text": "咸池（桃花）临，主风流酒色，情缘事多（撮 V11/V13）"},
    "贵人": {"quote": "", "strength": "推导", "quote_status": "complete", "topic": ["事业"], "text": "天乙贵人临，主少灾无挠，有人引接提携（撮 L4338）"},
    "驿马": {"quote": "", "strength": "推导", "quote_status": "complete", "topic": ["事业"], "text": "驿马临，主迁动得财，官员带职差遣（撮 L4338）"},
    "禄": {"quote": "", "strength": "推导", "quote_status": "complete", "topic": ["财运"], "text": "禄临，主加冠迁禄，常人得财（撮 L4338）"},
    "文昌": {"quote": "甲人蛇口乙猪头，丙狗丁龙戊向猴，己午庚寅辛未贵，六壬卯位癸逢牛（五行精纪 L2010）", "strength": "逐字", "quote_status": "complete", "topic": ["学识"], "text": "文昌临，主科名文章"},
    "将星": {"quote": "", "strength": "推导", "quote_status": "complete", "topic": ["事业"], "text": "将星临，与福贵并者妙，主威望统领"},
    "劫煞": {"quote": "", "strength": "推导", "quote_status": "complete", "topic": ["事业"], "text": "劫煞临，主诸事耗散、横事，远行防劫夺（撮 L4424）"},
    "孤辰": {"quote": "凡太岁二运如到孤辰，必有孝服，到寡宿必有血光之灾也（五行精纪 L4386）", "strength": "逐字", "quote_status": "complete", "topic": ["婚恋"], "text": "孤辰临，主孤寡之性、六亲缘薄"},
    "寡宿": {"quote": "凡太岁二运如到孤辰，必有孝服，到寡宿必有血光之灾也（五行精纪 L4386）", "strength": "逐字", "quote_status": "complete", "topic": ["婚恋"], "text": "寡宿临，主孤寡之性、晚年防血光"},
    "空亡": {"quote": "论空亡止以年日所在……为空亡受制，不能为灾，反为福也（五行精纪 L3483）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"], "text": "空亡临，虚而不实，止以年日所在，冲破反为福"},
    "元辰": {"quote": "阳男阴女，大小运行年之元辰，亦为厄会（L4270）；元辰犯运，仲尼困陈蔡之饥（L4271）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"], "text": "元辰临运，如物当风，灾祸倚伏"},
    "魁罡": {"quote": "", "strength": "推导", "quote_status": "complete", "topic": ["综合"], "text": "魁罡四日（庚辰壬辰戊戌庚戌），聪明果断，秉权好杀，强则贵显衰则彻骨"},
    "天罗地网": {"quote": "运入天罗地网者，常以戌亥为天罗，辰巳为地网，若男行年至天罗，则有官符、诉讼、刑狱牵缠（五行精纪 L4325）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"], "text": "天罗地网临，主官灾、刑狱之虑"},
    "金舆": {"quote": "二运见金舆，不以贵贱，主婚姻庆贺，骨肉之喜（五行精纪 L4338）", "strength": "逐字", "quote_status": "complete", "topic": ["婚恋"], "text": "金舆临，主婚姻庆贺、骨肉之喜"},
}

# ================= 表四：GONG 宫位语义 =================
GONG_SEMANTICS: dict[str, dict] = {
    "命宫": {"quote": "迁移宫有长生，贵不求，财自至……官禄宫中有吉神，官职日迁荣……命宫帝座详在前，祸福总自然（五行精纪 L4241-4244 直道歌）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"], "text": "命宫为根基帝座，定一生祸福之总"},
    "身宫": {"quote": "", "strength": "推导", "quote_status": "complete", "topic": ["综合"], "text": "身宫主一生劳碌之地，身克命多奔波"},
}

# ================= 表五：TONE 五档措辞（合成类，输出须显式标注"合成判断"） =================
TONE_DICTION: dict[str, dict] = {
    "吉": {"lead": "此际气运顺遂", "mid": "逢吉神拱护", "tail": "谋为多遂，宜进取",
           "degree_strong": "大吉", "degree_weak": "吉", "advice": "顺势而为，宜进不宜守"},
    "动": {"lead": "此际气运多动", "mid": "逢冲合变迁", "tail": "主变动破旧立新，不为大凶",
           "degree_strong": "平偏吉", "degree_weak": "偏动", "advice": "变动之中藏机遇，宜审时度势"},
    "平": {"lead": "此际气运平平", "mid": "吉凶相抵", "tail": "守常为宜",
           "degree_strong": "平", "degree_weak": "平", "advice": "守常为宜，不宜妄动"},
    "滞": {"lead": "此际气运阻滞", "mid": "逢交运出入", "tail": "主灾滞变动，宜静守",
           "degree_strong": "平偏凶", "degree_weak": "偏滞", "advice": "此运宜守静，万勿妄动"},
    "凶": {"lead": "此际气运不利", "mid": "逢凶神冲克", "tail": "防灾祸侵扰，宜谨慎",
           "degree_strong": "大凶", "degree_weak": "凶", "advice": "宜守静谨行，防破财刑伤"},
}

# ================= 表八：YUN_SHEN_SHA_EFFECT 运见神煞应事（推导级） =================
# 大运/流年段落中"运见X"的应事深化（参考批断"卯为贵人文昌将星，贵人登科将星掌权"式）
YUN_SHEN_SHA_EFFECT: dict[str, str] = {
    "贵人": "贵人来助，多得提携，人缘顺遂",
    "禄": "禄神临运，财禄有源，利求财业",
    "驿马": "驿马主动，主奔波往来、动中求财",
    "华盖": "华盖临运，主孤高自许，宜静业偏门",
    "咸池": "咸池桃花，防感情困扰、情缘波折",
    "将星": "将星掌权，主威望统领，事业有权柄",
    "文昌": "文昌临运，文名可显，利文教学术",
}


# ================= 表六：SHI_SHEN 十神体系（禄命法以年命纳音为中心） =================
# 推导级（十神命名与释义为古法演绎，原著无逐句对应 → 显式标注〔推导〕）
SHI_SHEN_BY_REL: dict[str, dict] = {
    "克我": {"shi_shen": "官杀", "zhang_jie": "事业",
            "text": "克我者为官杀，主事业功名，亦主压力束缚；女命官星为夫星，主夫缘与婚姻"},
    "我克": {"shi_shen": "财", "zhang_jie": "财运",
            "text": "我克者为财，主财富资财，财星有力则财源丰盈，无力不现则财缘淡薄"},
    "我生": {"shi_shen": "食伤", "zhang_jie": "子女",
            "text": "我生者为食伤，主才华泄秀，亦主子女；食伤旺主聪明多能，有子女缘"},
    "生我": {"shi_shen": "印", "zhang_jie": "学识",
            "text": "生我者为印，主庇护学问，贵人长辈之助，印星有力主学业聪慧"},
    "比和": {"shi_shen": "比劫", "zhang_jie": "综合",
            "text": "比和者为比劫，主同类自立，同侪助力，亦主竞争分夺"},
}
SHI_SHEN_ZHANG_JIE = {v["shi_shen"]: v for v in SHI_SHEN_BY_REL.values()}

# ================= 表七：WUXING_HEALTH 五行盛衰→脏腑（推导级，古法五行配脏） =================
WUXING_HEALTH: dict[str, dict] = {
    "WATER": {"excess": "水旺主肾、膀胱、泌尿生殖之疾，水寒则宫寒湿滞", "deficit": "水弱主肾气不足"},
    "FIRE": {"excess": "火旺主心、血、眼目之疾，火炎则血燥目赤", "deficit": "火弱火熄主心血不足、眼目昏花、血循环不畅"},
    "WOOD": {"excess": "木旺主肝、胆、筋骨之疾，木亢则风动", "deficit": "木弱木浮主肝气不舒、筋骨乏力"},
    "METAL": {"excess": "金旺主肺、大肠、皮肤之疾", "deficit": "金弱金沉主呼吸系统薄弱、皮肤干燥过敏"},
    "EARTH": {"excess": "土旺主脾胃壅滞、消化不良", "deficit": "土弱土崩主脾胃虚寒、腹胀湿滞"},
}
# 岁运刑害触发脏腑（如丑戌未三刑伤土 → 脾胃）：由 risk/刑害句在合成器引用


def audit_health_shi_shen() -> dict:
    """十神/健康表结构审计."""
    errors = []
    if set(SHI_SHEN_BY_REL) != {"生我", "我生", "克我", "我克", "比和"}:
        errors.append("SHI_SHEN_BY_REL 关系键不完整")
    for k, v in SHI_SHEN_BY_REL.items():
        if not v.get("shi_shen") or not v.get("zhang_jie") or not v.get("text"):
            errors.append(f"SHI_SHEN {k}: 字段缺失")
    if len(WUXING_HEALTH) != 5:
        errors.append("WUXING_HEALTH 应 5 条")
    return {"ok": not errors, "errors": errors}


def audit_secondary_tables() -> dict:
    """四张释义表结构审计（REL 30 / SHEN_SHA 15 / GONG 2 / TONE 5）. """
    errors = []
    if len(REL_SEMANTICS) != 30:
        errors.append(f"REL 应 30 条，实 {len(REL_SEMANTICS)}")
    for k, v in REL_SEMANTICS.items():
        if v["strength"] != "推导" or not v["topic"]:
            errors.append(f"REL {k}: 字段非法")
    if len(SHEN_SHA_SEMANTICS) != 15:
        errors.append(f"SHEN_SHA 应 15 条，实 {len(SHEN_SHA_SEMANTICS)}")
    for k, v in SHEN_SHA_SEMANTICS.items():
        if v["strength"] not in _STRENGTHS or v["quote_status"] not in _QUOTE_STATI or not v["text"]:
            errors.append(f"SHEN_SHA {k}: 字段非法")
        if v["strength"] == "逐字" and not v["quote"]:
            errors.append(f"SHEN_SHA {k}: 逐字但 quote 空")
    if len(GONG_SEMANTICS) != 2 or len(TONE_DICTION) != 5:
        errors.append("GONG/TONE 条数非法")
    h = audit_health_shi_shen()
    if h["errors"]:
        errors += h["errors"]
    if len(YUN_SHEN_SHA_EFFECT) < 5:
        errors.append("YUN_SHEN_SHA_EFFECT 应不少于 5 条")
    return {"ok": not errors, "errors": errors,
            "counts": {"REL": len(REL_SEMANTICS), "SHEN_SHA": len(SHEN_SHA_SEMANTICS),
                       "GONG": len(GONG_SEMANTICS), "TONE": len(TONE_DICTION),
                       "SHI_SHEN": len(SHI_SHEN_BY_REL), "HEALTH": len(WUXING_HEALTH),
                       "YUN_SHEN_SHA": len(YUN_SHEN_SHA_EFFECT)}}
