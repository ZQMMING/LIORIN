# -*- coding: utf-8 -*-
"""查地点注册表支持哪些别名，中山/广东是否在内。"""
import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

from heluo_engine.engines.time.location_registry import LocationRegistry  # noqa: E402
import heluo_engine.engines.time.location_registry as lr  # noqa: E402

out = []
print("模块文件:", lr.__file__)
src = io.open(lr.__file__, encoding="utf-8").read()
print("行数:", len(src.split("\n")))

reg = LocationRegistry()
out.append("别名总数: %d" % len(getattr(reg, "_by_alias", {})))
alias = sorted(getattr(reg, "_by_alias", {}))
out.append("前 40 个别名: %s" % alias[:40])
out.append("")
for kw in ("中山", "广东", "广州", "深圳", "珠海", "佛山", "东莞", "惠州"):
    hits = [a for a in alias if kw in a]
    out.append("  含「%s」: %s" % (kw, hits[:8] if hits else "无"))

out.append("")
out.append("=== 数据来源 ===")
for i, l in enumerate(src.split("\n")[:60], 1):
    out.append("%4d| %s" % (i, l[:100]))

io.open(ROOT / "tools" / "heluo" / "quzheng_20261008" / "loc_probe.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out[:26]))