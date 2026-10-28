# -*- coding: utf-8 -*-
"""Provenance Contract v1 schema 校验（只校验契约结构，不跑 Rule 判定）。"""
import sys, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 收集现有 evidence_id
EXISTING_EVIDENCE_IDS = set()
for p in (ROOT / "registries" / "evidence").glob("*.jsonl"):
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            EXISTING_EVIDENCE_IDS.add(json.loads(line)["evidence_id"])
        except (json.JSONDecodeError, KeyError):
            continue

CONDITION_ID_RE = re.compile(r"^ZP-RULE-[A-Z]+(-[A-Z]+)?-[A-Z][A-Z_0-9]*$")
AUTHORIZATIONS = {"required", "blocked", "premise", "supported", "unknown_pending"}


def validate_condition(cond):
    errs = []
    cid = cond.get("condition_id", "")
    if not CONDITION_ID_RE.match(cid):
        errs.append(f"condition_id 格式非法: {cid}")
    if not cond.get("condition_name"):
        errs.append(f"{cid}: 缺 condition_name")
    refs = cond.get("evidence_refs", [])
    if not isinstance(refs, list):
        errs.append(f"{cid}: evidence_refs 必须是数组")
    else:
        for r in refs:
            if r not in EXISTING_EVIDENCE_IDS:
                errs.append(f"{cid}: evidence_refs 引用不存在: {r}")
    auth = cond.get("authorization", "")
    if auth not in AUTHORIZATIONS:
        errs.append(f"{cid}: authorization 非法: {auth}")
    return errs


def validate_rule(rule):
    errs = []
    if not rule.get("rule_id"):
        errs.append("缺 rule_id")
    cids = [c.get("condition_id") for c in rule.get("conditions", [])]
    if len(cids) != len(set(cids)):
        errs.append("condition_id 在 Rule 内不唯一")
    for c in rule.get("conditions", []):
        errs.extend(validate_condition(c))
    return errs


if __name__ == "__main__":
    # 自校验：一个合法样例 + 一个非法样例
    good = {
        "rule_id": "ZP-RULE-CAI",
        "conditions": [
            {
                "condition_id": "ZP-RULE-CAI-ROOT",
                "condition_name": "财有根",
                "evidence_refs": [],
                "authorization": "required",
            }
        ],
    }
    bad = {
        "rule_id": "X",
        "conditions": [
            {
                "condition_id": "bad_id",
                "condition_name": "",
                "evidence_refs": ["NOT-EXIST"],
                "authorization": "xxx",
            }
        ],
    }
    e1 = validate_rule(good)
    e2 = validate_rule(bad)
    print("合法样例错误:", e1)
    print("非法样例错误:", e2)
    print("现有 evidence_id 数:", len(EXISTING_EVIDENCE_IDS))
    assert e1 == [], "合法样例不应报错"
    assert len(e2) >= 3, "非法样例应报错"
    print("SCHEMA VALIDATION PASS")
