# -*- coding: utf-8 -*-
"""核实三处：① 数格方向两层不一致 ② judgment.domain ③ source_ref 重复。"""
import io
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")
os.environ.setdefault(
    "TONGSHU_AUTHORITY_CREDENTIALS",
    "architecture-governance:schema-v1-arch-gov-2026;admission_registry:test-cred-hash")

from heluo_engine.engines.heluo.frozen_state import build_frozen_state  # noqa: E402
from heluo_engine.engines.heluo.guajie import judge_shu_xiong  # noqa: E402
from heluo_engine.engines.heluo import diagnosis_rule_graph as dg  # noqa: E402
from tongshu.pipeline import TONGSHUPipeline  # noqa: E402

out = []
r = TONGSHUPipeline.for_demo(ROOT).run(
    analysis_date=date(2026, 10, 8), birth_date=(1983, 11, 3, 12),
    gender="male", theme="WORK", compute_only=True,
    heluo_target_date=date(2026, 8, 17))
H = r.heluo_result
fs = build_frozen_state(H)

out.append("== ① 数格：解卦层 vs 诊断层 ==")
bj = judge_shu_xiong(H.numbers.tian_shu, H.numbers.di_shu, 11, "male")
out.append("  解卦层(birth_month=11): shu_xiong=%s  pattern=%s"
           % (bj.shu_xiong, bj.pattern))
for bm in (None, 11):
    d, note = dg.heluo_own_direction("HL_TIAN_DI_SHU", fs)
    out.append("  诊断层 当前实现: %s  (%s)"
               % (d.value if d else None, note))
# 手动试带 birth_month
d2 = judge_shu_xiong(H.numbers.tian_shu, H.numbers.di_shu, 11, "male")
out.append("  手动带 birth_month=11: shu_xiong=%s pattern=%s"
           % (d2.shu_xiong, d2.pattern))
out.append("  frozen_state.birth_date = %r" % fs.birth_date)
out.append("  frozen_state 有 birth_month 字段? %s"
           % ("birth_month" in fs.__dataclass_fields__))

out.append("")
out.append("== ② judgment.domain ==")
jd = r.heluo_diagnosis.judgment
out.append("  domain=%r  type=%s" % (jd.domain, type(jd.domain).__name__))
out.append("  → 我上一条报告说 domain=None 是**探针 bug**：把字符串当枚举取 .value")

out.append("")
out.append("== ③ source_ref 重复 ==")
g = r.heluo_guidance
for a in g.action_items:
    if "HELUO_RULES" in (a.source_ref or ""):
        ids = a.source_ref.split("::", 1)[1].split(",")
        out.append("  %s: %d 段, 去重后 %d 段"
                   % (a.title, len(ids), len(set(ids))))
        out.append("     重复项: %s"
                   % [x for x in set(ids) if ids.count(x) > 1])

io.open(ROOT / "tools" / "heluo" / "quzheng_20261008" / "check3.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))