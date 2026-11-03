# TEST BASELINE · STEP 0.3 真实测试事实基线

> **日期**: 2026-08-23 · **执行**: Hermes（STEP 0 修正版作业）
> **纪律**: 失败即事实。零修复、零 mock、零跳过删除。

---

## 运行环境记录

```text
COMMAND     = PYTHONPATH=src python -m pytest tests/ -q --tb=short
WORKDIR     = D:/today/backend
GIT_COMMIT  = 052aebb981a18e668ab90fdc1ca65ae6ed88abce (audit-baseline-20260823)
PYTHON      = 3.11.15 (session venv)
LOG         = docs/audit/step0_baseline/pytest-baseline.log
```

## 9 字段事实

| 字段 | 值 |
|---|---|
| COLLECTED | 1284 |
| TOTAL | 1284 |
| **PASSED** | **1283** |
| FAILED | **0** |
| ERROR | **0** |
| SKIPPED | 1 |
| XFAILED | 0 |
| XPASSED | 0 |
| DURATION | 17.40s |

## 结论

```text
BASELINE_TEST_STATUS = FACT
失败列表             = 无（FAILED=0, ERROR=0）
首个 traceback       = N/A
```

## 三方数字矛盾裁决输入

| 来源 | 声称 | 实测裁决 |
|---|---|---|
| BUG_TRACKING.md / BUG06A_FINAL.md | "1283 passed, 1 skipped" | ✅ **与本步实测完全一致** |
| AUDIT_2026-08-23.md | "32 failed, 1147 passed" | ❌ 与实测不符——该审计的运行条件（环境/依赖/时点）与当前基线不同，其结论应标注为**特定时点/特定环境下的历史观测**，不得作为当前基线 |
| TEST_REPORT.md（已删） | "683 全部通过" | 已被 Phase 0 BUG-12 裁定失实并删除，维持原裁定 |

**关键推断**：AUDIT_0823 报告中 P0 缺陷（BUG-01 易经透传断裂 / BUG-02~04 五行词表混用）的**代码层证据仍需 STEP 1 Claude 逐一复核**——测试全绿不等于缺陷不存在（可能正是"测试被适配"的残留特征），但也不等于存在。以代码 diff 实证为准，不以任何一份报告为准。

## 零修改确认

✅ 未修代码　✅ 未修测试　✅ 未改 Golden/fixture　✅ 未临时 mock　✅ 未删失败测试
仅设置 PYTHONPATH=src（修正案明确允许的唯一运行条件）。

**GATE 进度: 5/8**
├── 0.1 Git state captured        PASS
├── 0.1 Dirty files accounted     PASS
├── 0.2 DB actual snapshot        PASS
├── 0.2 Historical provenance     PASS
├── 0.3 pytest reality captured   PASS
├── 0.4 baseline hash recorded    HOLD
├── 0.5 freeze declaration        HOLD
└── 0.6 no production mutation    PASS（累计确认）
