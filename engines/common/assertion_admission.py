# -*- coding: utf-8 -*-
"""PATCH-103 Assertion Admission
状态机 DRAFT→CANDIDATE→ADMITTED→ACTIVE
门槛: 原文/可解释/绑Evidence/不越权产State
"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

VALID = ["DRAFT", "CANDIDATE", "ADMITTED", "ACTIVE"]


def admit_assertion(a):
    """按门槛升级"""
    # 门槛检查
    checks = {
        "has_classic_source": bool(a.get("classic_source")),
        "has_evidence": bool(a.get("evidence_id")),
        "has_namespace": bool(a.get("namespace")),
        "no_state_write": a.get("guard") == "不反写State",
        "has_assertion_text": bool(a.get("assertion_text"))
    }
    passed = all(checks.values())
    if not passed:
        return {"assertion_id": a.get("assertion_id"), "status": "REJECTED",
                "failed": [k for k, v in checks.items() if not v]}
    # 升级: CANDIDATE→ADMITTED需人工golden, 这里框架
    cur = a.get("status", "DRAFT")
    if cur == "CANDIDATE":
        new = "ADMITTED"
    else:
        new = cur
    return {"assertion_id": a["assertion_id"], "status": new, "checks": checks}


if __name__ == '__main__':
    good = {"assertion_id": "ASSERT-001", "classic_source": "PZZQ", "evidence_id": "PZZQ-007-004",
            "namespace": "PZZQ.pattern", "guard": "不反写State",
            "assertion_text": "财格佩印格成", "status": "CANDIDATE"}
    bad = {"assertion_id": "ASSERT-002", "classic_source": "", "evidence_id": "",
           "namespace": "", "guard": "", "assertion_text": "", "status": "DRAFT"}
    print("=== 103 Assertion Admission ===")
    print("合格:", admit_assertion(good)["status"])
    print("不合格:", admit_assertion(bad)["status"], "失败项:", admit_assertion(bad).get("failed"))
