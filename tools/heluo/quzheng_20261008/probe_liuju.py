# -*- coding: utf-8 -*-
"""验 interpretation 现在真的在用六项原典判据，且随输入变。"""
import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

from heluo_engine.engines.heluo.interpretation import (  # noqa: E402
    HeluoInput, RelationalInterpretationEngine)

out = []


def mk(**kw):
    d = dict(prenatal_hexagram="乾上乾下", yuan_tang="五爻",
             postnatal_hexagram="乾上坤下", day_hexagram="屯上蒙下",
             year_cycle="乙巳", month_cycle="甲申", day_cycle="丙午",
             element_state={"木": 0.6, "火": 0.8, "土": 0.3, "金": 0.5, "水": 0.7},
             line_position={"active_line": 5, "position_type": "尊位",
                            "yinyang": "阳"},
             time_state={"solar_term": "立秋", "hour": 14})
    d.update(kw)
    return HeluoInput(**d)


cases = [
    ("默认（乾上乾下 / 元堂五爻）", {}),
    ("元堂改二爻（应改判据结果）", {"yuan_tang": "二爻"}),
    ("元堂改初爻", {"yuan_tang": "初爻"}),
    ("卦名改兑（原文明举吉卦含兑）", {"prenatal_hexagram": "兑上兑下"}),
    ("卦名改坎（不在明举例内）", {"prenatal_hexagram": "坎上坎下"}),
    ("元堂爻名不可解析", {"yuan_tang": "?"}),
    ("卦名不可解析", {"prenatal_hexagram": "???"}),
]

out.append("%-32s %-8s %-8s %s" % ("案例", "base", "已判项", "吉/凶/不判"))
out.append("-" * 96)
for label, kw in cases:
    e = RelationalInterpretationEngine(mk(**kw))
    base, ju = e._liuju_base()
    n = len(ju.get("吉", [])) + len(ju.get("凶", []))
    out.append("%-32s %-8s %-8s 吉=%s 凶=%s 不判=%s"
               % (label, base, n, ju.get("吉", []), ju.get("凶", []),
                  ju.get("不判", [])))

out.append("")
out.append("== 明细留证（默认案例）==")
e = RelationalInterpretationEngine(mk())
base, ju = e._liuju_base()
for k in sorted(ju.get("明细", {})):
    out.append("  %-4s %s" % (k, ju["明细"][k][:78]))
out.append("  刻度说明: %s" % ju.get("刻度说明"))
out.append("")
out.append("== compute() 端到端不再抛 NotImplementedError ==")
r = RelationalInterpretationEngine(mk()).compute()
out.append("  current_state: %s" % r.current_state[:56])
out.append("  opportunity   : %s / %.2f" % (r.opportunity.type, r.opportunity.strength))
out.append("  risk          : %s / %.2f" % (r.risk.type, r.risk.severity))
out.append("  meta.confidence_score = %s" % r.meta.get("confidence_score"))

io.open(ROOT / "tools" / "heluo" / "quzheng_20261008" / "liuju_probe.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))