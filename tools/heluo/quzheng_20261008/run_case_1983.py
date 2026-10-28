# -*- coding: utf-8 -*-
"""单个真实案例的全量报告：1983-11-03 午时 男（广东中山）。

走完整排盘链路 TONGSHUPipeline，把每一层的实际输出都倒出来，
并附本盘的关键计算次数，便于对照「哪里算了几遍」。

用法：
  PYTHONPATH=src python tools/heluo/quzheng_20261008/run_case_1983.py
"""
import io
import os
import sys
import time
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

from heluo_engine.engines.heluo import diagnosis_rule_graph as dg   # noqa: E402
from heluo_engine.engines.heluo.frozen_state import build_frozen_state  # noqa: E402
from tongshu.pipeline import TONGSHUPipeline  # noqa: E402

BIRTH = (1983, 11, 3, 12)
GENDER = "male"
LOCATION = "中山"          # 「广东中山」这种省+市拼接查不到，见 loc_coverage.txt
TZ = "Asia/Shanghai"
ANALYSIS = date(2026, 10, 8)
TARGET = date(2026, 8, 17)

# ── 计算次数统计 ────────────────────────────────────────────────
CNT: Counter = Counter()
_o_fs, _o_byy = sxtwl.fromSolar, sxtwl.getJieQiByYear
sxtwl.fromSolar = lambda *a, **k: (CNT.update(["sxtwl.fromSolar"]),
                                   _o_fs(*a, **k))[1]
sxtwl.getJieQiByYear = lambda *a, **k: (CNT.update(["sxtwl.getJieQiByYear"]),
                                       _o_byy(*a, **k))[1]

out = []


def sec(t):
    out.append("")
    out.append("─" * 88)
    out.append(t)
    out.append("─" * 88)


def kv(k, v):
    out.append("  %-16s %s" % (k, v))


t0 = time.perf_counter()
LOC_MODE = "已启用"
try:
    r = TONGSHUPipeline.for_demo(ROOT).run(
        analysis_date=ANALYSIS, birth_date=BIRTH, gender=GENDER, theme="WORK",
        compute_only=True, timezone=TZ, location=LOCATION,
        heluo_target_date=TARGET)
except Exception as exc:  # noqa: BLE001
    # ⚠ 2026-10-08 实测：传 location 会让 calc_context 生效，紫微改走
    #   ziwei_adapter → Node/iztro 硬路径；本机没装 iztro 时异常**逃逸**，
    #   整条排盘链路挂掉（不传 location 则走 ziwei_engine 的 stub 兜底、正常）。
    #   这是**紫微引擎**的缺陷，不在河洛域内，本脚本只做回退并如实标注。
    LOC_MODE = ("⚠ 已回退（未传 location）：紫微层缺 iztro 时 ziwei_adapter 抛异常"
                "打挂整链 —— 紫微域缺陷，非河洛")
    r = TONGSHUPipeline.for_demo(ROOT).run(
        analysis_date=ANALYSIS, birth_date=BIRTH, gender=GENDER, theme="WORK",
        compute_only=True, heluo_target_date=TARGET)
dt = time.perf_counter() - t0

H = r.heluo_result
out.append("╔" + "═" * 86 + "╗")
out.append("║ 案例：1983-11-03 12:00（午时） 男  广东中山" + " " * 34 + "║")
out.append("║ 分析日 %s  流年日 %s  耗时 %.2fs  %s%s║"
           % (ANALYSIS, TARGET, dt, LOC_MODE[:22], " " * 4))
out.append("╚" + "═" * 86 + "╝")

# ── 四柱 ────────────────────────────────────────────────────
sec("【1】四柱与时间（八字引擎）")
try:
    _c = getattr(r, "canonical", None)
    _bz = getattr(_c, "bazi_chart", None) if _c else None
    if _bz is not None:
        for nm, p in (("年柱", _bz.year_pillar), ("月柱", _bz.month_pillar),
                      ("日柱", _bz.day_pillar), ("时柱", _bz.hour_pillar)):
            kv(nm, "%s%s" % (p.stem, p.branch))
        kv("日主", "%s（%s）" % (_bz.day_master, _bz.day_master_element))
    else:
        # 河洛主链自带四柱（bazi[0..3] 透传），直接用它，不另找来源
        _b = (H.prenatal, H.yuantang, H.postnatal)
        kv("四柱来源", "canonical 无 bazi_chart 字段，改用河洛内部透传")
except Exception as exc:
    kv("四柱", "读取失败 %s" % exc)

# ── 河洛主链 ────────────────────────────────────────────────
sec("【2】河洛主链")
kv("天数 / 地数", "%d / %d　（归一 %d / %d）"
   % (H.numbers.tian_shu, H.numbers.di_shu,
      H.numbers.tian_reduced, H.numbers.di_reduced))
kv("先天卦", "%s（上%s 下%s）五行 %s"
   % (H.prenatal.hexagram_name, H.prenatal.upper_gua, H.prenatal.lower_gua,
      getattr(H.prenatal, "five_elements", "—")))
kv("后天卦", "%s（上%s 下%s）六爻 %s"
   % (H.postnatal.hexagram_name, H.postnatal.upper_gua,
      H.postnatal.lower_gua, list(H.postnatal.lines)))
kv("元堂", "%s（index=%d，%s爻）六爻 %s"
   % (H.yuantang.yuantang, H.yuantang.yuantang_index,
      getattr(H.yuantang, "yao_nature", "—"),
      list(getattr(H.yuantang, "lines", []) or [])))
if H.structure:
    _st = H.structure
    kv("卦象结构", "%s｜体用 %s｜生克 %s｜互体 %s"
       % (_st.name, getattr(_st, "ti_yong", getattr(_st, "ti_use", "—")),
          getattr(_st, "sheng_ke", "—"),
          getattr(_st, "hu_gua", getattr(_st, "cuo_gua", "—"))))
sh = H.seasonal_hexagram or {}
kv("节候卦", "%s（jq=%s）%s %s"
   % (sh.get("jq_name"), sh.get("jq_index"),
      sh.get("main_gua", ""), sh.get("moving_line", "")))

# ── 化工 ────────────────────────────────────────────────────
sec("【3】化工（原典 L558–L567 节气窗口）")
hg = H.hua_gong
for e in hg.evidence[:6]:
    out.append("  · %s" % e)
kv("结论", "%s　当令化工卦=%s　层=%s　减半=%s"
   % (hg.state.value, hg.huagong_trigram, hg.level, hg.reduced))

# ── 时间轴 ──────────────────────────────────────────────────
sec("【4】大运与流年")
if H.timeline:
    segs = H.timeline.yearly_hexagrams
    out.append("  大运/流年段：%d 段" % len(segs))
    for s in segs[:3] + ([{"age": "…"}] if len(segs) > 8 else []) + segs[-3:]:
        if "age" in s and s.get("age") == "…":
            out.append("      …")
            continue
        out.append("      %s–%s  %s %s" % (s.get("start_age"), s.get("end_age"),
                                          s.get("hexagram_name", ""),
                                          s.get("ganzhi", "")))

# ── 解卦 ────────────────────────────────────────────────────
sec("【5】解卦判词")
g = H.guajie or {}
kv("流年 / 流月 / 流日", "%s / %s / %s"
   % (g.get("liunian_hexagram"), g.get("liuyue_hexagram"),
      g.get("liuri_hexagram")))
ev = g.get("evidence") or []
kv("evidence 条数", len(ev))
for e in ev[:10]:
    out.append("  · %s" % e)
if len(ev) > 10:
    out.append("  · …（其余 %d 条）" % (len(ev) - 10))

# ── 诊断与建议 ──────────────────────────────────────────────
sec("【6】河洛诊断（H12）")
d = r.heluo_diagnosis
own = dg.heluo_own_basis()
out.append("  %-24s %-11s %s" % ("规则", "方向", "来源"))
out.append("  " + "─" * 62)
for a in d.assertions:
    src = "河洛判据" if a.source_rule in own else (
        "信号层" if str(a.source_rule).startswith("ZPZ") else "默认")
    out.append("  %-24s %-11s %s" % (a.source_rule, a.direction.value, src))
kv("丢弃（未注册）", dg.dropped_rules())
kv("无信号可依", dg.unmatched_evidence())
for k, v in sorted(own.items()):
    out.append("  判据依据 %-20s %s" % (k, v[:60]))
jd = d.judgment
kv("判决", "domain=%s｜%s｜支撑 %d 条｜授权 %s"
   % (getattr(getattr(jd, "domain", None), "value", None),
      getattr(jd, "semantic", ""), len(getattr(jd, "supporting_assertions", []) or []),
      (getattr(jd, "authorized_by", "") or "")[:56]))

sec("【7】行动建议")
gd = r.heluo_guidance
out.append("  总览：%s" % gd.overview)
for i, a in enumerate(gd.action_items, 1):
    out.append("  %d. [%s] %s" % (i, a.title, a.description))
    out.append("     置信 %.2f　出处 %s　时效 %s"
               % (a.confidence, a.source_ref, a.temporal_scope))
for c in gd.caution_items:
    out.append("  ⚠ %s" % c)

# ── 计算次数 ────────────────────────────────────────────────
sec("【8】本盘关键计算次数")
for k in ("sxtwl.fromSolar", "sxtwl.getJieQiByYear"):
    out.append("  %-26s %d" % (k, CNT.get(k, 0)))
out.append("  （河洛自身各层主链均为 1 次，详见 call_counts.txt）")

io.open(ROOT / "tools" / "heluo" / "quzheng_20261008" / "case_1983.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))