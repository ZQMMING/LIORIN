# YHZP Golden / Regression（Phase 8 · V2.22 §67/§91）

**日期**：2026-09-15 · 分支 feature/ziping · engine=YUHAI_ZIPING

## 状态：Phase 8 PASS（引擎 53/53，全量 76/76）

## 交付物

```
engines/yuhai_ziping/golden/
├── __init__.py
├── golden_runner.py       run/compare/report（§67 Agent 权限边界）
└── tests/test_golden_regression.py   6 tests

engines/yuhai_ziping/regression/
├── __init__.py
└── regression_harness.py  基线快照 + diff 回归报告
```

## 关键约束执行

- **TG-001~012 全部 DEFINED/NOT_APPROVED** → GoldenRunner.report 阻塞，Agent 不代行审批（§67/§91）
- **Agent 仅 run/compare/report**；CREATE/APPROVE/FREEZE 仅 Human Architect
- **Business Golden Registry 为空** → 无可运行业务 golden（Human 填充后运行）
- 模拟批准测试验证：TG-001（Canonical Gate）与 TG-006（Forbidden Scan）批准后即跑 PASS

## Regression

- 基线快照：样例命盘 → 六组 facts 规范化快照（稳定排序，去运行噪声键）
- 回归对比：diff → added/removed/组统计 → pass/fail
- 确定性验证：同输入两次运行快照一致；篡改 fact → 回归报差异 ✅

## 下一步

Phase 9（§68 Cross-Domain）+ Phase 10（§69 Production Admission）：YHZP 作为 L2A 只提供 Public Contract 不消费上层；生产准入需 Golden 审批（Human）+ Provenance 生成。
