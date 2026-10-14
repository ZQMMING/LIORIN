"""Z86: 童限/小儿命——《紫微斗数全书》第五十/第八十一~八十五。

只录原典明确的童限安法+小儿断语。
school=CLASSICAL_SOURCE。

Z80-G 审核标注（2026-10-14）：本模块在 src/ 内**零引用**（仅测试/文档提及）。
  处置建议：应接线 —— 童限/小儿命，production 无
  依据：docs/audit/ZIWEI_ENGINE_FULL_AUDIT_20261014.md
"""
from __future__ import annotations

SRC = "紫微斗数全书"

# ============================================================
# 童限安法（第五十）
# ============================================================
CHILD_LIMIT_RULES = [
    {
        "rule_id": "CL-01",
        "name": "童限安法",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "安童限诀第五十",
        "verbatim": "一命二财三疾厄，四妻五福六官禄，余年一派顺流行，十五命宫看端的。",
        "condition": "童限1岁命宫→2岁财帛→3岁疾厄→4岁夫妻→5岁福德→6岁官禄→顺行→15岁回命宫",
    },
    {
        "rule_id": "CL-02",
        "name": "小儿命断法",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论小儿命第八十一",
        "verbatim": "小儿初生，命中星辰庙旺，大小二限未行，断其灾少，易养，父母无克。若命坐恶杀及缠陷弱之地，大小二限未行，断其灾多，难养，刑克父母。",
        "condition": "小儿命坐庙旺→易养无克；坐恶杀陷地→难养刑克父母",
    },
    {
        "rule_id": "CL-03",
        "name": "小儿克亲",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论小儿克亲第八十五",
        "verbatim": "如寅午巳酉生人，见辰戌丑未时最毒，子申亥卯生人次之。若寅亥巳生人，见午申酉亥时，主先克父，出十六岁则不妨。若辰巳丑未生人，见子午卯巳亥申酉时生者，主先克母。",
        "condition": "特定生年+生时组合→先克父/先克母",
    },
    {
        "rule_id": "CL-04",
        "name": "生时阴阳安命",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "论人生时安命吉凶第八十三",
        "verbatim": "凡男女生在寅午戌申子辰六阳时，安命在此六宫者吉。生在巳酉丑亥卯未六阴时，安命在此六宫者吉。反此则少遂。",
        "condition": "阳时安命阳宫→吉；阴时安命阴宫→吉；反此→少遂",
    },
    {
        "rule_id": "CL-05",
        "name": "十二宫强弱",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "安十二宫弱强第五十五",
        "verbatim": "男命：财帛、官禄、福德、迁移、田宅为强宫，子女、奴仆、兄弟、父母为弱宫。女命：夫君、子息、财帛、田宅、福德为强，余宫皆弱。",
        "condition": "男命强宫=财官福迁田；女命强宫=夫妻子福田",
    },
]


def count() -> int:
    return len(CHILD_LIMIT_RULES)
