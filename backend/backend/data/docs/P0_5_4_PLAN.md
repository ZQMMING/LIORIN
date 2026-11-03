# P0-5.4 工作计划：寻找不依赖 strength_engine 的 Authorized Primitive

**目标**: 基于 P0-3.7 的 4 条 EXPLICIT 授权，找到不依赖 strength_engine 的 Canonical Primitive

---

## 一、背景

P0-3.7 确认 4 条 EXPLICIT 授权：
1. 滴天髓_生克制化_总论："生克制化，须制中有生，生中有制"
2. 滴天髓_理法_气势："一行得二三人之气，则党众而专，须从其势"
3. 滴天髓_理法_生扶克泄耗："生克制化，须制中有生，生中有制"
4. 渊海子平_论法_论太岁吉凶_5："日犯岁君，灾殃必重；五行有救，其年反必招财"

当前架构：
- Canonical State ✅ 已建立
- de_ling/de_di/de_shi ❌ 未实现（在 legacy strength_engine）
- strength_engine 🔒 LEGACY（不能用于生产）

---

## 二、审计目标

### 1. 分析 4 条 EXPLICIT 授权
哪些可以：
- 使用当前 Canonical State（facts + relations）直接计算？
- 需要新增 Canonical Feature？
- 需要等待后续实现？

### 2. 识别不依赖 strength_engine 的 Primitive
优先选择：
- 只涉及 L1 事实（天干地支五行）
- 只涉及 L1 关系（生克制化）
- 不涉及旺衰评分

---

## 三、候选 Primitive

### 候选 1: 五行生克关系
- 原典：生克制化，须制中有生
- 计算：检查四柱中是否存在相克的五行，同时存在相生的五行
- 依赖：不需要 strength_engine，只需要四柱和五行关系

### 候选 2: 天干地支同党
- 原典：一行得二三人之气（二三人可能是约数）
- 计算：检查天干或地支中是否有 >=2 个同五行的元素
- 依赖：不需要 strength_engine，只需要四柱和五行映射

### 候选 3: 日干支与太岁关系
- 原典：日犯岁君，灾殃必重
- 计算：检查日干是否克太岁（年干）
- 依赖：不需要 strength_engine，只需要四柱和天干五行

---

## 四、实现计划

1. 创建 P0-5.4 脚本，分析 4 条 EXPLICIT 授权
2. 识别哪些 Primitive 可以使用当前 Canonical State
3. 选择 1-2 个候选 Primitive 进行验证
4. 提交验证报告等待 GPT 裁决

---

**请 GPT 裁决是否批准此计划**
