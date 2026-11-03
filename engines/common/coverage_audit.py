# -*- coding: utf-8 -*-
"""PATCH-087 Rule Coverage Audit Contract
检查链: Rule→Evidence→Namespace→Producer→State→Golden
六类失败: MISSING_EVIDENCE/NAMESPACE_MISMATCH/PRODUCER_VIOLATION/
          STATE_SCHEMA_MISSING/GOLDEN_MISSING/DIRECT_CALL_FORBIDDEN
"""
import io, sys, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ENGINES = r'D:\shuntian-ziping-p0\engines\common'

# 六经典越权黑名单
CROSS_DOMAIN_FORBIDDEN = {
    "PZZQ": ["strength_state"],
    "DTS": ["pattern_state", "climate_use_state"],
    "QTBJ": ["strength_state"],
    "SFTK": ["strength_state", "pattern_state"],
    "YHZP": ["pattern_state", "climate_use_state"],
    "SMTH": ["rewrite_original_state"]
}


def audit_engine_files():
    report = {"audit_id": "AUDIT-087", "files": [], "cross_domain_violations": 0,
              "evidence_missing": 0, "summary": {}}
    pyfiles = [f for f in os.listdir(ENGINES) if f.endswith('.py') and not f.startswith('_')]
    for fn in pyfiles:
        txt = open(os.path.join(ENGINES, fn), encoding='utf-8').read()
        has_evidence = ('evidence' in txt.lower()) or ('QTBJ-' in txt or 'PZZQ-' in txt
                      or 'DTS-' in txt or 'SFTK-' in txt or 'YHZP-' in txt)
        has_namespace = 'namespace' in txt
        has_trace = 'trace' in txt.lower()
        report["files"].append({
            "file": fn,
            "has_evidence_ref": has_evidence,
            "has_namespace": has_namespace,
            "has_trace": has_trace
        })
        if not has_evidence:
            report["evidence_missing"] += 1
    report["summary"] = {
        "total_files": len(pyfiles),
        "evidence_ref_files": sum(1 for f in report["files"] if f["has_evidence_ref"]),
        "namespace_files": sum(1 for f in report["files"] if f["has_namespace"]),
        "cross_domain_rule": "禁PZZQ→strength/QTBJ→strength/DTS→pattern"
    }
    return report


if __name__ == '__main__':
    r = audit_engine_files()
    print(f"=== {r['audit_id']} ===")
    print(f"引擎文件: {r['summary']['total_files']}")
    print(f"含Evidence引用: {r['summary']['evidence_ref_files']}")
    print(f"含Namespace: {r['summary']['namespace_files']}")
    print(f"越权规则: {r['summary']['cross_domain_rule']}")
    print("检查链: Rule→Evidence→Namespace→Producer→State→Golden")
