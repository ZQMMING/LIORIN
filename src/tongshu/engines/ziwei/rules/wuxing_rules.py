"""Z84: 五行生克/星辰制化——《紫微斗数全书》第五十八/五十九。

只录原典明确的星曜五行属性+制化规则。
school=CLASSICAL_SOURCE，不污染南北派。

Z80-G 审核标注（2026-10-14）：本模块在 src/ 内**零引用**（仅测试/文档提及）。
  处置建议：证据资产 —— 星曜五行 + 生克制化原典录入
  依据：docs/audit/ZIWEI_ENGINE_FULL_AUDIT_20261014.md
"""
from __future__ import annotations

SRC = "紫微斗数全书"

# ============================================================
# 星曜五行属性（第五十九）
# ============================================================
STAR_WUXING = {
    # 十四主星
    "紫微": {"wuxing": "土", "dou": "南北斗", "role": "帝座/官禄主"},
    "天机": {"wuxing": "木", "dou": "南斗", "role": "善/兄弟主"},
    "太阳": {"wuxing": "火", "dou": "南北斗", "role": "贵/官禄主"},
    "武曲": {"wuxing": "金", "dou": "北斗", "role": "财/财帛主"},
    "天同": {"wuxing": "水金", "dou": "南斗", "role": "福/福德主"},
    "廉贞": {"wuxing": "火", "dou": "北斗", "role": "杀囚/官禄主/次桃花"},
    "天府": {"wuxing": "土", "dou": "南斗", "role": "令星/财帛田宅主"},
    "太阴": {"wuxing": "水", "dou": "南北斗", "role": "富/财帛田宅主"},
    "贪狼": {"wuxing": "水木", "dou": "北斗", "role": "桃花杀/祸福主"},
    "巨门": {"wuxing": "水", "dou": "北斗", "role": "暗/是非主"},
    "天相": {"wuxing": "水", "dou": "南斗", "role": "印/官禄主"},
    "天梁": {"wuxing": "土", "dou": "南斗", "role": "荫/寿星"},
    "七杀": {"wuxing": "火金", "dou": "南斗", "role": "降星/遇帝为权"},
    "破军": {"wuxing": "水", "dou": "北斗", "role": "耗/夫妻子女奴仆"},
    # 辅曜
    "禄存": {"wuxing": "土", "dou": "北斗", "role": "爵贵寿星"},
    "左辅": {"wuxing": None, "dou": "北斗", "role": "善住令星"},
    "右弼": {"wuxing": None, "dou": "北斗", "role": "善住令星"},
    "文昌": {"wuxing": "金", "dou": "南北斗", "role": "科甲/文魁之首"},
    "文曲": {"wuxing": "水", "dou": "北斗", "role": "科甲"},
    "天魁": {"wuxing": "火", "dou": None, "role": "贵人"},
    "天钺": {"wuxing": "火", "dou": None, "role": "贵人"},
    "天马": {"wuxing": "火", "dou": None, "role": "驿马"},
    # 煞曜
    "擎羊": {"wuxing": "金", "dou": "北斗", "role": "刑"},
    "陀罗": {"wuxing": "金", "dou": "北斗", "role": "忌"},
    "火星": {"wuxing": "火", "dou": "南斗", "role": "助星"},
    "铃星": {"wuxing": "火", "dou": "南斗", "role": "助星"},
    "地空": {"wuxing": "火", "dou": None, "role": "空亡"},
    "地劫": {"wuxing": "火", "dou": None, "role": "空亡"},
    # 杂曜
    "天伤": {"wuxing": "水", "dou": None, "role": "虚耗"},
    "天使": {"wuxing": "水", "dou": None, "role": "传使"},
    # 四化
    "化禄": {"wuxing": "土", "dou": None, "role": "喜见禄存"},
    "化权": {"wuxing": "木", "dou": None, "role": "喜会巨门武曲"},
    "化科": {"wuxing": "水", "dou": None, "role": "喜会魁钺"},
    "化忌": {"wuxing": "水", "dou": None, "role": "计都星"},
    # 桃花
    "红鸾": {"wuxing": "水", "dou": None, "role": "婚姻"},
    "天喜": {"wuxing": "水", "dou": None, "role": "婚姻"},
}

# ============================================================
# 制化规则（第五十八）
# ============================================================
WUXING_RULES = [
    {
        "rule_id": "WX-01",
        "name": "星曜落宫五行生克",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论星辰生克制化第五十八",
        "verbatim": "星曜全明生克制化之机，次看落于何宫，如廉真属火在寅宫，乃木乡能生廉真之火，若武曲金星与廉真同度，则武曲为财而无用也。",
        "condition": "星曜五行+落宫五行生克关系",
        "example": "廉贞(火)在寅(木)→木生火→生旺；武曲(金)与廉贞(火)同度→火克金→武曲无用",
    },
    {
        "rule_id": "WX-02",
        "name": "受制四种",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论星辰生克制化第五十八",
        "verbatim": "金入火乡，火入水乡，水入土乡，土入木乡，俱为受制。",
        "condition": "星曜五行+落宫五行被克→受制",
        "list": ["金入火乡", "火入水乡", "水入土乡", "土入木乡"],
    },
    {
        "rule_id": "WX-03",
        "name": "紫微制杀",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论命宫诀第六十五",
        "verbatim": "紫微...其威制七杀降火铃。",
        "condition": "紫微在三方四正→可制七杀/火铃之凶",
    },
]


def count() -> dict:
    return {
        "star_wuxing": len(STAR_WUXING),
        "rules": len(WUXING_RULES),
    }
