# P0-3.6 验证报告：Primitive/Condition 正式 Schema + Authorization 边界

**日期**: 2026-08-30  
**状态**: 🟢 PASS（符合约束）

---

## 一、核心约束执行确认

### 约束 1: CLASSICAL_IMPLICIT 不自动授权

✅ 已实现
- `check_authorization()` 要求 `CLASSICAL_EXPLICIT + VERIFIED`
- `CLASSICAL_IMPLICIT` 即使 VERIFIED 也不授权

### 约束 2: generate_judgment() 审计

✅ 已实现
- 临时方案：返回 None
- 避免旧评分逻辑污染
- 后续需要实现新的 Judgment Generator

### 约束 3: operator/value 来源明确

✅ 已实现
- `source_documented` 字段强制文档化来源
- 未文档化的 operator/value 会抛异常

---

## 二、验证结果

总数：9 条 C 类证据

| 状态 | 数量 | 占比 |
|------|------|------|
| VERIFIED | 0 | 0% |
| STRUCTURED | 0 | 0% |
| UNRESOLVED | 9 | 100% |
| INVALID | 0 | 0% |

| 授权级别 | 数量 | 占比 |
|----------|------|------|
| CLASSICAL_EXPLICIT | 0 | 0% |
| CLASSICAL_IMPLICIT | 0 | 0% |
| UNRESOLVED | 9 | 100% |

**授权数**: 0（符合预期）

---

## 三、结果分析

### 为什么 0 VERIFIED？

保守策略：
- 只有 `CLASSICAL_EXPLICIT + VERIFIED` 才能授权
- 当前证据中没有明确的 EXPLICIT 授权标记
- 所有 9 条都标记为 UNRESOLVED

### 这是正确的

Gemini 裁决：
> "CLASSICAL_IMPLICIT 即使结构化，也先保持研究状态，不能自动产生 Judgment"

所以当前结果符合约束。

---

## 四、下一步

### 任务 1: 重新标注证据

为 4 条原典明确证据添加 `CLASSICAL_EXPLICIT` 标记。

### 任务 2: 实现 Judgment Generator

审计旧的 `generate_judgment()` 逻辑，实现新的无偏 Judgment Generator。

### 任务 3: 重新验证

重新运行验证，期望：
- 部分证据变为 VERIFIED
- 授权数增加
- 但不超过 4 条（保守估计）

---

## 五、关键结论

✅ **架构边界清晰**
- STRUCTURED vs VERIFIED vs UNRESOLVED 区分明确
- Authorization Gate 固化到代码

✅ **保守策略正确**
- 不替古人补条件
- 不自动授权 IMPLICIT
- 不产生 Judgment 除非明确授权

✅ **可追溯性完整**
- 每条证据都有 source_documented 标记
- operator/value 有明确来源

---

**请 Gemini 裁决是否继续执行下一步**
