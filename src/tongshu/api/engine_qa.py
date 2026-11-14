"""本机 QA 结果投影：保留引擎来源与可核对字段，避免向浏览器传 100 年全量时间轴。"""
from __future__ import annotations

from typing import Any


def summarize_result(result: Any, analysis_date) -> dict:
    canon = result.canonical
    claims = list(getattr(canon, "atomic_claims", None) or [])
    heluo = getattr(result, "heluo_result", None)
    yi = getattr(result, "yi_structure", None)
    chart = getattr(result, "bazi_chart", None)
    pillars_fn = getattr(chart, "get_pillars_chinese", None)
    pillars = pillars_fn() if callable(pillars_fn) else None
    canon_dict = canon.to_dict() if hasattr(canon, "to_dict") else {}
    meta = canon_dict.get("meta") or {}
    cross = canon_dict.get("cross_analysis") or {}
    by_engine = cross.get("by_engine") or {}
    return {
        "analysis_date": analysis_date.isoformat(),
        "canonical_id": canon.canonical_id,
        "trace_id": meta.get("trace_id") or (getattr(canon, "meta_observability", None) or {}).get("trace_id"),
        "source": result.source,
        "validation_passed": bool(getattr(result, "validation_passed", False)),
        # This summary is produced only by the compute_only QA route. The
        # pipeline deliberately skips rendering and its validation in that mode.
        "validation_status": "not_run",
        "bazi_pillars": pillars,
        "observed_evidence_by_engine": {
            key: len((value or {}).get("evidence_ids") or [])
            for key, value in by_engine.items() if isinstance(value, dict)
        },
        "result_available": {
            "heluo": heluo is not None,
            "yijing_structure": yi is not None,
        },
        "ziping_claim_count": sum(1 for c in claims if (c.get("claim_id", "") if isinstance(c, dict) else "").startswith("AC-ZP-")),
        "heluo": {
            "prenatal": getattr(getattr(heluo, "prenatal", None), "hexagram_name", None),
            "postnatal": getattr(getattr(heluo, "postnatal", None), "hexagram_name", None),
        } if heluo is not None else None,
        "claims": [
            {"claim_id": c.get("claim_id"), "domain": c.get("domain"),
             "conclusion": c.get("conclusion"), "claim": str(c.get("claim", ""))[:360],
             "evidence_refs": c.get("evidence_refs", [])[:12]}
            for c in claims if isinstance(c, dict)
        ][:50],
        "claim_count": len(claims),
        "warning": "TEST ONLY：仅供人工排查引擎问题，不代表算法已验收或预测有效。",
    }
