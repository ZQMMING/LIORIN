# PATCH-193 Judgment/Assertion 输出端四态审计（SEALED）

## 审计对象
judgment_producer（最终输出端）：核四态在输出端是否被压扁。

## 逐项核

### 1. UNSAT→NOT_SUPPORTED
- direction 直接透传 resolved['candidate_direction']，不重新推导 ✅
- synthesize 已把 required UNSAT/blocked BLOCKED 映射为 NOT_SUPPORTED，judgment 原样输出 ✅

### 2. UNKNOWN→PENDING
- 第17行：direction==PENDING → 返回 PENDING_REVIEW，不产确定 Judgment ✅
- note："required满足但仍有UNKNOWN, 不产确定Judgment" ✅

### 3. NOT_AUTHORIZED 原样保持
- NOT_AUTHORIZED 在 evaluator 层即为 UNKNOWN，到 judgment 前已变 PENDING，不压 TRUE/FALSE ✅
- judgment 不把 PENDING 降成 NOT_SUPPORTED ✅

### 4. SUPPORTED 只是记录不硬判
- direction==SUPPORTED 时 state=RECORDED，note="candidate方向记录, 非成格/吉凶" ✅
- 无 is_success/成格/吉凶字段 ✅

### 5. Assertion 不自行推导 Rule 状态
- direction 来自上游 resolved，judgment 不计算新状态 ✅
- fail-closed 三道：ambiguous(条件词多匹配)/无evidence(无Assertion反查)/PENDING拦截 ✅
- provenance: Judgment→Assertion→Evidence→原文 完整 ✅

## 结论
输出端无压扁：
```
PENDING → PENDING_REVIEW(不产确定)
SUPPORTED → RECORDED(仅记录, 非成格)
NOT_SUPPORTED → 透传(required UNSAT/blocked BLOCKED)
NOT_AUTHORIZED → evaluator层UNKNOWN→PENDING, 不压FALSE
fail-closed: ambiguous/no-provenance 拒绝产Judgment
```
Rule→Assertion 四态语义链全链封死，可继续补原典规则。
