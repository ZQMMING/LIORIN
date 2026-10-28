# YHZP Evidence Registry（Phase 5 · V2.22 §39/§64）

**日期**：2026-09-15 · 分支 feature/ziping · engine=YUHAI_ZIPING

## 状态：Phase 5 PASS（测试 6/6，全量 57/57）

## 交付物

```
engines/yuhai_ziping/evidence/
├── __init__.py
├── evidence_registry.py   从正式 Source/Rule Registry 派生 Evidence + Gap Report
└── tests/test_evidence_registry.py   6 tests

registries/evidence/
├── evidence.yhzp.jsonl     66 条 Evidence Record（§39）
└── gap_report.yhzp.jsonl   4 条 UNVERIFIED_SOURCE（非断链，待 Human 裁定）
```

## 设计要点

- **Evidence 结构**（§39）：evidence_id / source_id / source_location / text_layer / evidence_grade / rule_ids / fact_ids
- **链完整性**（§64）：每条 Rule → Source → Evidence 必须可走通；链断 → BROKEN_CHAIN → FAIL_CLOSED，不强行通过
- **同源复用**：同一 Source 被多 Rule 引用时复用同一条 Evidence（同一文本证据）
- **运行时**：Rule Engine 产出的 fact 经 `attach()` 补 evidence_ids（Fact→Evidence 边）
- **Gap Report**：UNVERIFIED（grade=D）不视为断链，但列入报告待 Human 裁定（4 条，对应已登记存疑）

## 验收

- 340 条 Rule 全部有证据链，0 断链 ✅
- 66 条 Evidence，id 唯一、结构符合 §39 ✅
- Fact attach 后带 evidence_ids，且与 rule 的 source_ids 对应 ✅
- 全量 57 tests + 5 Validators PASS ✅

## 说明

- 66/592 sources 被规则引用（其余为描述性/不可形式化文本，已在 unformalizable 台账）
- evidence_requirement 字段已随 Rule 保留，本阶段完成其 Registry 化
