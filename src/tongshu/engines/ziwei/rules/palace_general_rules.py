"""Z85: 十二宫总论——《紫微斗数全书》论命宫诀~论父母诀总论性原则。

大部分"X星坐Y宫"断语已在 palace_star_verdicts.py 168条中覆盖。
本文件只录168条里没有的总论性原则。

Z80-G 审核标注（2026-10-14）：本模块在 src/ 内**零引用**（仅测试/文档提及）。
  处置建议：证据资产 —— 十二宫总论，部分已被 palace_star_verdicts 覆盖
  依据：docs/audit/ZIWEI_ENGINE_FULL_AUDIT_20261014.md
"""
from __future__ import annotations

SRC = "紫微斗数全书"

PALACE_GENERAL_RULES = [
    {
        "rule_id": "PG-01",
        "name": "子女宫南斗北斗定男女",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论子女诀第六十八",
        "verbatim": "又看三方四正得南斗星多主生男，北斗星多主生女。若太阳星落在阳宫主先生男，太阴星落在阴宫主先生女。",
        "condition": "子女宫三方四正南斗星多→男，北斗星多→女",
        "status": "COVERED_BY_PRINCIPLE",
    },
    {
        "rule_id": "PG-02",
        "name": "子女宫日夜忌星",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论子女诀第六十八",
        "verbatim": "日生最怕太阴临，夜生最怕太阳照，此星若在儿女宫方恐无儿。",
        "condition": "日生人子女宫坐太阴→不利子；夜生人子女宫坐太阳→不利子",
    },
    {
        "rule_id": "PG-03",
        "name": "父母宫太阳太阴定父母",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论父母诀第七十六",
        "verbatim": "凡看父母以太阳星为父，太阴星为母。太阳在陷宫主先克父，太阴星在陷宫主先克母。",
        "condition": "太阳落陷→克父；太阴落陷→克母",
    },
    {
        "rule_id": "PG-04",
        "name": "父母宫日夜生时",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论父母诀第七十六",
        "verbatim": "如二星具在陷地，只以人之本生时，日生者主父存，夜生者主母在。",
        "condition": "太阳太阴俱陷→日生父在，夜生母在",
    },
    {
        "rule_id": "PG-05",
        "name": "疾厄宫先看命宫",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论疾厄诀第七十",
        "verbatim": "先看命宫星曜落陷加羊陀火铃空劫化忌守照如何，又看疾厄宫星曜善恶庙旺落陷如何断之。",
        "condition": "断疾厄先看命宫煞忌，次看疾厄宫",
    },
    {
        "rule_id": "PG-06",
        "name": "子女宫先看本宫次看对宫",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论子女诀第六十八",
        "verbatim": "凡看子女先看本宫星宿主有几子。若加羊陀火铃空劫杀忌主生子女有刑克，次看对宫有冲刑否。如本宫无星曜专看对宫有何星宿主有几子。",
        "condition": "子女宫无正曜→看对宫；加煞忌→刑克",
    },
]


def count() -> int:
    return len(PALACE_GENERAL_RULES)
