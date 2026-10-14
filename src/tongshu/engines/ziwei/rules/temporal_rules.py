"""Z80b: 时间层 Evidence/Rule——《紫微斗数全书》时间层解释。

Fact 来自 temporal_facts.py，本文件只接解释。
不做成"流曜=吉凶"，保留传统条件结构：
  流曜 + 落宫 + 本宫星曜 + 庙旺 + 化吉化忌 → Rule → Assertion

来源：《紫微斗数全书》卷二/卷三
- 论太岁小限星辰庙陷遇十二宫中吉凶第九十六
- 安斗君诀第四十三
- 安流禄流羊流陀诀第五十七

Z80-G 审核标注（2026-10-14）：本模块在 src/ 内**零引用**（仅测试/文档提及）。
  处置建议：应接线 —— 时间层解释（太岁小限/斗君/流曜），production 无时间层规则
  依据：docs/audit/ZIWEI_ENGINE_FULL_AUDIT_20261014.md
"""
from __future__ import annotations

SRC = "紫微斗数全书·卷二"

# ============================================================
# 小限 / 太岁 Rule
# ============================================================
# 原典第九十六：太岁+小限到某宫，看本宫星曜庙旺化吉化忌
# 不逐宫录48条（太长），先录核心原则+代表宫位

TAISUI_XIAOXIAN_RULES = [
    {
        "rule_id": "TMPL-01",
        "name": "太岁小限到子宫",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
        "verbatim": "子年太岁并小限到子宫入庙化吉：七杀破军在子宫守岁限癸庚己生人发福；巨门天机乙癸生人发福；天府天相天梁丁己庚人财旺遂心；天同丙丁生人财官双美。",
        "condition": "太岁宫=子 且 小限宫=子",
        "good_stars": ["七杀","破军","巨门","天机","天府","天相","天梁","天同"],
        "bad_stars": ["紫微"],
    },
    {
        "rule_id": "TMPL-02",
        "name": "太岁小限到子宫化凶",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
        "verbatim": "子年太岁并小限到子宫不入庙化凶：紫微在子宫守命及岁限丙戊生人悔吝，破财灾殃。",
        "condition": "太岁宫=子 且 小限宫=子 且 落陷化凶",
        "bad_stars": ["紫微"],
    },
    {
        "rule_id": "TMPL-03",
        "name": "太岁所值吉凶星总则",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
        "verbatim": "子年太岁所值吉凶星：禄存天机天同太阴昌曲辅弼破军天相廉真武曲天府巨门七杀，可断其年人财两美事事遂心。若遇贪狼紫微天梁忌星太阳擎羊，便断人财耗散孝服，本身灾晦不宁，减半论之。",
        "condition": "太岁宫星曜吉凶分类",
        "good_stars": ["禄存","天机","天同","太阴","文昌","文曲","左辅","右弼","破军","天相","廉贞","武曲","天府","巨门","七杀"],
        "bad_stars": ["贪狼","紫微","天梁","化忌","太阳","擎羊"],
    },
    # 12宫逐宫（原典第九十六完整录入）
    {"rule_id": "TMPL-04", "palace": "丑", "name": "丑年太岁小限入庙化吉", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "天机在丑守命丙辛生人发旺，天相戊生人发旺，太阴武曲丙戊生人发旺，天府廉贞戊生人发旺，天梁丙戊辛生人发旺。",
     "condition": "太岁+小限到丑宫入庙化吉",
     "good_stars": ["天机","天相","太阴","武曲","天府","廉贞","天梁"]},
    {"rule_id": "TMPL-05", "palace": "丑", "name": "丑年太岁小限不入庙化凶", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "太阴在丑宫守命戊生人悔吝，太阳星甲乙生人悔吝，天机丙辛癸生人悔吝，天同廉贞丁庚生人招官非。",
     "condition": "太岁+小限到丑宫不入庙化凶",
     "bad_stars": ["太阴","太阳","天机","天同","廉贞"]},
    {"rule_id": "TMPL-06", "palace": "寅", "name": "寅年太岁小限入庙化吉", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "紫微太阳武曲天梁七杀，甲庚丁己生人财官双美。",
     "condition": "太岁+小限到寅宫入庙化吉",
     "good_stars": ["紫微","太阳","武曲","天梁","七杀"]},
    {"rule_id": "TMPL-07", "palace": "寅", "name": "寅年太岁小限不入庙化凶", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "廉贞贪狼破军在寅，丙戊生人招官非，甲子生人不喜寅申岁限。",
     "condition": "太岁+小限到寅宫不入庙化凶",
     "bad_stars": ["廉贞","贪狼","破军"]},
    {"rule_id": "TMPL-08", "palace": "卯", "name": "卯年太岁小限入庙化吉", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "紫微天机太阳天相天府天同武曲在命乙辛生人发旺。",
     "condition": "太岁+小限到卯宫入庙化吉",
     "good_stars": ["紫微","天机","太阳","天相","天府","天同","武曲"]},
    {"rule_id": "TMPL-09", "palace": "卯", "name": "卯年太岁小限不入庙化凶", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "廉贞甲丙生人横破财，太阴甲乙生人财破灾害，庚生人亦不宜主灾害。",
     "condition": "太岁+小限到卯宫不入庙化凶",
     "bad_stars": ["廉贞","太阴"]},
    {"rule_id": "TMPL-10", "palace": "辰", "name": "辰年太岁小限入庙化吉", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "紫微贪狼七杀在辰宫守命限癸甲生人财官禄旺，天机太阳丁庚癸生人财禄发旺，天同戊庚癸生人顺遂，巨门丙辛生人遂意。",
     "condition": "太岁+小限到辰宫入庙化吉",
     "good_stars": ["紫微","贪狼","七杀","天机","太阳","天同","巨门"]},
    {"rule_id": "TMPL-11", "palace": "辰", "name": "辰年太岁小限不入庙化凶", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "贪狼武曲在辰壬癸生人灾晦，天同巨门丁庚生人灾晦，廉贞壬癸生人主灾晦至重，太阴太阳天机甲乙戊己生人灾晦。",
     "condition": "太岁+小限到辰宫不入庙化凶",
     "bad_stars": ["贪狼","武曲","天同","巨门","廉贞","太阴","太阳","天机"]},
    {"rule_id": "TMPL-12", "palace": "巳", "name": "巳年太岁小限入庙化吉", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "紫微天府天同巨门天相天梁破军丙戊辛人发福。",
     "condition": "太岁+小限到巳宫入庙化吉",
     "good_stars": ["紫微","天府","天同","巨门","天相","天梁","破军"]},
    {"rule_id": "TMPL-13", "palace": "巳", "name": "巳年太岁小限不入庙化凶", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "巨门贪狼癸丙生人口舌灾晦，太阴破军灾晦多端。",
     "condition": "太岁+小限到巳宫不入庙化凶",
     "bad_stars": ["巨门","贪狼","太阴","破军"]},
    {"rule_id": "TMPL-14", "palace": "午", "name": "午年太岁小限入庙化吉", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "紫微太阳武曲天同天梁廉贞七杀破军丁己甲癸生人进财遂心。",
     "condition": "太岁+小限到午宫入庙化吉",
     "good_stars": ["紫微","太阳","武曲","天同","天梁","廉贞","七杀","破军"]},
    {"rule_id": "TMPL-15", "palace": "午", "name": "午年太岁小限不入庙化凶", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "贪狼在丙午壬癸生人破财官灾口舌。",
     "condition": "太岁+小限到午宫不入庙化凶",
     "bad_stars": ["贪狼"]},
    {"rule_id": "TMPL-16", "palace": "未", "name": "未年太岁小限入庙化吉", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "紫微天机天府天相天梁壬乙生人发福，太阴庚壬生人发福生财。",
     "condition": "太岁+小限到未宫入庙化吉",
     "good_stars": ["紫微","天机","天府","天相","天梁","太阴"]},
    {"rule_id": "TMPL-17", "palace": "未", "name": "未年太岁小限不入庙化凶", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "太阳甲乙生人多灾晦，天同丁庚生人多灾，武曲壬癸生人生灾招官非横祸。",
     "condition": "太岁+小限到未宫不入庙化凶",
     "bad_stars": ["太阳","天同","武曲"]},
    {"rule_id": "TMPL-18", "palace": "申", "name": "申年太岁小限入庙化吉", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "廉贞破军紫微甲庚癸生人发福，巨门甲庚癸生人发福，天机丁甲癸生人发福。",
     "condition": "太岁+小限到申宫入庙化吉",
     "good_stars": ["廉贞","破军","紫微","巨门","天机"]},
    {"rule_id": "TMPL-19", "palace": "申", "name": "申年太岁小限不入庙化凶", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "天机乙戊生人灾晦，巨门丁生人不宜，廉贞丙壬生人有灾，天同甲庚生人灾祸，贪狼癸丙生人有灾祸。",
     "condition": "太岁+小限到申宫不入庙化凶",
     "bad_stars": ["天机","巨门","廉贞","天同","贪狼"]},
    {"rule_id": "TMPL-20", "palace": "酉", "name": "酉年太岁小限入庙化吉", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "紫微天机太阴酉宫守命丙戊乙辛生人进财吉利。",
     "condition": "太岁+小限到酉宫入庙化吉",
     "good_stars": ["紫微","天机","太阴"]},
    {"rule_id": "TMPL-21", "palace": "酉", "name": "酉年太岁小限不入庙化凶", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "太阳天同甲乙生人不宜，武曲庚壬生人不宜，天相甲庚生人不宜，廉贞甲庚丙辛生人不宜，天府甲庚壬生人不宜。",
     "condition": "太岁+小限到酉宫不入庙化凶",
     "bad_stars": ["太阳","天同","武曲","天相","廉贞","天府"]},
    {"rule_id": "TMPL-22", "palace": "戌", "name": "戌年太岁小限入庙化吉", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "紫微壬甲丁己生人进财，太阴丁己生人吉庆，武曲丁己甲庚生人吉庆，天机甲乙丁己生人发福，巨门己辛癸生人发福，天同廉贞破军七杀丁己甲生人发财。",
     "condition": "太岁+小限到戌宫入庙化吉",
     "good_stars": ["紫微","太阴","武曲","天机","巨门","天同","廉贞","破军","七杀"]},
    {"rule_id": "TMPL-23", "palace": "戌", "name": "戌年太岁小限不入庙化凶", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "贪狼癸生人不宜，天同庚生人不宜，天机戊生人不宜，巨门丁生人不宜，太阳甲生人不宜，廉贞丙生人不宜，武曲壬生人不宜。",
     "condition": "太岁+小限到戌宫不入庙化凶",
     "bad_stars": ["贪狼","天同","天机","巨门","太阳","廉贞","武曲"]},
    {"rule_id": "TMPL-24", "palace": "亥", "name": "亥年太岁小限入庙化吉", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "紫微天同巨门天梁壬癸戊生人吉庆，天机壬生人吉美，天相丁己生人及丙戊生人发福，太阴戊己生人财官双美。",
     "condition": "太岁+小限到亥宫入庙化吉",
     "good_stars": ["紫微","天同","巨门","天梁","天机","天相","太阴"]},
    {"rule_id": "TMPL-25", "palace": "亥", "name": "亥年太岁小限不入庙化凶", "school": "CLASSICAL_SOURCE", "source": SRC,
     "source_section": "论太岁小限星辰庙陷遇十二宫中吉凶第九十六",
     "verbatim": "廉贞丙壬癸生人不宜，武曲壬丙生人不宜，太阳甲生人不宜。",
     "condition": "太岁+小限到亥宫不入庙化凶",
     "bad_stars": ["廉贞","武曲","太阳"]},
]

# ============================================================
# 斗君 Rule
# ============================================================
DOUJUN_RULES = [
    {
        "rule_id": "TDJ-01",
        "name": "斗君=月将星",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "安斗君诀第四十三",
        "verbatim": "即月将星是也。于流年太岁宫起正月逆至本生月，又从本生月起子顺数至本生时安斗君。",
        "condition": "斗君宫位=月将，定流月吉凶",
        "note": "Fact层已算，本Rule只作概念定义，不作吉凶断",
    },
]

# ============================================================
# 流禄/流羊/流陀 Rule
# ============================================================
LIUYAO_RULES = [
    {
        "rule_id": "TLY-01",
        "name": "流禄=流年干禄存",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "安流禄流羊流陀诀第五十七",
        "verbatim": "论流年太岁。假如己丑流年流禄在午、流羊在未、流陀在巳。",
        "condition": "流禄=流年干禄存所在地支",
        "note": "流禄主年吉庆，落宫看本宫星曜",
    },
    {
        "rule_id": "TLY-02",
        "name": "流羊=流年干擎羊",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "安流禄流羊流陀诀第五十七",
        "verbatim": "流羊在未（己丑年）。",
        "condition": "流羊=流年干擎羊所在地支",
        "note": "流羊主年刑伤，落宫看本宫星曜",
    },
    {
        "rule_id": "TLY-03",
        "name": "流陀=流年干陀罗",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "安流禄流羊流陀诀第五十七",
        "verbatim": "流陀在巳（己丑年）。",
        "condition": "流陀=流年干陀罗所在地支",
        "note": "流陀主年拖延暗损，落宫看本宫星曜",
    },
]

# 汇总
ALL_TEMPORAL_RULES = TAISUI_XIAOXIAN_RULES + DOUJUN_RULES + LIUYAO_RULES


def count() -> dict:
    return {
        "taisui_xiaoxian": len(TAISUI_XIAOXIAN_RULES),
        "doujun": len(DOUJUN_RULES),
        "liuyao": len(LIUYAO_RULES),
        "total": len(ALL_TEMPORAL_RULES),
    }
