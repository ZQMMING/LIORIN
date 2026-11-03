# GOLDEN RECHECK · STEP 6 中期基线

> **日期**: 2026-08-23 · **目的**: 确认 GOLDEN_BASELINE.md (STEP 0/GF1) 的真实数字在治理 commit 后不变。

## 运行条件

- **命令**: `PYTHONPATH=src TONGSHU_ALLOW_ZIWEI_STUB=1 python -m tongshu.golden`
- **.env**: 被屏蔽（`TONGSHU_ENV_FILE` 指向不存在路径，API key 环境变量清除）→ 强制 StubLLMClient
- **Renderer**: StubLLMClient（deterministic）
- **ZiweiEngine**: stub fallback（iztro 不可用，`TONGSHU_ALLOW_ZIWEI_STUB=1`）
- **Commit**: 8f3b081 (baseline-v1.4-interim-20260823)

## 真实数字

| 指标 | GOLDEN_BASELINE (STEP 0) | STEP 6 重跑 | 一致 |
|------|--------------------------|-------------|------|
| LOADED_CASES | 20 | **20** | YES |
| PASSED | 7 | **7** | YES |
| FAILED | 13 | **13** | YES |
| 通过率 | 35% | **35%** | YES |

## 通过案例（7）— 与基线完全一致

GOLDEN-001, GOLDEN-005, GOLDEN-006, GOLDEN-007, GOLDEN-008, GOLDEN-009, GOLDEN-020

## 失败清单（13）— 逐条与基线比对

| Case | 基线失败项 | 重跑失败项 | 一致 |
|------|-----------|-----------|------|
| GOLDEN-002 | ontology_type ACTION→REFLECTION | 同 | YES |
| GOLDEN-003 | cross PARTIAL→INSUFFICIENT + 3 others | 同 | YES |
| GOLDEN-004 | cross ALIGNED→INSUFFICIENT + 3 others | 同 | YES |
| GOLDEN-010 | bazi_signal_refs + ontology_type | 同 | YES |
| GOLDEN-011 | cross PARTIAL→ALIGNED + 3 others | 同 | YES |
| GOLDEN-012 | cross PARTIAL→ALIGNED + 3 others | 同 | YES |
| GOLDEN-013 | cross PARTIAL→INSUFFICIENT + 3 others | 同 | YES |
| GOLDEN-014 | ontology_type CONSTRAINT→REFLECTION | 同 | YES |
| GOLDEN-015 | cross INSUFFICIENT→ALIGNED + 3 others | 同 | YES |
| GOLDEN-016 | cross ALIGNED→INSUFFICIENT + 3 others | 同 | YES |
| GOLDEN-017 | cross ALIGNED→INSUFFICIENT + 3 others | 同 | YES |
| GOLDEN-018 | cross INSUFFICIENT→ALIGNED + 3 others | 同 | YES |
| GOLDEN-019 | cross INSUFFICIENT→ALIGNED + 3 others | 同 | YES |

## 结论

**Golden 数字在 STEP 0 → STEP 6 期间完全不变：LOADED 20 / PASSED 7 / FAILED 13。**
所有失败项的 expected/actual 与 GOLDEN_BASELINE.md 逐字一致。
治理资产 commit 及 P0 代码修复未改变 golden 行为。

完整运行日志: `golden-interim.log`
