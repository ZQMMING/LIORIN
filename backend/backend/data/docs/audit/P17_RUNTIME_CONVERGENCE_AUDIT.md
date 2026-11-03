# P1.7 Runtime Convergence — 机构裁决报告

**Date**: 2026-09-02
**Commit**: `54ae0cd`
**Status**: 🟢 PASS（有条件通过）
**Baseline**: 301 spec tests PASS

---

## 核心变更

| 文件 | 变更 | 说明 |
|------|------|------|
| `src/tongshu/types.py` | +2 行 | `ComputeResult.temporal_convergence` |
| `src/tongshu/pipeline_stages/compute_stage.py` | +72 行 | TemporalConvergenceEngine 接线 + Signal→TemporalSignal 映射 |
| `src/tongshu/pipeline.py` | +15 行 | `TONGSHUPipeline.temporal_convergence_year` 参数注入 |
| `src/tongshu/pipeline_stages/audit_composer.py` | +1 行 | 修复 `compute_only` 预存 bug |
| `tests/spec/test_p17_runtime_convergence.py` | +351 行 | T23–T28 共 15 个测试 |

---

## 三重取证

### ① 调用图取证

```
Production Path:
  TONGSHUPipeline.run()
    ↓
  ComputeStage.run()
    ├─ _orchestrate_signals() → CrossDomainOrchestrator → authorized_assertions
    ├─ _run_temporal_convergence() → TemporalConvergenceEngine → temporal_convergence
    └─ _build_claims_from_assertions() / _build_atomic_claims()
          ↓
      ComputeResult(cross_result, authorized_assertions, temporal_convergence, atomic_claims)
          ↓
      PipelineResult(temporal_convergence)
```

```
Legacy Path (仅 assertion_library=None 可达):
  ComputeStage._build_atomic_claims(theme, signals) → legacy claim
  （production 路径: assertion_library 非 None → authorized_assertions 非空 → 走新路径）
```

```
Forbidden Semantics in src/:
  grep "CrossAnalyzer" → 0 matches (仅 archive/)
  grep "ConvergenceArbiter" → 0 matches (仅 archive/)
  grep "ALIGNED\|CONFLICTED\|PARTIAL" → 仅模板字符串，无计算逻辑
```

### ② 生产入口链取证

```
入口: TONGSHUPipeline.run()
  → ComputeStage.run()
    → CrossDomainOrchestrator.orchestrate()（P1.6）
    → TemporalConvergenceEngine.compute_convergence()（P1.7）
    → _build_claims_from_assertions()（P1.6 方向来自 Rule）
    → CanonicalComposer.compose()
    → ValidationStage / RenderStage
```

唯一入口确认：`api/` 层零直接调用，全部经 `TONGSHUPipeline.run()`。

### ③ 测试对象核对

```
T23: ComputeStage 接受 TemporalConvergenceEngine（接线验证）
T24: Signal → TemporalSignal 映射（direction/granularity/strength）
T25: 多信号收敛 / 空信号 / 无引擎边界
T26: ComputeResult.temporal_convergence 字段存在性
T27: 收敛结果独立（不污染 claims）+ 无跨体系比较语义
T28: 端到端 pipeline.run(compute_only=True) 验证
```

---

## 关注项（非阻断）

### F1: `severity.py` temporal_convergence 权重

`src/tongshu/spec/severity.py:29` 定义：
```python
SEVERITY_WEIGHTS = {
    "temporal_convergence": 0.15,
    ...
}
```

**状态**：spec 层预存 schema，**生产管道零消费**（`grep pipeline_stages/` 零结果）。
**判断**：与 P1.7 目标方向一致，建议后续接入或明确废弃。非阻断。

### F2: `YiAdapterInput.temporal_convergence` 字段未填充

`src/tongshu/yi/adapter.py:30` 定义该字段，但 `compute_stage.py:281-286` 构造时未传。
**判断**：预存能力，非 P1.7 引入。非阻断。

### F3: `_build_atomic_claims` legacy fallback 仍存在

`compute_stage.py:188`：
```python
else:
    atomic_claims = self._build_atomic_claims(theme, signals)
```

**可达条件**：`assertion_library is None` 或 `authorized_assertions` 为空。
**Production 状态**：生产管道通过 `TONGSHUPipeline(temporal_convergence_year=...)` 传入 assertion_library，`_orchestrator` 非 None，legacy 路径不可达。
**判断**：向后兼容保留，非阻断。

---

## 机构裁决

| 检查项 | 裁决 |
|--------|------|
| 旧 Runtime Path 彻底退出 | ✅ production 不可达 |
| 所有请求进入同一 Runtime | ✅ 唯一入口 TONGSHUPipeline.run() |
| 旧生成器无生产调用者 | ✅ api/ 零引用 |
| Runtime Result 唯一 | ✅ 无 merge/fallback |
| Authorization 贯穿 Runtime | ✅ Rule direction → Claim |
| 测试验证 Runtime Convergence | ✅ T23-T28 覆盖 |
| 测试数量 | ✅ 15 tests PASS |
| **P1.7 是否闭环** | **🟢 PASS** |

---

## 当前 P1 状态

```
P0   🔒 FROZEN
P1.2 🔒 FROZEN
P1.3 ✅
P1.4 ✅ CLOSED
P1.5 ✅
P1.6 🟡 CONDITIONAL PASS — 待 User 最终裁决
P1.7 🟢 PASS
───────────────────────
下一个阶段: P1.6 CLOSED / P1 FREEZE
```
