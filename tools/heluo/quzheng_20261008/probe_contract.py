# -*- coding: utf-8 -*-
"""探清 build_diagnosis_graph 期望的 signals 契约 vs 管线实际产出。"""
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
from tongshu.engines.heluo.evidence_producer import HeLuoEvidenceProducer  # noqa: E402
from tongshu.engines.heluo.diagnosis_rule_graph import (  # noqa: E402
    HELUO_RULES, RULE_DOMAIN_MAP)

out = []
p = TONGSHUPipeline.for_demo(ROOT)
r = p.run(analysis_date=date(2026, 10, 8), birth_date=(1983, 11, 3, 12),
          gender="male", theme="WORK", compute_only=True,
          heluo_target_date=date(2026, 8, 17))

cs = r.canonical_signals or {}
sigs = [x for v in cs.values() for x in v] if isinstance(cs, dict) else list(cs)
out.append("canonical_signals 摊平后: %d 条" % len(sigs))
if sigs:
    out.append("元素类型: %s.%s"
               % (type(sigs[0]).__module__, type(sigs[0]).__name__))
    import dataclasses
    if dataclasses.is_dataclass(sigs[0]):
        out.append("其字段: %s"
                   % [f.name for f in dataclasses.fields(sigs[0])])
for s in sigs:
    out.append("")
    for name in ("signal_id", "source_engine", "event_type", "event_types",
                 "domain", "ontology_type", "direction", "strength",
                 "temporal_scope", "rule_refs", "rule_id", "evidence_refs",
                 "layer", "extracted_at", "confidence"):
        if hasattr(s, name):
            v = getattr(s, name)
            extra = ""
            if name == "direction":
                extra = "  (type=%s, .value=%r)" % (type(v).__name__,
                                                    getattr(v, "value", None))
            out.append("  %-15s = %r%s" % (name, v, extra))
    out.append("  有 rule_id 属性? %s" % hasattr(s, "rule_id"))

out.append("")
out.append("=== 河洛证据的 rule_id 与注册表 ===")
evs = HeLuoEvidenceProducer().produce(r.heluo_result)
for ev in evs:
    node = HELUO_RULES.get(ev.rule_id)
    out.append("  %-26s value=%-8r 注册=%s 授权=%s"
               % (ev.rule_id, ev.value, node is not None,
                  getattr(node, "is_authorized", None)))
    out.append("      prefix(前4)=%r" % ev.rule_id[:4])

out.append("")
out.append("=== _signal_direction_for_evidence 的匹配逻辑能否对上 ===")
out.append("  取 ev.rule_id[:4] 作为 prefix，与 sig 的 rule_id 做前缀/包含匹配。")
out.append("  但 CanonicalSignal 只有 signal_id 与 rule_refs（列表），无 rule_id。")
allrefs = sorted({x for s in sigs for x in (s.rule_refs or [])})
out.append("  本盘所有 rule_refs 汇总: %s" % (allrefs if allrefs else "（空）"))

io.open(ROOT / "tools" / "heluo" / "quzheng_20261008" / "signal_contract.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))