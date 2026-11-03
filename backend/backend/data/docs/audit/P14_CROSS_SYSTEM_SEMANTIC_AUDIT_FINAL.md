# P1.4 Cross-System Semantic Audit — Final Report

**Date**: 2026-09-02
**Commit baseline**: `e13d76f` (P1.5 production_verified flag)
**Status**: ✅ AUDIT COMPLETE — 8 findings, 0 violations

---

## 审计目标

验证 CrossDomainOrchestrator 及整个 P1.3+P1.5 新链路是否真正实现了"互补不比较"（V13 §二）原则：

1. Orchestrator 是否比较不同引擎的 direction？
2. Coverage 是否产生新语义结论？
3. 生产路径上是否有任何 old cross-analysis / convergence 调用？
4. 未验证规则是否从任何入口都能进入生产？

---

## 三重取证结果

### ① 调用图取证

| 符号 | src/ 生产代码引用数 | tests/ 引用数 | 结论 |
|------|---------------------|---------------|------|
| `CrossAnalyzer` | 0 (仅 cross_analysis.py 自身定义) | 2 (T16, Gate C scan) | ✅ 孤儿代码 |
| `ConvergenceArbiter` | 0 (仅 convergence.py 自身定义) | 4 (vertical slice tests) | ✅ 孤儿代码 |
| `convergence` | 0 | 18 (temporal_convergence schema tests) | ✅ 命名隔离 |
| `cross_analysis` | 0 | 2 | ✅ 孤儿代码 |

**确认**：`convergence.py` 和 `cross_analysis.py` 在 src/ 中零生产调用。两者仅存在于各自文件内部定义，pipeline/aggregator/cross_domain 均无引用。

### ② 生产入口链取证

```
pipeline.py
  → compute_stage.py (Bazi + Ziwei engine → Evidence)
  → render_stage.py (Assertion → StructuredOutput)
  → audit_composer.py (Provenance verification)
  → CrossDomainOrchestrator (optional, structured observation)
```

```
grep "ConvergenceArbiter" pipeline.py compute_stage.py render_stage.py audit_composer.py
→ 0 matches

grep "CrossAnalyzer" pipeline.py compute_stage.py render_stage.py audit_composer.py
→ 0 matches

grep "convergence" src/tongshu/signal/aggregator.py
→ 0 matches (docstring says "NO Temporal Convergence (that's Phase 4)")
```

**确认**：旧 CrossAnalyzer / ConvergenceArbiter 未接入新 pipeline。

### ③ 测试对象核对

| 测试文件 | 测试对象 | 是否生产路径 |
|----------|----------|-------------|
| `test_cross_domain_integration.py` (25 tests) | CrossDomainOrchestrator | ✅ 集成测试 |
| `test_p15_shadow_integration.py` (32 tests) | Pipeline end-to-end | ✅ 影子链路 |
| `test_contract_gate.py` (Gate B admission) | ProductionRuleLoader | ✅ 准入门禁 |
| `test_vertical_slice_*.py` | Full runtime chain | ✅ 运行时验证 |

---

## 审计发现

### F1: CrossDomainOrchestrator 语义纯净 ✅

**审查范围**：`orchestrator.py` 全部 170 行

| 检查项 | 结果 |
|--------|------|
| 比较不同引擎 direction | ✅ 无（line 102-108: direction 来自 rule，非比较结果） |
| 计算 confidence/weight/score | ✅ 无 |
| 产生 CONFLICTED/ALIGNED/PARTIAL | ✅ 无 |
| 投票/多数决逻辑 | ✅ 无 |
| 旧 Signal/CrossAnalyzer/Convergence 调用 | ✅ 无 import |
| evidence_count 暴露 | ✅ 无（用 coverage.total_assertions 替代） |
| by_engine 分离存储 | ✅ 有（line 80-160） |
| Provenance 保持 | ✅ 有（EvidenceRef 完整追踪） |

**结论**：Orchestrator 是纯结构性编排器，不产生任何跨体系比较。

### F2: CrossDomainResult 结构纯净 ✅

**审查范围**：`result.py` 全部 174 行

| 检查项 | 结果 |
|--------|------|
| 含 direction/polarity/strength/confidence 字段 | ✅ 无（forbidden list in docstring only） |
| 含 CONFLICTED/ALIGNED/PARTIAL 状态 | ✅ 无 |
| verify_no_cross_comparison() 方法 | ✅ 存在，可运行时调用 |
| to_dict() 不含 forbidden 字段 | ✅ 仅 case_id/temporal_scope/by_engine/coverage |

**结论**：数据结构层面禁止了所有 forbidden 语义。

### F3: Production Admission Gate 有效 ✅

**验证脚本执行结果**：

```python
load(verified_rules)       → _production_verified=False, rules=1    # dev/test path
ProductionRuleLoader.load(verified)  → _production_verified=True, rules=1  # production path
load(unverified_rules)     → _production_verified=False, rules=1    # dev/test accepts all
ProductionRuleLoader.load(unverified) → _production_verified=True, rules=0  # HARD REJECT
```

**结论**：`ProductionRuleLoader` 是硬拒绝 gate，unverified/candidate 规则一律拒绝（计数=0，非空库）。

### F4: Dead Code — cross_analysis.py ⚠️

路径：`src/tongshu/reasoning/cross_analysis.py`

- 标记为 DEPRECATED (P1.4)
- 零生产调用
- 但仍在 `src/tongshu/` 中，非 archive/
- 包含 `CROSS_STATES`, `REASON_CODES`, `CrossResult`, `CrossAnalyzer` 类

**风险评估**：低（零调用），但违反"已删除即不存在"原则。

### F5: Dead Code — convergence.py ⚠️

路径：`src/tongshu/signal/convergence.py`

- 标记为 DEPRECATED (P1.2/P1.4)
- 零生产调用
- 但定义了完整的 `ConvergenceArbiter` 类，产出 ALIGNED/CONFLICTED/PARTIAL/INSUFFICIENT/UNDEFINED
- **含 `confidence` 计算和方向比较逻辑**（与"互补不比较"直接冲突的语义残留）

**风险评估**：中（语义污染风险）。虽然当前零调用，但代码定义了 forbidden 语义，未来开发者可能误用。

### F6: `production_verified` 可伪造 ⚠️

```python
AssertionRuleLibrary(rules, production_verified=True)  # 绕过 ProductionRuleLoader
```

**当前状态**：作为 P1.5 防线可用，但非不可伪造的 admission proof。

**建议**：在 `__init__` 中添加 factory method 保护，或移除 public `_production_verified` setter。

### F7: 测试 fixture `verified` 标识模糊 ⚠️

测试规则文件使用 `"verification_status": "verified"`，但这只是测试授权状态，不代表经过原典审核。

**建议**：增加 `verification_scope` 字段区分：
- `TEST_FIXTURE` — 测试用，不经过原典审核
- `SOURCE_VERIFIED` — 原典来源已验证
- `PRODUCTION_ADMITTED` — 通过 Admission Registry 准入

### F8: Gate B 负向测试覆盖充分 ✅

`TestGateB_RuleAdmission` 已覆盖：
- T1: 测试 fixture 不在生产目录
- T2: 测试 fixture 标记为 unverified
- T3: 生产目录不含测试 fixture
- T4: `load_verified()` 拒绝 unverified → 空库
- T5: `load_verified()` 接受 verified → 非空库
- T6: 混合 bundle 只保留 verified
- T7: `ProductionRuleLoader` 强制走 `load_verified()`

**结论**：负向测试已充分覆盖 Admission Gate。

---

## 语义扫描汇总

```
cross_domain/  forbidden semantics scan:
  direction (as cross-system comparison): 0  ← only in orchestrator.py:108 as rule.direction (from rule, not compared)
  confidence / weight / score:             0
  CONFLICTED / ALIGNED / PARTIAL:         0  ← only in docstring forbidden lists
  vote / compare / rank:                  0

production pipeline forbidden imports:
  CrossAnalyzer:                           0
  ConvergenceArbiter:                      0
  cross_analysis:                          0
  signal.convergence:                      0
```

---

## 待办事项（User 裁决中确认）

| 优先级 | 事项 | 状态 |
|--------|------|------|
| P0 | 归档 `cross_analysis.py` 和 `convergence.py` 到 `archive/` | 🔴 待实施 |
| P1 | `verification_scope` 字段设计 + 测试 fixture 更新 | 🟡 待 User 裁决 |
| P1 | `production_verified` 不可伪造保护 | 🟡 待 User 裁决 |
| P2 | P1.6 Assertion/Judgment Boundary | 🟡 待实施 |
| P2 | P1.7 Runtime Convergence | 🟡 待实施 |

---

## 最终结论

```
CrossDomainOrchestrator 语义审计:      ✅ PASS — 纯结构性编排，无跨体系比较
Production Admission Gate:             ✅ PASS — load_verified 硬拒绝 unverified
Negative Tests (Gate B):               ✅ PASS — 7 tests 覆盖拒绝路径
Forbidden Semantics in Production:     ✅ PASS — 0 calls to CrossAnalyzer/Convergence
Dead Code Risk:                        ⚠️ MEDIUM — convergence.py 含 forbidden 语义残留
Architecture Gate (production_verified): ✅ PASS — 当前阶段有效防线
```

**P1.4 审计结论**：架构方向正确，核心语义边界已建立。遗留问题是 dead code（convergence.py）和测试 fixture 标识模糊，不影响当前生产路径的安全性。
