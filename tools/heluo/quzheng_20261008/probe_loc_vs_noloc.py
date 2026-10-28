# -*- coding: utf-8 -*-
"""对照：同一案例，带 location 与不带的差别 —— 定位紫微层打挂的触发条件。"""
import io
import os
import sys
import traceback
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")
os.environ.setdefault(
    "TONGSHU_AUTHORITY_CREDENTIALS",
    "architecture-governance:schema-v1-arch-gov-2026;admission_registry:test-cred-hash")

from tongshu.pipeline import TONGSHUPipeline  # noqa: E402

BIRTH = (1983, 11, 3, 12)
out = []
p = TONGSHUPipeline.for_demo(ROOT)

for label, kw in [
    ("不带 location", {}),
    ("location='中山'", {"location": "中山", "timezone": "Asia/Shanghai"}),
    ("只给 timezone", {"timezone": "Asia/Shanghai"}),
    ("location 不存在的地名", {"location": "不存在市", "timezone": "Asia/Shanghai"}),
]:
    out.append("── %s" % label)
    try:
        r = p.run(analysis_date=date(2026, 10, 8), birth_date=BIRTH,
                  gender="male", theme="WORK", compute_only=True,
                  heluo_target_date=date(2026, 8, 17), **kw)
        h = r.heluo_result
        out.append("   ✅ 跑通   heluo=%s  guajie=%s  四柱=%s"
                   % ("有" if h else "None",
                      "有" if (h and h.guajie) else "无",
                      "-"))
        if h and h.numbers:
            out.append("      天数/地数 = %s/%s" % (h.numbers.tian_shu,
                                              h.numbers.di_shu))
    except Exception as exc:
        out.append("   ❌ 抛异常 %s: %s" % (type(exc).__name__,
                                          str(exc).splitlines()[0][:90]))
        tb = traceback.format_exc().splitlines()
        for l in tb[-6:-1]:
            if "File " in l:
                out.append("      " + l.strip()[:100])
    out.append("")

io.open(ROOT / "tools" / "heluo" / "quzheng_20261008" / "loc_vs_noloc.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))