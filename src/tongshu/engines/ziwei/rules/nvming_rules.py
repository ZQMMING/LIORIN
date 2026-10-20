"""Z81: 女命体系——《紫微斗数全书·女命骨髓赋》+女命专条。

只录原典明确的女命专属规则。
不复制男女通用规则，不强行扩展"女命十二宫完整体系"。
school=CLASSICAL_SOURCE。

Z80-H 接线（2026-10-15）：本模块资产已接入生产 —— 落点 classical_detail.nvming（build_answer 顶层键 classical_detail，独立通道，
  不并入 12 宫位维/体用层）。
  依据：docs/audit/ZIWEI_ENGINE_FULL_AUDIT_20261014.md（Z80-H 收口）
"""
from __future__ import annotations

SRC_FU = "紫微斗数全书·女命骨髓赋第十"
SRC_ZHUAN = "紫微斗数全书·诸星问答论"

# ============================================================
# 女命骨髓赋逐条
# ============================================================
NVMING_RULES = [
    {"rule_id": "NM-01", "name": "府相女命夫贤子贵", "school": "CLASSICAL_SOURCE",
     "source": SRC_FU, "source_section": "女命骨髓赋",
     "verbatim": "府相之星女命躔，必当子贵与夫贤。廉贞清白能相守，更有天同理亦然。",
     "condition": "女命 命宫坐天府/天相/廉贞/天同",
     "good_stars": ["天府","天相","廉贞","天同"]},
    {"rule_id": "NM-02", "name": "紫太阳星女命早遇贤夫", "school": "CLASSICAL_SOURCE",
     "source": SRC_FU, "source_section": "女命骨髓赋",
     "verbatim": "端正紫微太阳星，早遇贤夫性可凭。太阳寅到午，遇吉终是福。",
     "condition": "女命 命宫坐紫微/太阳 且 在寅~午宫",
     "good_stars": ["紫微","太阳"]},
    {"rule_id": "NM-03", "name": "左辅天魁女命福寿", "school": "CLASSICAL_SOURCE",
     "source": SRC_FU, "source_section": "女命骨髓赋",
     "verbatim": "左辅天魁为福寿，左弼天相福相临。禄存厚重多衣食，府相朝垣命必荣。",
     "condition": "女命 命宫坐左辅/天魁/右弼/天相/禄存",
     "good_stars": ["左辅","天魁","右弼","天相","禄存"]},
    {"rule_id": "NM-04", "name": "紫府巳亥女命福生", "school": "CLASSICAL_SOURCE",
     "source": SRC_FU, "source_section": "女命骨髓赋",
     "verbatim": "紫府巳亥相互辅，左右扶持福必生。",
     "condition": "女命 命宫在巳/亥 且坐紫微天府",
     "good_stars": ["紫微","天府"]},
    {"rule_id": "NM-05", "name": "巨门机梁女命贫破", "school": "CLASSICAL_SOURCE",
     "source": SRC_FU, "source_section": "女命骨髓赋",
     "verbatim": "巨门天机为破荡。天梁月曜女命贫。",
     "condition": "女命 命宫坐巨门/天机/天梁/太阴",
     "bad_stars": ["巨门","天机","天梁","太阴"]},
    {"rule_id": "NM-06", "name": "羊火昌曲女命福不全", "school": "CLASSICAL_SOURCE",
     "source": SRC_FU, "source_section": "女命骨髓赋",
     "verbatim": "擎羊火星为下贱。文昌文曲福不全。武曲之宿为寡宿。破军一曜性难明。",
     "condition": "女命 命宫坐擎羊/火星/文昌/文曲/武曲/破军",
     "bad_stars": ["擎羊","火星","文昌","文曲","武曲","破军"]},
    {"rule_id": "NM-07", "name": "贪狼七杀女命淫贱", "school": "CLASSICAL_SOURCE",
     "source": SRC_FU, "source_section": "女命骨髓赋",
     "verbatim": "贪狼内狠多淫佚。七杀沉吟福不荣。",
     "condition": "女命 命宫坐贪狼/七杀",
     "bad_stars": ["贪狼","七杀"]},
    {"rule_id": "NM-08", "name": "女命化禄旺夫益子", "school": "CLASSICAL_SOURCE",
     "source": SRC_FU, "source_section": "女命骨髓赋",
     "verbatim": "十干化禄最荣昌，女命逢之大吉昌。更得禄存相凑合，旺夫益子受恩光。",
     "condition": "女命 生年化禄 或 命宫坐禄存",
     "good_stars": ["化禄","禄存"]},
    {"rule_id": "NM-09", "name": "女命杀临夫宫祸患深", "school": "CLASSICAL_SOURCE",
     "source": SRC_FU, "source_section": "女命骨髓赋",
     "verbatim": "火铃羊陀及巨门，天空地劫又相临。贪狼七杀廉贞宿，武曲加临克害侵。三方四正嫌逢杀，更在夫宫祸患深。若是本宫无正曜，必主生离克害真。",
     "condition": "女命 夫妻宫坐煞星/化忌/无正曜",
     "bad_stars": ["火星","铃星","擎羊","陀罗","巨门","地空","地劫","贪狼","七杀","廉贞","武曲"]},
]

# ============================================================
# 女命专条（诸星问答论等）
# ============================================================
NVMING_ZHUAN = [
    {"rule_id": "NMZ-01", "name": "紫微女命旺夫益子", "school": "CLASSICAL_SOURCE",
     "source": SRC_ZHUAN, "source_section": "诸星问答论·紫微",
     "verbatim": "女命紫微太阳星早遇贤夫信可凭。女命紫微在寅午申宫吉，贵美旺夫益子。陷地平常，惟子酉及巳亥加四杀，美玉瑕玷日后不美。",
     "condition": "女命 命宫坐紫微 在寅午申宫",
     "good_stars": ["紫微"]},
    {"rule_id": "NMZ-02", "name": "天同女命贤", "school": "CLASSICAL_SOURCE",
     "source": SRC_ZHUAN, "source_section": "诸星问答论·天同",
     "verbatim": "女命天同必是贤。子生人命坐寅，辛人命卯，丁人命戌入格。丙辛人命中吉，己亥逢此化吉虽美必淫。",
     "condition": "女命 命宫坐天同",
     "good_stars": ["天同"]},
    {"rule_id": "NMZ-03", "name": "天相女命子贵夫贤", "school": "CLASSICAL_SOURCE",
     "source": SRC_ZHUAN, "source_section": "诸星问答论·天相",
     "verbatim": "天相之星女命缠必当子贵及夫贤。女命己生子宫，甲生午宫，庚生辰宫，俱是贵格。",
     "condition": "女命 命宫坐天相",
     "good_stars": ["天相"]},
    {"rule_id": "NMZ-04", "name": "天梁女命淫贫", "school": "CLASSICAL_SOURCE",
     "source": SRC_ZHUAN, "source_section": "诸星问答论·天梁",
     "verbatim": "天梁月曜女淫贫。梁巳亥阴寅申主淫佚，不陷衣禄遂如陷下贱。",
     "condition": "女命 命宫坐天梁 在巳亥寅申",
     "bad_stars": ["天梁"]},
    {"rule_id": "NMZ-05", "name": "太阳女命旺夫", "school": "CLASSICAL_SOURCE",
     "source": SRC_ZHUAN, "source_section": "诸星问答论·太阳",
     "verbatim": "女命端正太阳星早配贤夫信可凭。太阳守命，陷平常。居卯辰巳午无杀，旺夫益子。",
     "condition": "女命 命宫坐太阳 在卯辰巳午",
     "good_stars": ["太阳"]},
    {"rule_id": "NMZ-06", "name": "太阴女命淫贫", "school": "CLASSICAL_SOURCE",
     "source": SRC_ZHUAN, "source_section": "诸星问答论·太阴",
     "verbatim": "月曜天梁女淫贫。太阴寅申巳，多主淫贫，或偏房侍婢。",
     "condition": "女命 命宫坐太阴 在寅申巳",
     "bad_stars": ["太阴"]},
]

ALL_NVMING = NVMING_RULES + NVMING_ZHUAN


def count() -> dict:
    return {
        "nvming_best": len(NVMING_RULES),
        "nvming_zhuan": len(NVMING_ZHUAN),
        "total": len(ALL_NVMING),
    }
