# -*- coding: utf-8 -*-
"""查 yao_xiang 命中为 0 的原因：辞面到底有没有字。"""
import io
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, "src")
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")
os.environ.setdefault("TONGSHU_AUTHORITY_CREDENTIALS",
                      "architecture-governance:schema-v1-arch-gov-2026;"
                      "admission_registry:test-cred-hash")

from tongshu.pipeline import TONGSHUPipeline

out = []
P = TONGSHUPipeline.for_demo(Path(".").resolve())
r = P.run(analysis_date=date(2026, 10, 6), birth_date=(1990, 5, 20, 8),
          gender="male", theme="WORK", compute_only=True,
          heluo_target_date=date(2026, 8, 17))
g = r.heluo_result.guajie
out.append("流年卦=%s 流月卦=%s 流日卦=%s"
           % (g["liunian_hexagram"], g["liuyue_hexagram"], g["liuri_hexagram"]))
for k in ("liunian", "liuyue", "liuri"):
    yd = g.get(k + "_yao") or {}
    out.append("%s: yao=%r" % (k, yd.get("yao")))
    out.append("   ci=%r" % (yd.get("ci") or "")[:90])
    out.append("   xiang=%r" % (yd.get("xiang") or "")[:90])
    out.append("   len(ci)=%d len(xiang)=%d"
               % (len(yd.get("ci") or ""), len(yd.get("xiang") or "")))

out.append("")
out.append("== 语料统计：全库 384 爻辞里有几个字能触发取象 ==")
import json
d = json.load(io.open("data/heluo/guajie_jingyi.json", encoding="utf-8"))
out.append("顶层键: %s" % (list(d)[:8],))
keys = [k for k in d if "yao" in k.lower() or "爻" in k]
out.append("爻辞相关键样例: %s (共%d)" % (keys[:5], len(keys)))

io.open("probe_f2.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))