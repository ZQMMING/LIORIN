# Judgment Schema V1 - 三层权威分离机制

**时间**: 2026-08-31  
**阶段**: Step 7 Judgment提取  
**依据**: GPT裁决 695120e  
**状态**: 🟡 PENDING_AUTHORITY_VALIDATION

---

## 核心原则（GPT裁决明确）

### 禁止自动推导
```
❌ Condition = 原典授权
   + Result = 原典出现
   → Judgment自动授权
```

### 必须独立验证
```
✅ Primitive Authority（已有）
   ↓
✅ Condition Authority（已有，9个）
   ↓
✅ Judgment Authority（新建，必须独立验证）
   ↓
GPT Final Ruling
   ↓
Production Judgment
```

---

## Judgment Schema定义

### 字段结构
```json
{
  "judgment_id": "DTS-JUDG-001",
  "source_primitive_ids": ["DTS-PRIM-010"],
  "source_condition_ids": ["DTS-COND-006"],
  
  "authority_layer": {
    "primitive_authority": {
      "status": "APPROVED",
      "verified_by": "Claude+GPT",
      "verification_date": "2026-08-31",
      "ruling_id": "71d29ed"
    },
    "condition_authority": {
      "status": "APPROVED",
      "verified_by": "Claude+GPT",
      "verification_date": "2026-08-31",
      "ruling_id": "12a66b4"
    },
    "judgment_authority": {
      "status": "PENDING",
      "verified_by": "PENDING",
      "verification_date": null,
      "ruling_id": null,
      "requires_evidence": true
    }
  },
  
  "judgment_content": {
    "logic": "IF天干=丙THEN...",
    "original_text_for_condition": "五阳皆阳丙为最",
    "original_text_for_judgment": "（需单独证明）",
    "causal_relationship": "原典是否明确说'若丙为最阳则...'？",
    "inference_type": "DEFINITION|PREDICTION|EVENT"
  },
  
  "risk_flags": [],
  "status": "PENDING_AUTHORITY"
}
```

---

## 三层权威验证流程

### Layer 1: Primitive Authority（已完成）
```
✅ 35个Primitive已授权
✅ Claude审计通过
✅ GPT Finalization通过
```

### Layer 2: Condition Authority（已完成）
```
✅ 9个Condition已授权
✅ Red-Team审查通过
✅ Claude独立审计通过
✅ GPT Finalization通过
```

### Layer 3: Judgment Authority（新建）
```
🔲 从Condition出发，寻找原典明确的Judgment
🔲 验证原典是否说出"若Condition成立，则Event发生"
🔲 Red-Team审查Judgment是否工程推断
🔲 Claude独立审计Judgment是否忠实原典
🔲 GPT最终裁决Judgment是否授权
```

---

## 关键验证点（GPT裁决明确）

### 验证1: 因果/判断关系是否原典明确授权
```
问题: 原典是否明确说"若X成立，则Y事件发生"？
✅ 允许: "若成格，则主贵"（原典明确）
❌ 禁止: "丙为最阳" + "成格" → 工程推断"主贵"
```

### 验证2: 是否为同义反复或定义扩展
```
问题: Judgment是否只是Condition的重述？
✅ 允许: Condition="丙是最阳"，Judgment="丙主火性"（新信息）
❌ 禁止: Condition="丙是最阳"，Judgment="丙是阳"（重复）
```

### 验证3: 是否有工程推断
```
问题: 是否把Primitive A + Primitive B组合成Judgment C？
✅ 允许: 原典明确说"A+B→C"
❌ 禁止: 原典说"A"且"B"，工程推断"A+B→C"
```

### 验证4: 是否涉及L4 Strength
```
问题: Judgment是否涉及旺/弱/强/弱/势等力量判定？
✅ 允许: 分类性Judgment（如阴阳属性）
❌ 禁止: 力量性Judgment（如旺衰判断）
```

---

## 9个Condition的Judgment潜力分析

### 分析结果：无明确Judgment授权

对于每个Condition，检查：
1. **原典是否有后续段落明确推断事件？**
2. **原典是否说出"若X成立，则Y发生"？**
3. **是否有明确的Cause-Effect关系？**

### 逐条分析

| # | Condition ID | Original Text | Judgment潜力 | 分析 |
|---|--------------|---------------|--------------|------|
| 1 | DTS-COND-006 | "五阳皆阳丙为最" | ❌ 无 | 只是定义丙的属性，无事件推断 |
| 2 | DTS-COND-010 | "五阴皆阴癸为至" | ❌ 无 | 只是定义癸的属性，无事件推断 |
| 3 | DTS-COND-002 | "五阳皆阳丙为最" | ❌ 无 | 只是分类，无事件推断 |
| 4 | DTS-COND-009 | "五阳皆阳丙为最，五阴皆阴癸为至" | ❌ 无 | 只是分类，无事件推断 |
| 5 | DTS-COND-001 | "五阳皆阳丙为最，五阴皆阴癸为至" | ❌ 无 | 只是定义，无事件推断 |
| 6 | DTS-COND-012 | "阴支静且弱" | ❌ 无 | 只是属性描述，无事件推断 |
| 7 | ZPZQ-COND-001 | "格局者，月令之提纲也" | ❌ 无 | 只是定义，无事件推断 |
| 8 | ZPZQ-COND-004 | "财官印食，何以别之？" | ❌ 无 | 只是定义，无事件推断 |
| 9 | DTS-COND-003 | "五阴皆阴癸为至" | ❌ 无 | 只是分类，无事件推断 |

---

## 初步结论

### 当前9个Condition都是"定义性"的
- 它们回答"是什么"（定性），不回答"会怎样"（定量）
- 原典没有在这些Condition基础上进一步推断事件
- **因此：没有Judgment可以授权**

### 需要扩展原典挖掘
- 从其他Primitive出发，寻找有Judgment潜力的段落
- 搜索五部经典中明确说出"若X则Y"的段落
- 例如："若成格则贵"、"若破格则贫"等

---

## 下一步执行计划

### Phase 1: 建立Judgment Schema（当前）
- [x] 定义Judgment Schema V1
- [x] 明确三层权威分离
- [ ] 创建Judgment提取规范

### Phase 2: 原典挖掘（待启动）
- [ ] 从35个Primitive中识别有Judgment潜力的条目
- [ ] 搜索五部经典中"若X则Y"结构
- [ ] 提取Judgment Candidate（非当前9个Condition）

### Phase 3: Red-Team审查（待启动）
- [ ] 检查是否把Condition组合成Judgment
- [ ] 检查是否有工程推断
- [ ] 检查是否有L4风险

### Phase 4: Claude独立审计（待启动）
- [ ] 验证原典是否真正授权Judgment
- [ ] 验证无工程推断

### Phase 5: GPT裁决（待启动）
- [ ] 最终裁决哪些Judgment进入Production

---

## 关键约束（GPT裁决明确）

### 禁止行为
```
❌ Condition成立 → 自动推断Judgment
❌ 把原典语句加工成系统预测
❌ 用工程知识补充原典没说出的Judgment
❌ 把"宜/喜"包装成"必"
❌ 跨层推导（Primitive直接→Judgment，跳过Condition）
```

### 正确流程
```
Primitive Authority（已有）
↓
Condition Authority（已有）
↓
Judgment Authority（新建，必须独立验证）
↓
GPT Final Ruling
↓
Production Judgment
```

---

## 核心原则重申

> **Condition Authority ≠ Judgment Authority**
> 
> **不能因为Condition成立，就自动推断Judgment**
> 
> **必须从原典中找到明确的"条件→结果"因果关系**
> 
> **否则只能停留在PENDING，不得进入Production**