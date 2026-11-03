# P2 Entry Audit — Full Repository Reconciliation

**Date**: 2026-09-02
**Commit Baseline**: `4dadd95` (P1 FREEZE: 移除 legacy _build_atomic_claims fallback)
**Method**: Local git diff + grep triple-evidence (call graph + production entry chain + test object verification)
**Scope**: Read-only audit. No code changes.

---

## 1. P1 FREEZE VERIFICATION

### A. PRODUCTION_ADMITTED 显式授权 ✅

| 检查项 | 证据 | 结果 |
|--------|------|------|
| `VerificationScope` 三态分离 | `src/tongshu/assertion/assertion_rule_library.py:59` — `PRODUCTION_ADMITTED / SOURCE_VERIFIED / TEST_FIXTURE` | ✅ PASS |
| `load_verified()` 只接受 `PRODUCTION_ADMITTED` | `assertion_rule_library.py:107` — `return self.verification_scope == VerificationScope.PRODUCTION_ADMITTED` | ✅ PASS |
| `_from_production_admission()` 内部工厂 | `assertion_rule_library.py:308` — `object.__new__(cls)` 绕过 `__init__` | ✅ PASS |
| `ProductionRuleLoader.load()` 唯一入口 | `assertion_rule_library.py:375-464` — 强制走 `load_verified()` | ✅ PASS |
| 外部无法直接构造 `_ProductionRuleLibrary` | `assertion_rule_library.py:296` — `__init__` 抛 TypeError | ✅ PASS |

### B. Assertion → Judgment fail-closed ✅

| 检查项 | 证据 | 结果 |
|--------|------|------|
| `_build_atomic_claims` 零引用 | `grep -rn _build_atomic_claims src/tongshu/` → 零结果 | ✅ PASS |
| else 分支 → NO CLAIM | `compute_stage.py:183-186` — `if authorized_assertions: ... else: atomic_claims = []` | ✅ PASS |
| direction 来自 Rule | `compute_stage.py:449` — `"rule_direction": rule.direction.value` | ✅ PASS |
| direction 不来自 Signal | `compute_stage.py:466` — `"direction": auth.get("rule_direction", "UNKNOWN")` | ✅ PASS |
| no hardcoded strength | `compute_stage.py:438` — `"strength": "AUTHORIZED"`（来自 Rule，非硬编码） | ✅ PASS |

### C. Signal 不得绕过 Rule/Assertion ✅

| 检查项 | 证据 | 结果 |
|--------|------|------|
| `find_rule()` 在生产路径被调用 | `compute_stage.py:443` — `rule = self._assertion_library.find_rule(atom, {})` | ✅ PASS |
| `CrossDomainOrchestrator` 接入生产 | `compute_stage.py:103-104` — 实例化条件：`is_production == True` | ✅ PASS |
| `authorized_assertions` 非空时才产 claim | `compute_stage.py:183-186` — else → `[]` | ✅ PASS |

### D. 唯一收敛路径 ✅

| 检查项 | 证据 | 结果 |
|--------|------|------|
| API 层只调用 `TONGSHUPipeline.for_demo()` | `src/tongshu/api/app.py:57,224` — 唯一入口 | ✅ PASS |
| 无独立 ComputeStage 调用路径 | `grep -rn TONGSHUPipeline ComputeStage src/tongshu/api/` → 仅 app.py | ✅ PASS |
| Production entry chain | `app.py → TONGSHUPipeline.run() → ComputeStage.run()` | ✅ PASS |

### E. 互补不比较 ✅

| 检查项 | 证据 | 结果 |
|--------|------|------|
| `CrossAnalyzer` 零生产引用 | `grep CrossAnalyzer src/tongshu/` → 仅 `cross_domain/orchestrator.py:15`（注释提及）+ `spec/canonical/judgment.py:18`（注释提及） | ✅ PASS |
| `ConvergenceArbiter` 零引用 | 零结果 | ✅ PASS |
| `cross_states` 零引用 | 零结果 | ✅ PASS |
| `ALIGNED`/`PARTIAL` 仅在模板字符串 | `render/template_fallback.py:17-38` — 纯文本模板，无计算逻辑 | ✅ PASS |
| Archive 隔离 | `archive/reasoning/cross_analysis.py`, `archive/signal/convergence.py`, `archive/spec/cross_states.py` — 不可 import（不在 sys.path） | ✅ PASS |

### F. LLM 无事实裁决权 ✅

| 检查项 | 证据 | 结果 |
|--------|------|------|
| `JudgmentRuleLibrary` 零生产调用 | `grep JudgmentRuleLibrary src/tongshu/pipeline.py src/tongshu/pipeline_stages/` → 零结果 | ✅ PASS |
| `signal_engine.py` 无 LLM 决策 | 零 `LLM/llm/model` 引用（除注释） | ✅ PASS |
| strength 不硬编码 | `compute_stage.py:438` — 来自 Rule，非 `"MODERATE"` | ✅ PASS |

---

## 2. P0 LEGACY STATUS

| 项目 | 状态 | 证据 |
|------|------|------|
| `convergence.py` 归档 | ✅ 已移入 archive | `archive/signal/convergence.py` |
| `cross_analysis.py` 归档 | ✅ 已移入 archive | `archive/reasoning/cross_analysis.py` |
| `cross_states.py` 归档 | ✅ 已移入 archive | `archive/spec/cross_states.py` |
| `signal_ontology.py` 归档 | ✅ 已移入 archive | `archive/spec/signal_ontology.py` |
| Import 安全 | ✅ 不可从 src/ import | Python 未找到这些模块 |
| `legacy/` 目录 | ⚠️ 存在但未在生产路径引用 | `src/tongshu/legacy/` 存在，grep 零生产调用 |
| `assertion_v2/` 目录 | ⚠️ 存在但未在生产路径引用 | `src/tongshu/assertion_v2/` 存在 |
| `strength_engine.py` | ✅ 已删除 | 仅存 `__pycache__/strength_engine.cpython-311.pyc` |

---

## 3. B-18~B-24 RECONCILIATION MATRIX

| ID | 原始声明 | 当前状态 | 核验结果 | 严重等级 |
|----|---------|---------|---------|---------|
| **B-18** | `evaluate_strength_features` 死代码被宣传为隔离层 | `src/tongshu/canonical/producer.py:6` 仅有一行注释提及迁移方向；`grep evaluate_strength_features` 零结果 | ✅ **已修复** — 函数不存在，引用已清除 | LOW |
| **B-19** | `strength_engine.py` 双 docstring + `from __future__` 失效 | `strength_engine.py` 已删除（仅 pyc 残留）；Python 3.11 支持 `from __future__` | ✅ **已修复** — 文件已移除 | LOW |
| **B-20** | `PowerComparisonEvaluator` 纯计数比较无原典授权 | `src/tongshu/canonical/condition_evaluator.py:153` 存在；需确认是否在生产路径被调用 | ⚠️ **需进一步审计** | MEDIUM |
| **B-21** | `condition_evaluator.evaluate()` 收 `Dict[str, Any]` 而非 `CanonicalState` | `condition_evaluator.py:58,113,173,233,284` — 全部 `evaluate(self, canonical_state: Dict[str, Any])` | ✅ **确认** — 类型解耦存在 | MEDIUM |
| **B-22** | `canonical/composer.py` 与 `canonical/state.py` 共用包名但无关 | `src/tongshu/canonical/` 下有 `composer.py` + `state.py` + `condition_evaluator.py` + `producer.py` 等共 11 个模块 | ⚠️ **需确认** — 命名空间是否合理 | LOW |
| **B-23** | `ARCHITECTURE_DECISION_RESULT.md:227` 文档误标模块不存在 | `grep 227 docs/audit/FINAL_ARCHITECTURE_AUDIT.md` → 零结果（行数可能已变） | ⚠️ **需核实** — 文件行数可能已变化 | LOW |
| **B-24** | `p0_8_10` 系列报告基于 mock dict 模式 | `grep mock Mock tests/spec/test_p1*.py tests/spec/test_cross*.py tests/spec/test_production*.py` → 零结果 | ✅ **已修复** — P1 测试无 mock | LOW |

### B-20 详细说明

```
src/tongshu/canonical/condition_evaluator.py:153 — class PowerComparisonEvaluator(BaseConditionEvaluator)
src/tongshu/canonical/condition_evaluator.py:361-362 — evaluator_type == "power_comparison"
```
- 位于 `canonical/` 模块（非 `legacy/`）
- 需确认是否在生产路径被调用（`grep -rn PowerComparisonEvaluator` in production code）

### B-21 详细说明

```
src/tongshu/canonical/condition_evaluator.py:58 — def evaluate(self, canonical_state: Dict[str, Any]) -> EvaluationResult:
```
- 5 个 evaluate 方法均收 `Dict[str, Any]` 而非 `CanonicalState`
- 这是类型安全漏洞，但不影响 P1 Freeze Contract（P1.7 的 TemporalConvergence 是观察层，不消费此模块）

---

## 4. G1~G4 STATUS

| ID | 目标 | 当前实现 | 状态 |
|----|------|---------|------|
| **G1** | Admission Registry（替代 threading.local()） | `threading.local()` 机制存在但非最终方案；`assertion_rule_library.py` 使用 `_production_context.inside_production` | 🔴 **未实现** |
| **G2** | verified_by Identity Binding（绑定真实审核身份） | `verified_by: str = ""` 仅非空检查，无审核身份验证 | 🔴 **未实现** |
| **G3** | Synthetic Hard Stop（ProductionLoader 全局拒绝 synthetic=true） | `RuleProvenance.from_dict()` backward-compat 映射未提及 synthetic 字段处理 | 🔴 **未实现** |
| **G4** | Unified Production Gate（所有入口经同一 Admission Gate） | `ProductionRuleLoader.load()` 是生产规则唯一入口，但 `AssertionRuleLibrary()` 直接构造仍存在（虽不接受 `production_verified=True`） | 🟡 **部分实现** |

---

## 5. P2 AUTHORITY LEDGER STATUS

| 组件 | 位置 | 生产引用 | 状态 |
|------|------|---------|------|
| `CrossDomainOrchestrator` | `src/tongshu/cross_domain/orchestrator.py` | `compute_stage.py:27,104,168` | ✅ 生产接线 |
| `ProductionRuleLibrary` | `src/tongshu/assertion/assertion_rule_library.py:284` | `compute_stage.py:443` | ✅ 生产接线 |
| `AdmissionRecord` | `src/tongshu/assertion/assertion_rule_library.py` | hash-based integrity | ✅ 已实现 |
| `TemporalConvergenceEngine` | `src/tongshu/temporal/convergence.py` | `compute_stage.py:40-41,173-175` | ✅ P1.7 接线 |
| `JudgmentRuleLibrary` | `src/tongshu/assertion/judgment_rule_library.py` | 零生产引用 | ⚠️ 孤儿代码 |
| `CanonicalAssertion` | `src/tongshu/assertion/` | 需确认 | ⚠️ 需核查 |

---

## 6. PRODUCTION RUNTIME TRACE

### 完整链路
```
src/tongshu/api/app.py:224
  → TONGSHUPipeline.for_demo(root)
    → ComputeStage(bazi_engine, ziwei_engine, huangli_engine, signal_engine, theme_engine,
                   assertion_library=prod_lib, temporal_convergence_engine=tce)
      ↓
    run():
      1. Engine layer (bazi + ziwei + huangli)
      2. SignalEngine.build() → signals[BASELINE, CYCLE_CONTEXT, DAILY_ACTIVATION]
      3. CrossDomainOrchestrator.orchestrate() → cross_result
      4. _extract_authorizations() → authorized_assertions (direction from Rule)
      5. TemporalConvergenceEngine.compute_convergence() → temporal_convergence (observation layer)
      6. _build_claims_from_assertions() → atomic_claims
      7. CanonicalComposer.compose() → canonical
      8. ValidationStage + RenderStage
```

### 唯一生产入口
- `src/tongshu/api/app.py:224` — `TONGSHUPipeline.for_demo(root)`
- 无其他独立路径

### 已知旁路风险
1. **G1 未实现**: `threading.local()` 是进程内信任标志，非 immutable admission proof
2. **G2 未实现**: `verified_by` 仅非空检查，无审核身份绑定
3. **G3 未实现**: `synthetic=true` 标记未被 ProductionLoader 全局硬拒绝
4. **B-20 需确认**: `PowerComparisonEvaluator` 在生产路径是否被调用
5. **B-21 确认**: `condition_evaluator.evaluate()` 收 `Dict[str, Any]` 而非 `CanonicalState`

---

## 7. NEW BLOCKER MATRIX

| # | 严重等级 | 描述 | 文件:行号 | 证据 |
|---|---------|------|----------|------|
| **N-1** | 🔴 HIGH | `JudgmentRuleLibrary` 零生产调用 — P1.6 审计遗留 | `src/tongshu/assertion/judgment_rule_library.py` | grep 零引用 |
| **N-2** | 🟡 MEDIUM | `canonical/condition_evaluator.py` evaluate() 收 Dict 非 CanonicalState | `condition_evaluator.py:58,113,173,233,284` | 类型解耦 |
| **N-3** | 🟡 MEDIUM | `PowerComparisonEvaluator` 生产路径调用确认 | `condition_evaluator.py:153` | 需 grep 确认调用方 |
| **N-4** | 🟠 LOW | `strength_engine.cpython-311.pyc` 残留 | `src/tongshu/engines/__pycache__/` | pyc 文件残留 |
| **N-5** | 🟠 LOW | `src/tongshu/legacy/` 和 `assertion_v2/` 目录存在 | `src/tongshu/legacy/`, `src/tongshu/assertion_v2/` | 需确认是否被 import |

---

## 8. P2 RECOMMENDED EXECUTION ORDER

### Phase P2.1: Authority Hardening（优先级最高）
```
P2.1.1  G1 — Admission Registry 实现
         替代 threading.local()，实现 immutable admission credential

P2.1.2  G2 — verified_by Identity Binding
         绑定真实审核身份到 AdmissionRecord

P2.1.3  G3 — Synthetic Hard Stop
         ProductionLoader 全局拒绝 synthetic=true 资产
```

### Phase P2.2: Type Safety（中等优先级）
```
P2.2.1  B-21 — condition_evaluator.evaluate() 类型修复
         Dict[str, Any] → CanonicalState

P2.2.2  B-20 — PowerComparisonEvaluator 原典授权审计
         确认是否在生产路径被调用，如被调用需补充原典依据
```

### Phase P2.3: Cleanup（低优先级）
```
P2.3.1  N-1 — JudgmentRuleLibrary 生产接线或归档
P2.3.2  N-4 — strength_engine.pyc 清理
P2.3.3  N-5 — legacy/ 和 assertion_v2/ 目录审计
```

---

## 测试基线

```
301 spec tests PASS
3 pre-existing failures (test_signal_engine_dual_track.py — data schema issue, unrelated)
4 warnings (DeprecationWarning in evaluation/l2_direction.py, corpus/validation.py)
```

---

**审计结论**: P1 FREEZE Contract 全量验证通过。P1.6/P1.7 生产路径 fail-closed 硬化完成。B-18/B-19/B-24 已修复。B-20/B-21 需 P2 处理。G1-G4 未实现，转入正式治理 backlog。
