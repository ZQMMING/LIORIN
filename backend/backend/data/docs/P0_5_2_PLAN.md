# P0-5.2 工作计划：Threshold 来源审计 + 规则分层

**目标**: 把 Condition 正式分成5层，隔离 ENGINEERED_THRESHOLD

---

## 一、背景

P0-5.1 确认：
- de_di >= 2: ENGINEERED_THRESHOLD（没有原典授权）
- de_shi >= 2: ENGINEERED_THRESHOLD（没有原典授权）

**核心问题**：
> CANONICAL Feature ≠ CLASSICAL Condition

需要把 Condition 正式分成5层：
- CLASSICAL_EXPLICIT（原典明确授权）
- CLASSICAL_IMPLICIT（原典暗示但未明确）
- ENGINEERED_THRESHOLD（工程定义）
- SEMANTIC_ONLY（语义保留）
- UNRESOLVED（未确定）

---

## 二、规则分层架构

### 1. CLASSICAL_EXPLICIT + VERIFIED
→ 可授权，进入 Classical Judgment

### 2. CLASSICAL_IMPLICIT
→ 暂不授权

### 3. ENGINEERED_THRESHOLD
→ 研究层，禁止 Classical Judgment

### 4. SEMANTIC_ONLY / UNRESOLVED
→ 禁止 Judgment

---

## 三、实现计划

1. 扩展 AuthorizationStatus 枚举
2. 更新 auth_gate 逻辑
3. 修改 P0-5 测试脚本
4. 验证分层效果

---

## 四、关键约束

- ENGINEERED_THRESHOLD 不能标记为 CLASSICAL_EXPLICIT
- 不能进入 Classical Authorization Gate
- 可以作为研究/实验规则，但不能标为五经原典断言

---

**请 GPT 裁决是否批准此计划**
