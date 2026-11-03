# -*- coding: utf-8 -*-
"""PATCH-020 Engine Validation Layer（引擎验证层）

职责（严格不越权）：
- 020-01 验证管线框架：加载 patch_017/018/019 + 各域 Rule Candidate Registry，执行三层验证
- 020-02 静态验证（STATIC_VALIDATION）：60 条规则全量——source 可回查 / output 非空 / condition 非空 / 禁转换已声明 / 字段齐备
- 020-03 首批 Golden 验证（GOLDEN_BLOCK）：5 条全局必测反例的「规则元数据级拦截测试」——确认不存在允许禁转换（旺→STRONG 等）的规则；Conflict Resolver 单测
- 本层不实现任何命理计算（不产出生辰→状态的推导），只验证规则库/契约的正确性；真正八字输入计算属 Engine Execution（未启动）

产出：governance/patch_020_engine_validation_report.json
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"D:\shuntian-ziping-p0"

BOOK_FILE = {
    "YHZP": "yhzp", "PZZQ": "pzzq", "DTS": "dts",
    "QTBJ": "qtbj", "SMTH": "smth", "SFTK": "sftk",
}

# 5 条全局必测反例（PATCH-017）
GLOBAL_BLOCK = [
    {"title": "旺≠强", "forbidden": ["wang_state→STRONG", "旺→强"]},
    {"title": "得令≠强", "forbidden": ["GET_ORDER→STRONG", "order_state→STRONG", "得令→强"]},
    {"title": "有根≠强", "forbidden": ["root_state→STRONG", "有根→强", "has_root→STRONG"]},
    {"title": "调候≠旺衰", "forbidden": ["seasonal_state→STRONG", "seasonal→STRONG"]},
    {"title": "病药≠用神", "forbidden": ["病药→直接取用神"]},
]


def load_source_ids() -> set:
    ids = set()
    for book, f in BOOK_FILE.items():
        p = os.path.join(ROOT, "registries", "source", f"sources.{f}.jsonl")
        with io.open(p, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    ids.add(json.loads(line)["source_id"])
    return ids


def collect_candidates() -> list:
    """收集 60 条 Rule Candidate（与 patch_017/019 同源）。"""
    files = []
    files.append((os.path.join(ROOT, "governance", "patch_005a_concept_boundary_registry.json"), "candidates", "rule_candidate_id"))
    files.append((os.path.join(ROOT, "governance", "patch_005c_strength_state_rule.json"), "1_rule_predicate_layer.candidate_predicates", "rule_id"))
    for n in range(6, 17):
        for p in glob.glob(os.path.join(ROOT, "governance", f"patch_{n:03d}_*_rule_modeling.json")):
            files.append((p, "rule_candidates", "rule_id"))
    files.append((os.path.join(ROOT, "governance", "patch_012_ganzhi_liuqin_boundary.json"), "A+B", "rule_id"))

    def get_path(d, path):
        cur = d
        for k in path.split("."):
            cur = cur[k]
        return cur

    out = []
    for path, key, idfield in files:
        d = json.load(io.open(path, encoding="utf-8"))
        if key == "A+B":
            cands = d["section_A_ganzhi"]["rule_candidates"] + d["section_B_liu_qin"]["rule_candidates"]
        else:
            cands = get_path(d, key)
        for c in cands:
            excl = c.get("excluded_transition") or c.get("excluded") or []
            if isinstance(excl, str):
                excl = [excl]
            out.append({
                "rule_id": c.get(idfield) or c.get("rule_id"),
                "source_ids": c.get("source_ids") or [],
                "output": c.get("output") or c.get("output_type") or c.get("output_state") or "",
                "condition": c.get("condition") or c.get("concept_definition") or c.get("original_text") or "",
                "excluded": excl,
                "classical_scope": c.get("classical_scope", ""),
                "input": c.get("input_factor") or c.get("input_states") or [],
            })
    return out


def static_validate(cands: list, source_ids: set) -> list:
    """020-02 静态验证：source 可回查 / output 非空 / condition 非空 / 禁转换已声明 / 字段齐备。"""
    report = []
    for c in cands:
        checks = {
            "source_traceable": bool(c["source_ids"]) and all(s in source_ids for s in c["source_ids"]),
            "output_nonempty": bool(c["output"]),
            "condition_nonempty": bool(c["condition"]),
            "excluded_declared": len(c["excluded"]) > 0,
            "scope_nonempty": bool(c["classical_scope"]),
            "rule_id_nonempty": bool(c["rule_id"]),
        }
        # 设计豁免：弱概念（CAND-RUO-001）——005A Human 裁决「弱 PENDING，六部无单源等价」，无单锚是设计而非缺陷
        exempt = c["rule_id"] == "CAND-RUO-001" and not c["source_ids"]
        if exempt:
            report.append({
                "rule_id": c["rule_id"],
                "checks": checks,
                "result": "DESIGN_EXEMPT",
                "reason": "005A Human 裁决：弱=PENDING，六部无单源等价；无单锚为设计豁免",
            })
            continue
        report.append({
            "rule_id": c["rule_id"],
            "checks": checks,
            "result": "STATIC_PASS" if all(checks.values()) else "STATIC_FAIL",
        })
    return report


def golden_block_test(cands: list) -> list:
    """020-03 首批 Golden 验证：5 全局反例拦截测试。
    规则元数据级：扫描全部规则，确认没有任何规则的 output 命中禁转换 target 且 input 涉及禁转换 source。"""
    results = []
    for block in GLOBAL_BLOCK:
        violations = []
        for c in cands:
            out = c["output"].upper()
            inp = " ".join(str(x) for x in (c["input"] if isinstance(c["input"], list) else [c["input"]])) + " " + c["condition"]
            for fb in block["forbidden"]:
                src, _, tgt = fb.partition("→")
                # 命中判定：output 含 target，且 input/condition/scope 含 source 相关词
                src_hit = any(k in inp.upper() or k in c["classical_scope"].upper() for k in src.upper().split("_"))
                if tgt.upper() in out and src_hit:
                    # 但若该规则自身 excluded 已声明此禁转换，则不算违规（自洽）
                    if not any(fb.split("→")[0].upper() in e.upper().replace("→", "") for e in c["excluded"]):
                        violations.append(c["rule_id"])
        results.append({
            "title": block["title"],
            "forbidden": block["forbidden"],
            "violations": violations,
            "result": "BLOCKED" if not violations else "VIOLATION",
        })
    return results


def conflict_test() -> dict:
    """020-03 Conflict Resolver 单测：8 类冲突 resolution 类型合法。"""
    p = os.path.join(ROOT, "governance", "patch_018_conflict_resolver.json")
    d = json.load(io.open(p, encoding="utf-8"))
    valid = {"CONFLICT_RESOLVED_BY_SCOPE", "CONFLICT_RESOLVED_BY_CONDITION", "UNRESOLVED"}
    rc = d["resolved_conflicts"] + d["unresolved_pending"]
    bad = [c["conflict_id"] for c in rc if c["resolution"] not in valid]
    return {"total": len(rc), "invalid_resolution": bad, "result": "PASS" if not bad else "FAIL"}


def main() -> None:
    source_ids = load_source_ids()
    cands = collect_candidates()
    static = static_validate(cands, source_ids)
    golden = golden_block_test(cands)
    conflict = conflict_test()

    report = {
        "contract_id": "PATCH-020",
        "name": "Engine Validation Layer（引擎验证层）",
        "status": "FROZEN_DRAFT",
        "summary": {
            "rules_total": len(cands),
            "static_pass": sum(1 for r in static if r["result"] == "STATIC_PASS" or r["result"] == "DESIGN_EXEMPT"),
            "static_fail": sum(1 for r in static if r["result"] == "STATIC_FAIL"),
            "golden_block_pass": sum(1 for g in golden if g["result"] == "BLOCKED"),
            "golden_block_total": len(golden),
            "conflict_resolver": conflict["result"],
        },
        "020_01_pipeline": ["加载 60 条 Rule Candidate", "静态验证（STATIC_VALIDATION）", "Golden 拦截测试（GOLDEN_BLOCK）", "Conflict Resolver 单测"],
        "020_02_static_validation": static,
        "020_03_golden_block": golden,
        "020_03_conflict_test": conflict,
        "note": "本层不实现命理计算；ADMITTED 状态不变更（引擎执行层未启动，golden_pass 仍为 false）",
    }
    out_path = os.path.join(ROOT, "governance", "patch_020_engine_validation_report.json")
    json.dump(report, io.open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("PATCH-020 Engine Validation Report 生成")
    print("  规则总数:", report["summary"]["rules_total"])
    print("  静态验证 PASS:", report["summary"]["static_pass"], "/ FAIL:", report["summary"]["static_fail"])
    print("  Golden 拦截 PASS:", report["summary"]["golden_block_pass"], "/", report["summary"]["golden_block_total"])
    print("  Conflict Resolver:", report["summary"]["conflict_resolver"])
    for g in golden:
        print("   -", g["title"], g["result"], g["violations"])


if __name__ == "__main__":
    main()
