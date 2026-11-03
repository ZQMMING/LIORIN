# P1.6 Assertion → Judgment Boundary Audit Report

**Date**: 2026-09-02
**Status**: 🔴 BOUNDARY VIOLATION DETECTED — 生产管道未接 P1.3/P1.5
**Baseline**: 272 spec tests PASS, AdmissionRecord hash-based integrity ✅

---

## 审计目标

验证 P1.6 八大边界规则在生产路径上的满足情况。

### 八大边界规则
1. Assertion 与 Judgment 职责边界不可混淆
2. Assertion 不得偷偷携带未经授权的 Judgment 结论
3. Judgment 只能消费已经授权的 Assertion / Signal
4. 不允许通过 fallback/默认值/legacy 字段/旁路重新产生 Judgment
5. Judgment 层不能反向改变 Assertion 的事实语义
6. PRODUCTION_ADMITTED 之前的资产不能进入生产 Judgment
7. 所有 Production Judgment 路径最终都必须经过统一授权边界
8. 测试必须覆盖正向 + 负向 + bypass

---

## 三重取证结果

### ① 调用图取证

| 符号 | src/ 生产代码引用数 | tests/ 引用数 | 结论 |
|------|---------------------|---------------|------|
| `CrossDomainOrchestrator` | **0** | 25 | 🔴 孤儿代码 |
| `ProductionRuleLibrary` | **0** | 多处 | 🔴 孤儿代码 |
| `AdmissionRecord` | **0** | 测试中 | 🔴 孤儿代码 |
| `JudgmentRuleLibrary` | **0** | 0 | 🔴 零引用 |
| `CanonicalAssertion` | **0** | 测试中 | 🔴 孤儿代码 |

**结论**：P1.3/P1.5 新架构（CrossDomainOrchestrator + AdmissionRecord + ProductionRuleLibrary）全部**未接入生产管道**。

### ② 生产入口链取证

```
pipeline.py
  └── compute_stage.py
        ├── SignalEngine.build() → signals (含 direction via _DIRECTION_MAP)
        │     _DIRECTION_MAP = {"INCREASE": "POSITIVE", "DECLINE": "NEGATIVE", ...}
        ├── _build_atomic_claims(theme, signals)
        │     └── claim["direction"] = sig.direction  ← 从 Signal 直接取，无 Rule 授权
        ├── CanonicalComposer.compose(atomic_claims=...)
        └── RenderStage.run(compute, ...)
              └── Renderer.render(payload) → text
```

```
grep "CrossDomainOrchestrator\|ProductionRuleLibrary\|AdmissionRecord" src/tongshu/pipeline.py src/tongshu/pipeline_stages/
→ 0 matches (仅注释提及)
```

**确认**：生产管道完全走旧 Signal → Claim 路径，不经过任何 Assertion 授权 Gate。

### ③ 方向（direction）溯源

```
src/tongshu/reasoning/signal_engine.py:
  _DIRECTION_MAP = {
      "INCREASE": "POSITIVE",    # ← 信号映射，非原典授权
      "DECLINE": "NEGATIVE",
      "STABLE": "NEUTRAL",
      "VOLATILE": "CHANGE",
  }
  direction = _DIRECTION_MAP.get(signal.direction, "UNKNOWN")

src/tongshu/pipeline_stages/compute_stage.py:
  claims.append({"direction": sig.direction, ...})  # 直接用 signal 的 direction
```

**对比应有路径**：
```python
# 应有：通过 AssertionRuleLibrary.find_rule() 授权
rule = assertion_lib.find_rule(atom, context)
if rule is None:
    continue  # NO_ASSERTION
direction = rule.direction  # ← 来自 Authorized Assertion Rule
```

---

## 审计发现

### F1: 生产方向未经 Assertion Rule 授权 🔴

**现状**：`compute_stage.py:286-294` 直接从 Signal 取 direction。

**违反规则**：#2 (Assertion 不得携带未经授权的方向)

### F2: CrossDomainOrchestrator 未接入生产 🔴

**现状**：`compute_stage.py:144` 注释写着 "replaced by CrossDomainOrchestrator"，但代码中**没有实际调用**。

**违反规则**：#7 (所有生产路径须经统一授权边界)

### F3: JudgmentRuleLibrary 零引用 🔴

**现状**：`judgment_rule_library.py` 存在但生产管道零引用，`find_judgment()` 从未被调用。

**违反规则**：#3 (Judgment 只能消费已授权的 Assertion)

### F4: atomic_claims 携带方向绕过授权边界 🔴

**现状**：
```python
claims.append({
    "direction": sig.direction,  # ← 直接来自 signal，未经 Rule 授权
    "strength": "MODERATE",       # ← 硬编码
    ...
})
```

**风险**：方向从 Signal 直接传递到 Render，绕过了 `ProductionRuleLibrary.find_rule()`。

**违反规则**：#2, #4, #7

### F5: P1.3/P1.5 组件均为孤儿代码 🔴

`CrossDomainOrchestrator`, `ProductionRuleLibrary`, `AdmissionRecord`, `CanonicalAssertion` 在 `src/tongshu/` 中零生产调用方。只有测试文件引用它们。

**违反规则**：#7

### F6: cross_result=None 硬编码 ⚠️

```python
return ComputeResult(
    ...
    cross_result=None,  # ← 硬编码 None
    ...
)
```

P1.4 注释说 "replaced by CrossDomainOrchestrator"，但 `cross_result` 始终为 None。

---

## 已验证的安全机制 ✅

### AdmissionRecord 不可伪造 ✅

`7fce87b` 已实现不可伪造的 Admission Proof：
- `AdmissionRecord` = frozen dataclass，含 `admission_hash`（对规则内容+元数据的 SHA-256）
- `ProductionRuleLibrary` 只能通过 `AdmissionRecord` 构造（类型隔离）
- 外部无法伪造（需完整规则内容计算 hash）
- 10 个攻击向量测试全部 PASS

**这解决了 P1.4 裁决中的 "verified_by 可信身份" 和 "threading.local 信任边界" 问题。**

### verification_scope 三态 ✅
- `TEST_FIXTURE` / `SOURCE_VERIFIED` / `PRODUCTION_ADMITTED`
- Legacy `verified` 自动降级为 `SOURCE_VERIFIED`（不进入生产）

---

## 修复方案

### Step 1: 生产管道集成 CrossDomainOrchestrator

在 `compute_stage.py` 中：
1. 接受 `assertion_library: ProductionRuleLibrary` 参数
2. 在 `_build_atomic_claims()` 之前，先通过 `CrossDomainOrchestrator.orchestrate()` 编排
3. `atomic_claims` 的 direction 来自 `rule.direction`（非 `sig.direction`）
4. `cross_result` 从 None 改为实际 Orchestrator 输出
5. 无授权 Rule → skip claim（NO_ASSERTION，不产出入 render）

### Step 2: 添加 P1.6 边界测试

新增 `tests/spec/test_p16_assertion_judgment_boundary.py`：
- T16: 生产管道必须使用 CrossDomainOrchestrator（import 扫描）
- T17: atomic_claim direction 必须来自 Rule（非 Signal）
- T18: 无授权 Rule → 不产出 claim
- T19: cross_result 不能为 None
- T20: JudgmentRuleLibrary 必须被生产路径引用

### Step 3: 更新文档

`docs/audit/P16_ASSERTION_JUDGMENT_BOUNDARY.md`

---

## 当前 P1 状态

```
P0   🔒 FROZEN
P1.2 🔒 FROZEN
P1.3 ✅ 代码存在，未接入生产
P1.4 ✅ CLOSED (AdmissionRecord hash-based ✅)
P1.5 ✅ VERIFIED
────────────────
P1.6 🔴 BOUNDARY VIOLATION — 待修复
```

**测试基线**: 272 spec tests PASS

**下一步**: 修复生产管道集成 → P1.6 复审 → P1.7 Runtime Convergence
