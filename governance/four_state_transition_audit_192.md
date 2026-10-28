# PATCH-192 Rule→Assertion 四态转换链审计（SEALED）

## 审计对象
root/combination/transparent_condition_evaluator + condition_bundle + condition_router

## 逐项核

### 1. TRUE→SAT / FALSE→UNSAT
- root: v=True→SAT, v=False→UNSAT（v为布尔）✅
- combination: hit=True→SAT, hit=False→UNSAT ✅
- transparent: 存在→SAT, 不存在→UNSAT ✅

### 2. None/missing→UNKNOWN（不自动FALSE）
- root: `if v is None → UNKNOWN(target_root_missing_fact)` ✅
- root: `if not spec → UNKNOWN(not_registered)` ✅
- root: `NOT_IMPLEMENTED → UNKNOWN` ✅
- **已知边界**: combination evaluator `cf.get(kind,[])` 对 missing key 会静默 UNSATISFIED。
  但 combination_facts 的 key（六合/六冲/三刑/六害/六破/三合/三会）是 build() 固定全出的，实际不触发。记录为已知边界，不改代码。

### 3. UNKNOWN→UNKNOWN
- bundle required: 无UNSAT但有UNKNOWN→UNKNOWN ✅
- bundle blocked: 有UNKNOWN→BLOCK_UNKNOWN（不误判CLEAR）✅
- 空 required→UNKNOWN（不自动SAT）✅；空 blocked→BLOCK_UNKNOWN（不自动CLEAR）✅

### 4. NOT_AUTHORIZED→NOT_AUTHORIZED
- evaluator NOT_IMPLEMENTED→UNKNOWN（不冒充支持）✅
- synthesize: r UNSAT或b BLOCKED→NOT_SUPPORTED；r SAT且b CLEAR→SUPPORTED；其余PENDING ✅
- supported纯记录不参与硬判 ✅

### 5. 隐式bool / None转FALSE
- bundle全部用 `stats.get(key,0)>0` 显式计数，无隐式bool ✅
- 无 `if facts.get(...)` 裸布尔判断（除已记录的combination get）✅

## 结论
四态转换链干净：
```
L0 TRUE/FALSE → SAT/UNSAT
None/missing(可缺失Fact) → UNKNOWN
未注册/NOT_IMPLEMENTED → UNKNOWN
bundle: required全SAT且blocked CLEAR → SUPPORTED
        required UNSAT 或 blocked BLOCKED → NOT_SUPPORTED
        其余(含UNKNOWN/BLOCK_UNKNOWN) → PENDING
NOT_AUTHORIZED 独立, 永不转TRUE/FALSE/SUPPORTED
```
唯一已知边界：combination evaluator对missing key静默UNSAT，但combination_facts key固定全出，实际不触发，留痕。
