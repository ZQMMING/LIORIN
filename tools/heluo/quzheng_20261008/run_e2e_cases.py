# -*- coding: utf-8 -*-
"""端到端案例跑批：经**完整排盘链路**（TONGSHUPipeline），不经手工拼 bazi。

目的：查本轮改动之后，排盘链路上还有哪些问题没冒出来。
手工调 HeluoCanonical 只能验证化工这一层；真正的风险在上游
（八字引擎 → 先天/后天 → 元堂 → 化工 → 解卦 → 冻结态）任一处断链时，
下游会静默降级而没人知道。

打印：每案跑批状态 + 化工取法/状态 + 解卦判词条数 + 全链路降级痕迹。

用法：
  PYTHONPATH=src python tools/heluo/quzheng_20261008/run_e2e_cases.py
"""
import io
import os
import sys
import traceback
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

from tongshu.pipeline import TONGSHUPipeline  # noqa: E402

CASES = [
    ("A 纪晓岚（已翻转 Golden）", (1724, 5, 22, 12), "male"),
    ("B 回归案例", (1983, 11, 3, 12), "male"),
    ("C 纯卦男乾", (1980, 3, 16, 8), "male"),
    ("D 寅月生（旧近似表整月判错）", (1985, 3, 2, 12), "male"),
    ("E 巳月生（旧近似表整月判错）", (1988, 5, 20, 12), "male"),
    ("F 申月生（旧近似表整月判错）", (1991, 8, 25, 12), "male"),
    ("G 亥月生（旧近似表整月判错）", (1994, 11, 8, 12), "male"),
    ("H 卯月上半月（跨窗口月）", (1997, 3, 12, 12), "male"),
    ("I 午月上半月（跨窗口月）", (1999, 6, 10, 12), "male"),
    ("J 酉月上半月（跨窗口月）", (2001, 9, 18, 12), "male"),
    ("K 女命巳月", (1986, 5, 30, 12), "female"),
    ("L 现代样例", (1995, 8, 15, 14), "female"),
    ("M 边界 立春当日", (1988, 2, 4, 12), "male"),
    ("N 边界 冬至当日", (1990, 12, 22, 12), "male"),
    ("O 边界 白露当日", (1993, 9, 8, 12), "male"),
]

ANALYSIS = date(2026, 10, 8)
TARGET = date(2026, 8, 17)

out = []
out.append("=" * 96)
out.append("端到端案例跑批（TONGSHUPipeline 全链路）  分析日 %s  流年日 %s"
           % (ANALYSIS, TARGET))
out.append("=" * 96)
out.append("%-30s %-4s %-4s %-4s %-6s %-8s %-5s %s"
           % ("案例", "四柱", "先天", "后天", "化工", "状态", "节候", "解卦"))
out.append("-" * 96)

pipeline = TONGSHUPipeline.for_demo(ROOT)
issues = []
notes = []
n_ok = 0

for label, bd, gender in CASES:
    try:
        r = pipeline.run(analysis_date=ANALYSIS, birth_date=bd, gender=gender,
                         theme="WORK", compute_only=True,
                         heluo_target_date=TARGET)
        h = r.heluo_result
        if h is None:
            issues.append("%s: heluo_result 为 None（整层没算出来）" % label)
            out.append("%-30s %s" % (label, "❌ heluo_result=None"))
            continue
        g = h.guajie or {}
        fs = None
        try:
            from tongshu.engines.heluo.frozen_state import build_frozen_state
            fs = build_frozen_state(h)
        except Exception as exc:
            issues.append("%s: 冻结态构建失败 %s: %s" % (label,
                                                     type(exc).__name__, exc))
        hv = (getattr(h, "hua_gong", None))
        state = getattr(getattr(hv, "state", None), "value", "—")
        tri = getattr(hv, "huagong_trigram", "—")
        sh = getattr(h, "seasonal_hexagram", None) or {}
        jq = sh.get("jq_name", "—")
        # 找化工取法那一行
        basis = "—"
        for e in (getattr(hv, "evidence", None) or []):
            if "取法" in e:
                basis = ("节气窗口" if "节气窗口" in e else
                         "兜底近似表" if "兜底" in e else "—")
                break
        if basis == "兜底近似表":
            issues.append("%s: 走了兜底近似表（未用原典窗口）" % label)
        ev_n = len(g.get("evidence") or [])
        if ev_n == 0:
            issues.append("%s: 解卦 evidence 为空" % label)
        if not g.get("liunian_hexagram"):
            # 先分清「断链」与「超龄盘」：大运只覆盖到约 93 虚岁，
            # 超龄后流年/月/日三层本就无从取。分不清就报断链＝误报。
            age = ANALYSIS.year - bd[0] + 1
            if age > 93:
                notes.append("%s: 虚岁 %d 已超大运覆盖（1–93），流年/月/日三层为空"
                             " —— **正常现象，非断链**；但下游未自曝此原因"
                             % (label, age))
            else:
                issues.append("%s: 虚岁 %d 未超龄却流年卦为空（解卦层可能没接上）"
                              % (label, age))
        pre = getattr(h.prenatal, "hexagram_name", "—") if h.prenatal else "—"
        post = getattr(h.postnatal, "hexagram_name", "—") if h.postnatal else "—"
        n_ok += 1
        out.append("%-30s %-4s %-4s %-4s %-6s %-8s %-5s %s(%d条)"
                   % (label, "有", pre, post, "%s%s" % (tri, basis[:0]),
                      state, jq, "解卦", ev_n))
    except Exception as exc:
        issues.append("%s: 跑批抛异常 %s: %s" % (label, type(exc).__name__, exc))
        out.append("%-30s ❌ %s: %s" % (label, type(exc).__name__, exc))
        out.append("     " + traceback.format_exc().splitlines()[-3][:88])

out.append("-" * 96)
out.append("跑通 %d / %d 例" % (n_ok, len(CASES)))

out.append("")
out.append("=" * 96)
out.append("问题清单（issues = 需要查的）")
out.append("=" * 96)
if not issues:
    out.append("（无）")
for i in issues:
    out.append("· " + i)
out.append("")
out.append("观察（notes = 已知现象，非本轮引入）")
for n in notes:
    out.append("· " + n)

io.open(ROOT / "tools" / "heluo" / "quzheng_20261008" / "e2e_case_run.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))