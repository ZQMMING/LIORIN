# -*- coding: utf-8 -*-
"""验批次 K：河洛诊断方向是否已来自河洛自己的判据。"""
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

from tongshu.pipeline import TONGSHUPipeline  # noqa: E402
from tongshu.engines.heluo import diagnosis_rule_graph as dg  # noqa: E402

out = []
CASES = [
    ("1983-11-03 男（回归案例）", (1983, 11, 3, 12), "male"),
    ("1990-05-20 男", (1990, 5, 20, 8), "male"),
    ("1995-08-15 女", (1995, 8, 15, 14), "female"),
    ("1985-03-02 男", (1985, 3, 2, 12), "male"),
    ("2001-09-18 男", (2001, 9, 18, 12), "male"),
]

p = TONGSHUPipeline.for_demo(ROOT)
for label, bd, g in CASES:
    r = p.run(analysis_date=date(2026, 10, 8), birth_date=bd, gender=g,
              theme="WORK", compute_only=True,
              heluo_target_date=date(2026, 8, 17))
    d = r.heluo_diagnosis
    own = dg.heluo_own_basis()
    out.append("── %s" % label)
    out.append("   断言 %d 条" % len(d.assertions))
    for a in d.assertions:
        src = "河洛判据" if a.source_rule in own else "信号/默认"
        out.append("     · %-26s %-11s [%s]" % (a.source_rule,
                                            a.direction.value, src))
    out.append("   河洛自有判据命中 %d 条: %s"
               % (len(own), sorted(own)))
    for k, v in sorted(own.items()):
        out.append("       %-24s %s" % (k, v[:64]))
    out.append("   无信号可依: %s" % dg.unmatched_evidence())
    out.append("")

io.open(ROOT / "tools" / "heluo" / "quzheng_20261008" / "own_direction.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out[:34]))