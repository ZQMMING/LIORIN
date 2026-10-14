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


# Judgment 映射表（Z80-G 实测 28 键 / 60 条 production，蔡明宏体系）
# 注：未登记的 rule_id 落 neutral 分支（见 resolve_judgment），
#     当前 32 条 production 无判定文本 —— 属内容缺口，待补。
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
