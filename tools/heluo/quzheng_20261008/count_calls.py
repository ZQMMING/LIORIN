# -*- coding: utf-8 -*-
"""一次真实排盘，统计各河洛计算函数的**实际调用次数**（修好类方法计数版）。

上一版探针有两个缺陷：
  1. 用 getattr(mod, "Class.method") 取类方法取不到 → 11 项误报「0 次」
  2. 只报总数不报调用来源 → 看不出 sxtwl.getJieQiByYear 282 次是谁调的

本版：类方法走 setattr(Class, name, wrapper)；
     sxtwl 两个热点入口记录调用栈的上两层，用于定位重复计算源头。

用法：
  PYTHONPATH=src python tools/heluo/quzheng_20261008/count_calls.py
"""
import io
import os
import sys
import time
import traceback
from collections import Counter
from datetime import date
from functools import wraps
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")
os.environ.setdefault(
    "TONGSHU_AUTHORITY_CREDENTIALS",
    "architecture-governance:schema-v1-arch-gov-2026;admission_registry:test-cred-hash")

import sxtwl  # noqa: E402

from tongshu.engines.heluo import (                                    # noqa: E402
    canonical, diagnosis_rule_graph, evidence_producer, frozen_state,
    guajie, gui_ming_liu_ju, hua_gong, jiegua, jiehhou, numbers,
    yuanqi_tables)
from tongshu.pipeline import TONGSHUPipeline  # noqa: E402

CNT: Counter = Counter()
SITES: dict = {}          # 计算项 -> Counter(调用点)


def _site():
    """取调用栈上最靠近本函数的一层非包装帧。"""
    st = traceback.extract_stack()
    for fr in reversed(st[:-2]):
        if "count_calls" in (fr.filename or ""):
            continue
        mod = Path(fr.filename).stem
        return "%s:%s" % (mod, fr.lineno)
    return "?"


def _count(key, orig, *a, **kw):
    CNT[key] += 1
    SITES.setdefault(key, Counter())[_site()] += 1
    return orig(*a, **kw)


def wrap(owner, dotted, label):
    """owner 可以是模块，也可以是类；dotted 支持 Class.method。"""
    parts = dotted.split(".")
    obj = owner
    for p in parts[:-1]:
        obj = getattr(obj, p, None)
        if obj is None:
            print("  跳过（不存在）: %s" % dotted)
            return
    leaf = parts[-1]
    orig = getattr(obj, leaf, None)
    if orig is None or not callable(orig):
        print("  跳过（不存在）: %s" % dotted)
        return

    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        # 模块级函数：原地替换
        @wraps(orig)
        def counted(*a, **kw):
            return _count(label, orig, *a, **kw)
        setattr(obj, leaf, counted)
    else:
        # 类方法：绑到类上，实例调用会走这里
        @wraps(orig)
        def counted(self, *a, **kw):
            return _count(label, orig, self, *a, **kw)
        setattr(obj, leaf, counted)


TARGETS = [
    (canonical, "HeluoCanonical.calculate", "canonical.calculate 河洛主链"),
    (canonical, "HeluoCanonical._compute_huagong", "canonical._compute_huagong"),
    (canonical, "HeluoCanonical._compute_seasonal_hexagram", "节候卦求 jq"),
    (canonical, "HeluoCanonical._compute_timeline", "canonical 时间轴"),
    (hua_gong, "compute_huagong", "hua_gong 化工主算"),
    (hua_gong, "huagong_by_birth_date", "hua_gong 出生日→窗口"),
    (numbers, "compute_tian_di_shu", "numbers 天数地数"),
    (numbers, "normalize_tian_shu", "numbers 天数归一"),
    (guajie, "build_guajie_from_result", "guajie 解卦"),
    (guajie, "compose_guajie", "guajie.compose 综合断卦"),
    (guajie, "judge_shu_xiong", "guajie 数格凶吉"),
    (guajie, "judge_si_duan", "guajie 死断诸法"),
    (guajie, "check_twelve_xiong", "guajie 十二凶卦"),
    (guajie, "judge_nayin_yuanqi", "guajie 纳音元气"),
    (frozen_state, "build_frozen_state", "frozen_state 冻结态"),
    (evidence_producer, "HeLuoEvidenceProducer.produce", "证据产出"),
    (diagnosis_rule_graph, "build_diagnosis_graph", "诊断图构建"),
    (diagnosis_rule_graph, "heluo_own_direction", "河洛自有判据"),
    (gui_ming_liu_ju, "judge_liu_ju", "六项贵命十体"),
    (yue_ling_shu_ge_shu := __import__(
        "tongshu.engines.heluo.yue_ling_shu_ge",
        fromlist=["x"]), "classify_shu_ge", "数格分类"),
    (jiehhou, "get_current_jieqi_info", "jiehhou 求节气"),
    (jiegua, "get_jie_gua", "jiegua 节卦"),
    (yuanqi_tables, "yuanqi_fan_ganzhi", "元气反表查值"),
]
for owner, dotted, label in TARGETS:
    wrap(owner, dotted, label)

# ── sxtwl 两个热点入口 ────────────────────────────────────────
_o_fs = sxtwl.fromSolar
_o_byy = sxtwl.getJieQiByYear

sxtwl.fromSolar = lambda *a, **kw: _count("sxtwl.fromSolar", _o_fs, *a, **kw)
sxtwl.getJieQiByYear = lambda *a, **kw: _count(
    "sxtwl.getJieQiByYear", _o_byy, *a, **kw)

CASES = [
    ("1983-11-03 12:00 男（回归案例）", (1983, 11, 3, 12), "male"),
    ("1990-05-20 08:00 男", (1990, 5, 20, 8), "male"),
]

out = []
for label, bd, g in CASES:
    CNT.clear()
    SITES.clear()
    t0 = time.perf_counter()
    r = TONGSHUPipeline.for_demo(ROOT).run(
        analysis_date=date(2026, 10, 8), birth_date=bd, gender=g,
        theme="WORK", compute_only=True,
        heluo_target_date=date(2026, 8, 17))
    dt = time.perf_counter() - t0

    out.append("=" * 96)
    out.append("%s   耗时 %.2fs" % (label, dt))
    out.append("=" * 96)
    d, gd = r.heluo_diagnosis, r.heluo_guidance
    out.append("产出：断言 %s / 建议 %s"
               % (len(d.assertions) if d else 0,
                  len(gd.action_items) if gd else 0))
    out.append("")
    out.append("%-32s %6s   主要调用点" % ("计算项", "次数"))
    out.append("-" * 96)
    for k, v in CNT.most_common():
        top = ", ".join("%s×%d" % (s, c)
                        for s, c in SITES.get(k, Counter()).most_common(3))
        out.append("%-32s %6d   %s" % (k, v, top[:44]))
    out.append("")

io.open(ROOT / "tools" / "heluo" / "quzheng_20261008" / "call_counts.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))