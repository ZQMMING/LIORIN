# -*- coding: utf-8 -*-
"""真实案例全量转储：1983-11-03 12:00 男 广东中山

目的：不只跑一遍，而是把**每一层的实际输出**都倒出来，并明确指出
哪些层「没接上」——即在本链路里取不到、或取了但为空、或压根没有调用方。

用法：
  PYTHONPATH=src python tools/heluo/quzheng_20261008/dump_real_case.py
"""
import io
import json
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

BIRTH = (1983, 11, 3, 12)
GENDER = "male"
LOCATION = "中山"
# ⚠ 2026-10-08 实测：传 location 会让 calc_context 生效，紫微改走
#   ziwei_adapter → Node/iztro 硬路径，本机没装 iztro 时异常**逃逸**、
#   整条排盘链路挂掉；不传 location 则走 ziwei_engine 的 stub 兜底、正常。
#   这是「降级不对称」缺陷，故本转储先用不传 location 的可跑通路径，
#   location 相关问题单独记录（见 loc_vs_noloc.txt）。
USE_LOCATION = False
TZ = "Asia/Shanghai"
ANALYSIS = date(2026, 10, 8)
TARGET = date(2026, 8, 17)

out = []
gaps = []          # 没接上 / 为空 的层
warns = []         # 跑了但可疑


def sec(title):
    out.append("")
    out.append("=" * 96)
    out.append(title)
    out.append("=" * 96)


def dump(title, obj, depth=0, _seen=None):
    """递归打印 dataclass / dict / list。"""
    import dataclasses
    pad = "  " * depth
    if obj is None:
        out.append("%s(None)" % pad)
        return
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        out.append("%s%s" % (pad, type(obj).__name__))
        for f in dataclasses.fields(obj):
            dump("%s = " % f.name, getattr(obj, f.name), depth + 1)
        return
    if isinstance(obj, dict):
        out.append("%s{共 %d 键}" % (pad, len(obj)))
        for k, v in obj.items():
            dump("%s[%r]" % (pad, k), v, depth + 1)
        return
    if isinstance(obj, (list, tuple)):
        if len(obj) > 24:
            out.append("%s[%d 项，截断前 24]" % (pad, len(obj)))
            obj = obj[:24]
        out.append("%s[%d]" % (pad, len(obj)))
        for i, v in enumerate(obj):
            dump("%s%d." % (pad, i), v, depth + 1)
        return
    s = repr(obj)
    if len(s) > 300:
        s = s[:300] + "…"
    out.append("%s%s" % (pad, s))


# ══ 跑排盘 ══════════════════════════════════════════════════
from tongshu.pipeline import TONGSHUPipeline  # noqa: E402

sec("【0】排盘链路调用")
out.append("birth_date   = %s" % (BIRTH,))
out.append("gender       = %s" % GENDER)
out.append("location     = %s   timezone = %s   （实参启用：%s）"
           % (LOCATION, TZ, USE_LOCATION))
out.append("analysis_date= %s   河洛流年日 = %s" % (ANALYSIS, TARGET))

pipeline = TONGSHUPipeline.for_demo(ROOT)
try:
    R = pipeline.run(analysis_date=ANALYSIS, birth_date=BIRTH, gender=GENDER,
                     theme="WORK", compute_only=True,
                     heluo_target_date=TARGET, birth_minute=0,
                     **({'timezone': TZ, 'location': LOCATION}
                        if USE_LOCATION else {}))
except Exception:
    out.append(traceback.format_exc())
    gaps.append("排盘链路 run() 直接抛异常")
    R = None

if R is not None:
    out.append("PipelineResult 字段: %s"
               % sorted(k for k in R.__dataclass_fields__))
    for k in sorted(R.__dataclass_fields__):
        v = getattr(R, k, None)
        flag = "" if v not in (None, "", [], {}) else "   ← 空"
        out.append("  %-26s %-10s%s"
                   % (k, type(v).__name__,
                      flag if isinstance(v, (str, list, dict, tuple)) else ""))
        if isinstance(v, (str, list, dict, tuple)) and not v:
            gaps.append("PipelineResult.%s 为空" % k)

    H = R.heluo_result
    if H is None:
        gaps.append("heluo_result 为 None —— 河洛层整层没算出来")
    else:
        sec("【1】HeluoResult 全部字段（河洛主链）")
        dump("HeluoResult", H)

        # ── 各层完整性 ────────────────────────────────────
        sec("【2】逐层接线核对")
        checks = [
            ("input", H.input), ("numbers 天数地数", H.numbers),
            ("prenatal 先天卦", H.prenatal), ("yuantang 元堂", H.yuantang),
            ("postnatal 后天卦", H.postnatal), ("timeline 时间轴", H.timeline),
            ("structure 卦象结构", H.structure),
            ("hua_gong 化工", H.hua_gong), ("era 时代", H.era),
            ("seasonal_hexagram 节候卦", H.seasonal_hexagram),
            ("guajie 解卦", H.guajie),
        ]
        out.append("%-24s %-14s %s" % ("层", "状态", "摘要"))
        out.append("-" * 96)
        for name, v in checks:
            if v is None:
                state = "❌ None"
                gaps.append("%s 为 None —— 该层没接上" % name)
                summ = "—"
            elif hasattr(v, "__dataclass_fields__") or isinstance(v, dict):
                n = (len(v.__dataclass_fields__) if hasattr(v, "__dataclass_fields__")
                     else len(v))
                if isinstance(v, dict) and not v:
                    state = "⚠ 空 dict"
                    gaps.append("%s 为空 dict" % name)
                else:
                    state = "✅ 有"
                summ = "%d 字段/键" % n
            else:
                state = "✅ 有"
                summ = repr(v)[:56]
            out.append("%-24s %-14s %s" % (name, state, summ))

        # ── 下游消费者层 ──────────────────────────────────
        sec("【3】管线内建输出（接线后应直接可得，不必手工调）")
        out.append("  heluo_diagnosis = %s" % type(R.heluo_diagnosis).__name__)
        out.append("  heluo_guidance  = %s" % type(R.heluo_guidance).__name__)
        d = getattr(R, "heluo_diagnosis", None)
        if d is not None:
            out.append("  断言 %d 条" % len(d.assertions))
            out.append("  判决 %s" % (getattr(getattr(d.judgment, "domain", None),
                                          "value", None)))
            from heluo_engine.engines.heluo import diagnosis_rule_graph as _dg
            out.append("  丢弃 %s" % _dg.dropped_rules())
            out.append("  无信号可依 %s" % _dg.unmatched_evidence())
        g = getattr(R, "heluo_guidance", None)
        if g is not None:
            out.append("  建议 %d 条：%s" % (len(g.action_items),
                                        [i.title for i in g.action_items]))

        sec("【3b】下游消费者层（逐个独立调用，看谁没接上）")

        def try_layer(label, fn):
            out.append("")
            out.append("── %s" % label)
            try:
                r = fn()
            except Exception as exc:
                out.append("   ❌ 抛异常 %s: %s" % (type(exc).__name__, exc))
                out.append("      " + traceback.format_exc().splitlines()[-3][:90])
                gaps.append("%s 调用失败：%s" % (label, exc))
                return None
            if r is None:
                out.append("   ⚠ 返回 None（该层在本盘上取不到）")
                gaps.append("%s 返回 None" % label)
                return None
            try:
                dump("结果", r)
            except Exception as exc:
                out.append("   (转储失败 %s)" % exc)
            return r

        try:
            from heluo_engine.engines.heluo.evidence_producer import HeLuoEvidenceProducer
            try_layer("HeLuoEvidenceProducer 证据产出",
                      lambda: HeLuoEvidenceProducer().produce(H))
        except Exception as exc:
            gaps.append("evidence_producer 不可导入：%s" % exc)

        try:
            from heluo_engine.engines.heluo.frozen_state import build_frozen_state
            fs = try_layer("build_frozen_state 冻结态",
                           lambda: build_frozen_state(H))
        except Exception as exc:
            gaps.append("frozen_state 不可导入：%s" % exc)
            fs = None

        DG = None
        try:
            from heluo_engine.engines.heluo import diagnosis_rule_graph as dgmod
            DG = dgmod
            try_layer("diagnosis_rule_graph 未注册规则",
                      lambda: dgmod.dropped_rules())
            evs = []
            try:
                from heluo_engine.engines.heluo.evidence_producer import (
                    HeLuoEvidenceProducer)
                evs = HeLuoEvidenceProducer().produce(H)
            except Exception:
                evs = []
            # canonical_signals 是 dict[str, list]，需摊平成 list 才能喂
            # build_diagnosis_graph(evidences, signals)（后者按 list 逐项 .get）。
            cs = getattr(R, "canonical_signals", None) or {}
            sigs = ([x for v in cs.values() for x in v]
                    if isinstance(cs, dict) else list(cs))
            def _diag():
                g = dgmod.build_diagnosis_graph(evidences=list(evs),
                                               signals=sigs,
                                               frozen_state=fs,
                                               subject="dump")
                out.append("   断言 %d 条 / 丢弃 %s / 无信号可依 %s"
                           % (len(g.assertions), dgmod.dropped_rules(),
                              dgmod.unmatched_evidence()))
                for a in g.assertions:
                    out.append("     · %-26s %-10s %s"
                               % (a.source_rule, a.direction.value,
                                  a.semantic))
                j = g.judgment
                out.append("   判决: %s" % ("None" if j is None else
                    "domain=%s | semantic=%s | authorized_by=%s | 支撑断言 %s 条"
                    % (getattr(j.domain, "value", j.domain), j.semantic,
                       j.authorized_by, len(j.supporting_assertions or []))))
                return g
            try_layer("build_diagnosis_graph 诊断图/断言", _diag)
        except Exception as exc:
            gaps.append("diagnosis_rule_graph 不可用：%s" % exc)

        try:
            from heluo_engine.engines.heluo.guidance import HeluoGuidanceEngine
            from heluo_engine.engines.heluo.evidence_producer import (
                HeLuoEvidenceProducer)
            from heluo_engine.engines.heluo.diagnosis_rule_graph import (
                build_diagnosis_graph)

            def _g():
                evs = HeLuoEvidenceProducer().produce(H)
                cs = getattr(R, "canonical_signals", None) or {}
                sigs = ([x for v in cs.values() for x in v]
                        if isinstance(cs, dict) else list(cs))
                graph = build_diagnosis_graph(evidences=list(evs),
                                              signals=sigs,
                                              frozen_state=fs,
                                              subject="dump")
                assertions = getattr(graph, "assertions", None) or []
                judgment = getattr(graph, "judgment", None)
                out.append("   (诊断图: 断言 %d 条, 判决 domain=%s, 支撑 %s)"
                           % (len(assertions),
                              getattr(getattr(judgment, "domain", None),
                                      "value", "None"),
                              judgment is not None))
                return HeluoGuidanceEngine().generate(
                    assertions=list(assertions),
                    judgment=judgment,
                    source_gua=H.prenatal.hexagram_name,
                    target_gua=H.postnatal.hexagram_name,
                    yuan_tang=getattr(H.yuantang, "yao_name", "") or "",
                    hua_gong_state=(H.hua_gong.state.value
                                    if H.hua_gong else None),
                    subject="dump")
            try_layer("HeluoGuidanceEngine 行动建议", _g)
        except Exception as exc:
            gaps.append("guidance 不可用：%s" % exc)

        try:
            from heluo_engine.engines.heluo.interpretation import (
                RelationalInterpretationEngine)
            try_layer("interpretation 关系解释",
                      lambda: RelationalInterpretationEngine(
                          H.input).compute())
        except Exception as exc:
            warns.append("interpretation 在本盘不可用：%s" % exc)

# ══ 缺口汇总 ════════════════════════════════════════════════
sec("【4】接线缺口汇总")
if gaps:
    out.append("以下层「没接上 / 为空」，需处理：")
    for g in gaps:
        out.append("  · " + g)
else:
    out.append("（无）")
if warns:
    out.append("")
    out.append("以下层可运行但结果需留意：")
    for w in warns:
        out.append("  · " + w)

io.open(ROOT / "tools" / "heluo" / "quzheng_20261008" / "real_case_dump.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))