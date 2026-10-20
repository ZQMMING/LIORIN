# -*- coding: utf-8 -*-
"""
Qintian Judgment Resolver — 钦天门判定层（Z44 蔡明宏主源版）

严格工程边界：
- 本模块只负责"组合命中 → 判定结论"映射
- 不涉及数据计算（combinations / features 负责）
- 不做最终用户判断（结论文字给"辨"层用）
- judgment_strength 仅作 raw 输出（"强弱"由"辨"层综合计算）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
from .combinations import QintianCombination


@dataclass
class QintianJudgment:
    rule_id: str
    evidence_grade: int
    judgment_strength: str  # "strong" / "moderate" / "weak" / "neutral"
    neutral_facts: List[str]


# Judgment 映射表（Z80-H 补齐：60 键 / 60 条 production 全覆盖，蔡明宏体系）
# 注：Z80-G 实测仅 28 键，32 条 production 无判定文本而落 neutral（内容缺口）。
#     本轮将余 32 条的 neutral_facts 严格转写自各 detect 的古典语义摘要
#     （蔡明宏《悟我十八年》/《飞星秘仪》/ 陆斌兆《讲义》），未新增命理内容。
#     resolve_judgment 仍保留 fail-closed：未登记 rule_id → neutral。
JUDGMENT_MAPPING: Dict[str, Dict] = {
    "QTN-CMB-031": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "四化对应四季：科春、权夏、禄秋、忌冬",
            "四化相应天地人物：禄天、权地、科人、忌物",
            "化科化权一组（木火一家）；化禄化忌一组（金水同航）",
        ],
    },
    "QTN-CMB-032": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "财帛宫干四化：禄权科入本命三合是自立谋生贵中之财",
            "照三合赚钱能力大于入三合",
            "化忌宜入本命三合为吉，不宜冲三合为凶，以上班薪俸为宜",
        ],
    },
    "QTN-CMB-033": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "官禄宫干四化：禄权科入三合是自立谋生事业顺利",
            "照三合亦主事业顺利多方面发展，照发展大于入",
            "化忌宜入三合为吉稳定（薪俸并不代表升迁），不宜冲三合为凶不稳定变动多",
        ],
    },
    "QTN-CMB-029": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "大限六亲宫化忌不宜冲本命之某六亲宫，主该六亲对该六亲缘份薄或对待不佳",
            "理则：用不可冲体，若禄权科照体则为佳论",
        ],
    },
    "QTN-CMB-030": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "三方（命财官）见生年禄权科主贵",
            "所落禄权科之宫位均有自化，则贵中有损其格，贵达不显",
        ],
    },
    "QTN-CMB-028": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "十干四化逐星论断（甲-癸）随生年干而定，见 qintian_shihua_readings 数据表",
            "每干四化星对应吉凶面向（禄主财名、权主权势变动、科主名声地位、忌主破耗是非）",
            "辛干文曲科原文缺失，该条不输出",
        ],
    },
    "QTN-CMB-025": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "田宅宫飞化入田宅三合：住宅附近环境有物相应",
            "田宅宫飞化入本命三合（含照命三合）：祖产有无及财源应用",
            "田宅宫飞化入迁移、子女：代表驿马",
            "命、财、官飞化入田宅：可见有无增置不动产",
        ],
    },
    "QTN-CMB-026": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "六阳宫主贵，六阴宫主富",
            "三吉化于六阴者，要成就的基本条件是人和；得有人和者财利随之而来",
        ],
    },
    "QTN-CMB-027": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "三方（命财官）见禄权科主贵",
            "来因宫在财帛：贵靠自己自立独谋；来因宫在兄弟：贵需借朋友兄弟之协，否则三方见亦成假象",
        ],
    },
    "QTN-CMB-023": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "命宫干四化显示命格高低：禄权科入本命三合主贵格自立更生",
            "禄权科照（夫迁福）亦主贵但须借他人之助",
            "化忌入本命三合不失格但犯小人；化忌冲三合损贵格宜薪俸",
        ],
    },
    "QTN-CMB-024": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "六亲宫（命兄弟夫妻子女交友父母）谁化忌冲谁均主缘薄",
            "谁化忌入谁虽不佳但比冲吉，只可解口角意见多",
        ],
    },
    "QTN-CMB-022": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "生年四化有单象与双象之别，平衡其理一定要单对单、双对双",
            "不平衡则法象：把自化去法生年同类（同类归类并兼看宫位）",
            "生年四化单星自化（如廉贞化禄又自化忌）属单对单平衡之变格",
        ],
    },
    "QTN-CMB-020": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "用神：祿忌一組、權科一組（来因宫四化分出用神）",
            "权科用神必须配合忌（权科用神的媒介一定要有化忌）",
            "来因宫自化者，论命由来因宫做缘起，用神优先次序=权科组",
        ],
    },
    "QTN-CMB-021": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "十二宫分六阳六阴，一阴一阳相为表里共六对（命↔迁移、兄弟↔交友、夫妻↔官禄、子女↔田宅、财帛↔福德、疾厄↔父母）",
            "对宫互飞同断：命宫化忌入迁移有驿马在外之命，迁移化忌入命宫解释一样",
        ],
    },
    "QTN-CMB-001": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "来因宫即命盘太极，确定一生主题与活动空间",
            "生年干=因果起点",
        ],
    },
    "QTN-CMB-002": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "钦天时空结构完整：体(生年四化/空间) + 用(自化/时间)齐备",
            "自化触发生年四化能量（体用合一）",
        ],
    },
    "QTN-CMB-004": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "向心自化主物质的凝聚",
            "箭头向内，能量回收于本宫",
        ],
    },
    "QTN-CMB-006": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "串联自化：同向自化跨多宫联动",
            "事件由单点变多点连锁",
        ],
    },
    "QTN-CMB-007": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "离心自化主物质的分散",
            "把已有的事物现象变成没有或改变另一种模式",
        ],
    },
    "QTN-CMB-011": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "自化五分类：生年四化 × 自化 的有无组合",
            "分类决定自化论命的切入层次",
        ],
    },
    "QTN-CMB-012": {
        "judgment_strength": "weak",
        "neutral_facts_template": [
            "出入视角：入=自化面对生年四化，出=自化背离生年四化",
            "用于判断事件面向（向内收敛/向外发散）",
        ],
    },
    "QTN-CMB-013": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "法象：自化之象对照生年四化宫位",
            "依两宫位互动产生吉凶征兆",
        ],
    },
    "QTN-CMB-014": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "命为体身为用：身宫=此生追求/执念/果报落点",
            "35岁后身宫权重放大，首看生年四化/宫内自化/三方四正",
        ],
    },
    "QTN-CMB-019": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "生年斗君在某宫，一生课题集中该宫与其对待宫",
            "十二宫以六宫论：命宫100%|迁移70%，兄弟100%|交友70%，夫妻100%|官禄70%，子女100%|田宅70%，财帛100%|福德70%，疾厄100%|父母70%",
        ],
    },
    "QTN-CMB-018": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "取意托乎随心而化乃名自化（自化之解）",
            "自化有反其意之作用：本好可变坏，本坏可变好，逢自化不可拘泥原本之意",
        ],
    },
    "QTN-CMB-017": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "大限应用一律与本命息息相关，宫位为飞化定点时与生年四化发生关系",
            "大限四化以本命盘宫干为用（本命为天、大限为地、流年为人）",
            "大限化禄逢生年忌成双忌论（书例）",
        ],
    },
    "QTN-CMB-016": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "流年四化以本命盘原始宫干为主（飞星秘仪），不用流年干",
            "若用流年干：四化为定象不可再转化，忌冲为凶；不与生年四化对待",
        ],
    },
    "QTN-CMB-015": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "生年四化落宫单象解义：以落宫断该宫位的人生课题基调",
            "生年四化本身无吉凶（静象），吉凶须待后天飞化碰撞（动象）",
        ],
    },
    # ── Z80-H 补齐（32 条）：neutral_facts 逐条转写自 combinations.py 各
    #    detect 的古典语义摘要，不新增命理内容；strength 沿用既有分层惯例
    #    （结构决定性=strong / 一般组合=moderate / 轻微征象=weak）。──
    "QTN-CMB-003": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "自化是一件事物现象本俱该有的平衡原理，如五行不能太过或不及",
            "太过与不及则失其平衡性，致吉凶生焉",
            "自化应时间（不论大限或流年）而发，无为而自化，强调时空效应法则",
        ],
    },
    "QTN-CMB-005": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "自化之「理」= 宇宙万有现象的平衡原理（太极即来因宫）",
            "自化之「象」= 现象有时空的出入",
            "自化之「数」= 现象存在的另一种变化论",
            "自化之「气」= 时间上种种不同物相的存有论",
        ],
    },
    "QTN-CMB-008": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "自化次序：生年忌再自化禄，如今年冬天植物到明年秋天收成，是即次序",
            "生年忌在财再自化禄：本是劳碌或上班的安定薪俸财，化忌再自化禄代表会由少到多的量",
        ],
    },
    "QTN-CMB-009": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "生年四化是「理」的本体存在论（有物在先）",
            "生年又自化是自化的「用」，在体上发生种种情况的变化",
            "自化的象都要法象到生年四化上去，再由宫位上判断现象的吉凶祸福",
        ],
    },
    "QTN-CMB-010": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "自化基本分类：生年单星自化、生年双星自化、生年四化自化又串联、无生年四化但有自化并串联",
            "来因宫自化者另见来因宫专解，不在此限",
        ],
    },
    "QTN-CMB-034": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "五行局：水二局、木三局、金四局、土五局、火六局，各局有根气与心性论断",
            "五行局论断为南/北派共用部分（陆斌兆《紫微斗数讲义》王亭之注解）",
        ],
    },
    "QTN-CMB-035": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "五行局×身宫：身宫落六寄宫（命/财帛/官禄/迁移/福德/夫妻）才有组合论断",
            "身宫落非六寄宫无论断（fail-closed）",
        ],
    },
    "QTN-CMB-036": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "财帛宫化忌显示不吉之象，则禄、权、科同时显示不吉利解",
            "化忌凶时，三吉化亦凶；化忌为吉时，三吉化亦吉",
        ],
    },
    "QTN-CMB-037": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "化禄在财帛：能自立谋生、自创业赚钱、忙碌、不善理财",
            "化权在财帛：善于用钱创业、不存死钱、利于周转活用",
            "化科在财帛：代表以上班宜，且安定不善变动，并主贵人相助良多",
        ],
    },
    "QTN-CMB-038": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "破军在夫妻/子女宫：容易有失，即留不住、耗损现象",
            "巨门入六亲宫：排斥性较强，象征遗弃星，在夫妻宫宜晚婚",
            "地空/地劫在夫妻宫：使婚姻难以成局",
        ],
    },
    "QTN-CMB-039": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "化忌在夫妻：忌星在六亲宫代表亏欠，主此人必有太太或先生，不必为婚姻之事烦恼",
            "唯不宜太早婚，婚前会有波折",
        ],
    },
    "QTN-CMB-040": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "紫微化科：名声远扬、贵人提拔、地位高升；若见四煞星，升迁受挫、破财招损",
            "左辅右弼三合会巨门/天机/七杀/四煞等，主命格较低",
            "命宫三方见生年禄权科本主贵，三合再见四煞则贵中有折、贵达不显",
        ],
    },
    "QTN-CMB-041": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "擎羊（羊刃）：化气为刑伤、凶厄之神，主灾杀，易见血光，个性好强激烈",
            "破军：也是血光星，对本身而言多外伤",
            "太阴：又称血光之星，与开刀有关",
            "天机化忌：代表死亡星，四肢易有外伤，或机械、车祸之事发生",
        ],
    },
    "QTN-CMB-042": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "四象法：宫位无主星，不借对宫之星为用，以本无主星之宫位的宫干为四化飞化要诀，以象其宫位之吉凶",
            "命宫无主星而宫干飞化致对宫成双忌者，成双忌论，力量加倍",
        ],
    },
    "QTN-CMB-043": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "化忌在命，又化忌，难贵显，格局难在中上层面",
            "纵任有财，层面不变",
        ],
    },
    "QTN-CMB-044": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "四化分单象与双象之排列组合，合十干归四象，演四象步十干，单双相对法两仪",
            "没有固定谁吉谁凶，因它是象，象是假象",
            "禄忌：禄不可解忌，以双忌论，主凶；禄权：财利、发达",
        ],
    },
    "QTN-CMB-045": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "命宫宫干与生年干相同，显示双倍之函义，故吉凶成败有强烈分明之别",
            "忌星坐命，上班为宜；宫干坐甲而太阳又化忌，可谓为臣不为君之格，若强而为君格终究必败，宜幕后之使者",
        ],
    },
    "QTN-CMB-046": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "命宫三合不见生年禄、权、科，而命宫自坐生年忌，主白手起家",
            "贵达难显，以上班或技术为生计",
        ],
    },
    "QTN-CMB-047": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "夫妻宫坐生年三吉化（禄/权/科任一）者，已象征在此大限会结婚",
            "不论顺行或逆行，均于第三个大限为结婚限",
        ],
    },
    "QTN-CMB-048": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "天刑星代表官非与牢狱之灾，尤其逢化忌时要注意",
            "天刑与生年化忌同宫，须防官非牢狱",
        ],
    },
    "QTN-CMB-049": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "天刑星不宜入夫妻宫，容易有离婚现象，晚婚佳",
        ],
    },
    "QTN-CMB-050": {
        "judgment_strength": "weak",
        "neutral_facts_template": [
            "天姚星在夫妻宫，夫妻双方都有人缘，多艳遇",
        ],
    },
    "QTN-CMB-051": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "武曲化忌：财星化忌，主财不利、周转不灵、倒债多",
            "武曲化忌与天刑同宫，因官非刑罚，宜节省守财",
        ],
    },
    "QTN-CMB-052": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "太阳化忌：不利男性、父、夫、子，眼目有疾",
            "太阳化忌与天刑星逢化忌同宫，注意牢狱之灾",
        ],
    },
    "QTN-CMB-053": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "大限四化以本命盘宫干为用（本命为天、大限为地），大限化忌入天刑宫",
            "此大限防官非牢狱之灾（应期层）",
        ],
    },
    "QTN-CMB-054": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "流月即指流年十二个月的吉凶，法流年而行",
            "流月用斗君起正月（斗君一定在原命盘寅位之宫位），流月四化飞曜天干一律用本命盘天干",
        ],
    },
    "QTN-CMB-055": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "流月宫本命盘宫干四化，化忌星落天刑所在宫，该流月官非牢狱结构成立",
            "应期到月，吉否仍参看生年/大限对待",
        ],
    },
    "QTN-CMB-056": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "禄、权、科全在六阴位，非自立格，若要有成必须有贵人于背后辅佐，才有自立可言",
            "三吉化于六阴者，要成就的基本条件是「人和」，若失人和则注定失败",
            "得有人和者，财利亦随之而来，是人荫其财",
        ],
    },
    "QTN-CMB-057": {
        "judgment_strength": "moderate",
        "neutral_facts_template": [
            "本命为天：生年四化与大限错综，断大限吉凶；大限为地：大限介于本命与流年之间为机纽；流年为人：生年四化与流年错综，断流年吉凶",
            "大限为天、流年为地、流月为人，亦三合而一；四化之飞曜天干一律用本命盘天干，不可另取用",
        ],
    },
    "QTN-CMB-058": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "辛干四化：巨门化禄、太阳化权、文曲化科、文昌化忌",
            "子女宫宫干坐辛，巨门化禄与文昌化忌同宫在财帛，虽言双忌必有子女，因忌入财帛与命三合；唯双忌主不多产，宜注意母体健康",
            "太阳化权入命宫，有子女，唯将来子女均独立，即自立更生格，个性比较刚强",
        ],
    },
    "QTN-CMB-059": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "大限忌与流年忌同落一宫，双忌叠加（应期到年）",
            "中州派法：单忌有转圜，双忌需提前止损；此年该宫代表事项需高度留意",
        ],
    },
    "QTN-CMB-060": {
        "judgment_strength": "strong",
        "neutral_facts_template": [
            "本命、大限、流年三层忌落同一宫位，称三忌同宫/三忌叠加",
            "此年该宫代表事项为全年风险焦点，需优先留意（事件概率大幅提升）",
        ],
    },
}


def resolve_judgment(combo: QintianCombination) -> QintianJudgment:
    """根据组合命中返回判定结论 (raw, 无最终解释)"""
    if combo.rule_id not in JUDGMENT_MAPPING:
        # fail-closed: 未知规则返回 neutral
        return QintianJudgment(
            rule_id=combo.rule_id,
            evidence_grade=combo.evidence_grade,
            judgment_strength="neutral",
            neutral_facts=[],
        )

    m = JUDGMENT_MAPPING[combo.rule_id]
    return QintianJudgment(
        rule_id=combo.rule_id,
        evidence_grade=combo.evidence_grade,
        judgment_strength=m["judgment_strength"],
        neutral_facts=list(m["neutral_facts_template"]),
    )
