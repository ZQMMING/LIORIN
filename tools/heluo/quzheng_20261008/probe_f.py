# -*- coding: utf-8 -*-
"""实测：爻辞取象 + 三条新数格在真实链路上是否真产出。"""
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
from tongshu.engines.heluo.yue_ling_shu_ge import classify_shu_ge
from tongshu.engines.heluo.yao_xiang import scan_yao_xiang

out = []
P = TONGSHUPipeline.for_demo(Path(".").resolve())
r = P.run(analysis_date=date(2026, 10, 6), birth_date=(1990, 5, 20, 8),
          gender="male", theme="WORK", compute_only=True,
          heluo_target_date=date(2026, 8, 17))
g = r.heluo_result.guajie
out.append("== 排盘实测 yao_xiang_hits ==")
out.append("键存在: %s" % ("yao_xiang_hits" in g))
hits = g.get("yao_xiang_hits") or []
out.append("命中条数: %d" % len(hits))
for h in hits[:8]:
    out.append("   言%s → %s | 条件=%s | satisfied=%s | 参与判定=%s"
               % (h["key"], h["verdict"][:24], h["condition"][:20],
                  h["satisfied"], h["participated"]))
out.append("-- evidence 里的取象行 --")
for e in (g.get("evidence") or []):
    if "取象" in e:
        out.append("   " + e)

out.append("")
out.append("== 三条新数格实测 ==")
for t, d, want in [(20, 30, "阴阳偏胜偏负"), (25, 20, "阴阳偏胜偏负"),
                   (30, 30, "阴阳偏胜偏负"), (25, 40, "阴阳偏胜偏负"),
                   (45, 20, "以强凌弱"), (50, 5, "以强凌弱"),
                   (39, 20, "以强凌弱"), (15, 55, "以下犯上"),
                   (24, 50, "以下犯上"), (25, 55, "以下犯上")]:
    names = [x.name for x in classify_shu_ge(t, d)]
    hit = "命中" if want in names else "未命中"
    out.append("  天%2d/地%2d  期望%s %s | 实得: %s"
               % (t, d, want, "✓" if want in names else "✗", "、".join(names)))

out.append("")
out.append("== 阴阳偏胜偏负 四支穷举边界 ==")
b = [x for x in classify_shu_ge(25, 40) if x.name == "阴阳偏胜偏负"][0]
for lo_t, hi_t, lo_d, hi_d in b.alternatives:
    out.append("   支(%d-%d, %d-%d): 内点=%s 边界外侧=%s"
               % (lo_t, hi_t, lo_d, hi_d,
                  any(x.name == "阴阳偏胜偏负" for x in classify_shu_ge((lo_t + hi_t) // 2, (lo_d + hi_d) // 2)),
                  any(x.name == "阴阳偏胜偏负" for x in
                      classify_shu_ge(min(hi_t, 24), lo_d)) if lo_t == 0 else "-"))

out.append("")
out.append("== yao_xiang 条件判定抽查 ==")
for txt, m, g_, sx in [("初九：龙战于野", 5, "male", False),
                       ("九五：鸿渐于陆", None, "", None),
                       ("言木之华", 4, "", None),
                       ("六二：朋亡", 5, "female", None)]:
    hh = scan_yao_xiang(txt, birth_month=m, gender=g_, shu_gua_xiang=sx)
    out.append("  %-12s → %s" % (txt, [(h.key, h.satisfied, h.participated) for h in hh]))

io.open("probe_f.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))