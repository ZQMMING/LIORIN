"""Z83: 限运进阶——《紫微斗数全书》限运叠加规则。

只录原典明确的限运叠加规则。
不做成"某星在限=吉/凶"，保留条件结构：
  本命Fact + 大限Fact + 流年/小限/太岁Fact + 限运叠加 → Rule → Assertion
school=CLASSICAL_SOURCE。

Z80-H 接线（2026-10-15）：本模块资产已接入生产 —— 落点 classical_detail.limit_advanced（build_answer 顶层键 classical_detail，独立通道，
  不并入 12 宫位维/体用层）。
  依据：docs/audit/ZIWEI_ENGINE_FULL_AUDIT_20261014.md（Z80-H 收口）
"""
from __future__ import annotations

SRC = "紫微斗数全书"

# ============================================================
# 羊陀迭并 / 七杀重逢
# ============================================================
LIMIT_ADVANCED_RULES = [
    {
        "rule_id": "LA-01",
        "name": "羊陀迭并",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论羊陀迭并第九十二",
        "verbatim": "如庚年生人，命在卯宫，迁移在酉宫。如遇羊陀，流年亦庚禄居申，流羊在酉，流陀在未，是命在卯宫原有酉宫擎羊冲合，流年又遇流羊流陀，谓之羊陀迭并。",
        "condition": "本命已有擎羊/陀罗在对宫冲合 + 流年流羊/流陀又冲照同宫",
        "definition": "本命羊陀 + 流羊流陀叠并冲照 = 羊陀迭并",
    },
    {
        "rule_id": "LA-02",
        "name": "七杀重逢",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论七杀重逢第九十三",
        "verbatim": "如命中三合原有七杀守照，而流年又遇流羊流陀冲照凶，七杀重逢二者为祸最毒。入庙灾晦减轻，如陷地逢忌及卯酉遇擎羊为闲宫，午生人不利也。然七杀逢吉曜众亦转凶化吉，不可一概论凶。擎羊陀罗七杀逢紫微天相禄存三合拱照可解。",
        "condition": "本命三合原有七杀守照 + 流年流羊流陀冲照",
        "breaking_condition": "入庙减轻；逢紫微天相禄存三合拱照可解",
    },
    {
        "rule_id": "LA-03",
        "name": "行限分南北斗",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论行限分南北斗第八十九",
        "verbatim": "阳男阴女南斗为福。阴男阳女北斗为福。北斗诸星吉凶，大限断上五年应，小限断上半年应。南斗诸星吉凶，大限断下五年应，小限断下半年应。",
        "condition": "大限/小限应期按南北斗分前后半",
    },
    {
        "rule_id": "LA-04",
        "name": "大限十年祸福",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论大限十年祸福何如第八十七",
        "verbatim": "如宫分星缠全吉庙旺得地，无擎羊陀罗火铃空劫者，主十年安静，人财全美。若限内有擎羊陀罗火铃空劫忌星为伴，成败不一。如宫分星缠陷地，值擎羊陀罗火铃空劫忌，又加流年恶杀凑合，及小限巡逢凶杀，则官灾死亡立见。",
        "condition": "大限宫星庙旺无煞→十年吉；陷地加煞加流年恶杀加小限凶杀→官灾死亡",
    },
    {
        "rule_id": "LA-05",
        "name": "二限太岁吉凶",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论二限太岁吉凶第八十八",
        "verbatim": "须详大限独守吉凶何如，小限独守吉凶何如，太岁独守吉凶何如。如岁限俱凶则凶。又看大限与小限相逢吉凶何如，大限逢太岁吉凶何如，小限逢太岁吉凶何如，祸福所定。又看太岁冲大限小限，太岁冲羊陀七杀，然后可断吉凶。",
        "condition": "大限+小限+太岁三者叠加，非单一断",
    },
    {
        "rule_id": "LA-06",
        "name": "流年太岁三方对照",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论流年太岁吉凶星杀第九十",
        "verbatim": "凡太岁看三方对照星辰吉凶何如以定祸福，太岁在命宫行者祸福尤紧。",
        "condition": "太岁看三方四正，非本宫单断",
    },
    {
        "rule_id": "LA-07",
        "name": "天伤天使夹限",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论大限十年祸福何如第八十七",
        "verbatim": "凡大小二限及太岁，怕行天伤天使夹地，怕行天空地劫之地，怕行擎羊陀罗之地，及羊陀冲照。如天伤在子，天使在寅，岁限在丑宫，乃并夹也。羊陀守命尚且无用，况夹限乎。",
        "condition": "天伤+天使夹岁限宫位 = 凶",
    },
]


def count() -> int:
    return len(LIMIT_ADVANCED_RULES)
