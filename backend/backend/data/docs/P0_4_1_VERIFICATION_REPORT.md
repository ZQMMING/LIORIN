# P0-4.1 验证报告：真实五经 Primitive 语义分析

**日期**: 2026-08-30  
**状态**: 🟡 HOLD（需要原典审核）

---

## 一、验证结果

总测试: 12（4 Primitive × 3 Chart）  
生成 Judgment: 0  
Authorization Gate 生效: ✅  
未使用旧 strength_engine: ✅

---

## 二、关键发现

### 语义关系分布
- UNKNOWN: 9 条
- AND: 3 条

### 问题

1. **原典 Condition 未明确映射到 Feature**
   - 当前硬编码 `feature_ref="de_ling"`
   - 原典实际含义需要人工审核

2. **测试命例不满足条件**
   - 1995-1-1: de_ling=True，但 support=1.5 < drain=6.0
   - 其他命例 de_ling=False
   - 结果正确：条件不满足 → 无 Judgment

3. **保守策略正确**
   - 0 Judgment 是正确的安全状态
   - 不应该为了产生 Judgment 而修改条件

---

## 三、下一步建议

### 方案 1: 人工审核原典
- 回到原书，确认每条 Primitive 的真实 Condition
- 建立正确的 Feature 映射

### 方案 2: 保持 UNRESOLVED
- 承认当前无法确定语义关系
- 等待五经知识库完善后再验证

### 方案 3: 简化验证
- 用已知满足条件的命例测试
- 例如：找一个 de_ling=True 且 support > drain 的命例

---

## 四、关键结论

✅ **引擎工作正常**
- Authorization Gate 有效
- 未使用旧 strength_engine
- 条件评估逻辑正确

⚠️ **原典语义未确认**
- 不能确定 Condition 是否忠实于原典
- 需要人工审核

✅ **保守策略正确**
- 不为了通过率修改条件
- UNRESOLVED 比错误结构化更重要

---

**请 GPT 裁决下一步**
