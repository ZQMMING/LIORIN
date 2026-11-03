# P1.4 Cross-System Semantics Audit

**Date**: 2026-09-01
**Status**: ✅ APPROVED — Implemented

---

## 审计结论

### R1：Production Signal 形态

`reasoning/signal_engine.py` 的 `Signal` 仍然在生产 pipeline 中使用，携带 `direction`。
P1.4 不重构此模块（属于 P1.2 Signal Migration 范围）。

**裁决**：保持现状，不修改。

### R2：CrossAnalyzer CONFLICTED 移除

**问题**：`cross_analysis.py` 是旧版跨系统比较器，产生 `ALIGNED/PARTIAL/INSUFFICIENT` 状态。
`template_fallback.py` 中仍有 `CONFLICTED` 模板（虽 `CrossAnalyzer` 当前不产出，但是死代码）。

**修复**：
1. `cross_analysis.py` — 添加 P1.4 DEPRECATED 头部声明
2. `convergence.py` — 更新 deprecation 注释，明确指向 `CrossDomainOrchestrator`
3. `template_fallback.py` — 移除所有 6 条 `CONFLICTED` 模板

**修复后**：
```
CrossAnalyzer 状态空间: ALIGNED / PARTIAL / INSUFFICIENT（无 CONFLICTED）
template_fallback 模板: (theme, ALIGNED/PARTIAL/INSUFFICIENT) — 无 CONFLICTED
```

### R3：spec/canonical_signal.py vs signal/canonical_signal.py

两个文件职责不同：
- `spec/canonical_signal.py` — V13 Canonical 合约层（已冻结）
- `signal/canonical_signal.py` — 旧 Signal 系统的契约

P1.4 不合并（属于 P1.6 Contract Consolidation 范围）。

---

## 变更清单

| 文件 | 变更 |
|------|------|
| `src/tongshu/reasoning/cross_analysis.py` | 添加 P1.4 DEPRECATED 头部 |
| `src/tongshu/signal/convergence.py` | 更新 deprecation 注释 |
| `src/tongshu/render/template_fallback.py` | 移除 6 条 CONFLICTED 模板 |

---

## 测试验证

| 套件 | 结果 |
|------|------|
| `tests/spec/` (204 tests) | ✅ 全 PASS |
| `tests/spec/test_vertical_slice*.py` (42 tests) | ✅ 全 PASS |
| `grep CONFLICTED template_fallback.py` | ✅ 0 matches |
| `grep CrossAnalyzer pipeline.py` | ✅ 保留（deprecated，向后兼容） |

---

## 架构正确性确认

```
旧 pipeline:
  pipeline.py → CrossAnalyzer → ALIGNED/PARTIAL/INSUFFICIENT
              → template_fallback(CONFLICTED)  ← 已移除

新 architecture (P1.3):
  CrossDomainOrchestrator
    → MultiDomainSemanticCoverage
      → domain × semantic × engine → assertion_ids
      → Structured Observation（非 Judgment）
```

**关键原则**：
- `CrossAnalyzer` 保留在旧 pipeline（向后兼容），但标记 DEPRECATED
- `CONFLICTED` 不再出现在任何生产代码路径
- P1.3 `CrossDomainOrchestrator` 是完全独立的新层，不依赖旧 CrossAnalyzer

---

## 最终状态

```text
P1.2 Architecture          🔒 FROZEN
P1.3 Cross-Domain          🔒 FROZEN
P1.4 Cross-System Semantics ✅ IMPLEMENTED
```
