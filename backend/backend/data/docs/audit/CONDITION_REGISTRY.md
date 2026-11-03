# Condition Registry - 9个Authorized Condition正式注册

**时间**: 2026-08-31  
**阶段**: Step 6完成 → Step 7准备  
**依据**: GPT裁决 12a66b4  
**状态**: 🟢 APPROVED注册

---

## Registry定义

### 什么是Condition Registry？
> 9个GPT最终授权的Condition，进入**生产可用**状态。
> 每个Condition都有完整的：原典授权 → 工程忠实度 → 无L4风险 → 无工程推断验证。

---

## 9个Authorized Condition清单

| # | Condition ID | Source Primitive | Original Text | Condition Logic | Authorization Date |
|---|--------------|------------------|---------------|-----------------|-------------------|
| 1 | DTS-COND-006 | DTS-PRIM-010 | "五阳皆阳丙为最" | IF天干=丙THEN属性=最阳 | 2026-08-31 |
| 2 | DTS-COND-010 | DTS-PRIM-011 | "五阴皆阴癸为至" | IF天干=癸THEN属性=最阴 | 2026-08-31 |
| 3 | DTS-COND-002 | DTS-PRIM-008 | "五阳皆阳丙为最" | IF天干IN{甲丙戊庚壬}THEN分类=五阳 | 2026-08-31 |
| 4 | DTS-COND-009 | DTS-PRIM-007 | "五阳皆阳丙为最，五阴皆阴癸为至" | IF天干IN{甲丙戊庚壬}THEN阴阳分类=阳 | 2026-08-31 |
| 5 | DTS-COND-001 | DTS-PRIM-004 | "五阳皆阳丙为最，五阴皆阴癸为至" | IF天干IN{甲丙戊庚壬}THEN属性=阳 | 2026-08-31 |
| 6 | DTS-COND-012 | DTS-PRIM-018 | "阴支静且弱" | IF地支IN{丑卯巳未酉亥}THEN属性=阴 | 2026-08-31 |
| 7 | ZPZQ-COND-001 | ZPZQ-PRIM-001 | "格局者，月令之提纲也" | IF月令地支IN{十二地支}THEN格局基础=月令格 | 2026-08-31 |
| 8 | ZPZQ-COND-004 | ZPZQ-PRIM-007 | "财官印食，何以别之？" | IF日干所克=财AND...THEN十神关系=确立 | 2026-08-31 |
| 9 | DTS-COND-003 | DTS-PRIM-009 | "五阴皆阴癸为至" | IF天干IN{乙丁己辛癸}THEN分类=五阴 | 2026-08-31 |

---

## Condition vs Judgment严格区分

### Condition（当前阶段已批准）
```
作用: 判断事实条件是否成立
示例: IF天干=丙THEN属性=最阳
性质: 事实描述，原典明确定义
边界: 只回答"是什么"，不回答"因此会怎样"
```

### Judgment（下一阶段）
```
作用: 推断命理事件结论
示例: IF成格THEN主贵
性质: 预测判断，需原典明确授权
边界: 必须从原典证据推导，不能从Condition自动组合
```

### 关键禁令
```
❌ Condition A + Condition B → 自动产生 Judgment C
✅ 只有原典明确说"A + B → C"才能产生 Judgment C
```

---

## Registry数据格式

```json
{
  "condition_id": "DTS-COND-006",
  "source_primitive_id": "DTS-PRIM-010",
  "original_text": "五阳皆阳丙为最",
  "condition_logic": "IF天干=丙THEN属性=最阳",
  "text_layer": "ORIGINAL_TEXT",
  "source_location": "通神论·天干篇",
  "condition_type": "PROPERTY",
  "confidence": "HIGH",
  "authorization_chain": {
    "claude_audit": "APPROVED",
    "redteam_review": "APPROVED",
    "gpt_finalization": "APPROVED",
    "finalization_date": "2026-08-31",
    "gpt_ruling_id": "12a66b4"
  },
  "risk_flags": [],
  "provenance": {
    "parent_candidate_id": "CAND-DTS-010",
    "derived_condition_ids": ["DTS-COND-006"],
    "derivation_reason": "从CAND-DTS-010提取：原典明确授权丙是最阳"
  },
  "status": "AUTHORIZED",
  "production_authorization": "CONDITION_ONLY",
  "judgment_authorization": "NOT_AUTHORIZED"
}
```

---

## 核心原则（GPT裁决明确）

> **Primitive → Condition → Judgment 是严格分层**
> 
> **Condition只负责：判断事实条件是否成立**
> 
> **Condition不负责：推断命理事件结论**
> 
> **Condition成立 ≠ 原典一定授权某个Judgment**

---

## 下一步：Judgment Pilot

### 授权条件
```
9 Authorized Conditions → 提取原典明确的Judgment → Red-Team → Claude Audit → GPT Ruling
```

### 执行步骤
1. **从9个Condition中提取Judgment候选**
   - 只选原典明确说出的Judgment
   - 排除工程推断的Judgment

2. **Red-Team审查**
   - 检查是否把"条件成立"包装成"事件结论"
   - 检查是否有Primitive组合推导Judgment

3. **Claude独立审计**
   - 验证原典是否真正授权Judgment
   - 验证无工程推断

4. **GPT最终裁决**
   - 裁决哪些Judgment进入Production

### 关键验证点
```
✅ 允许: 原典明确说"若X则Y" → Judgment: 若X成立则Y发生
❌ 禁止: Condition X + Condition Y → 工程推断Z发生
```

---

## 时间线

### 当前（Step 6完成）
- ✅ Primitive Registry Frozen（35个）
- ✅ Condition Registry Authorized（9个）
- ✅ Step 6 Pipeline完成

### 下一步（Step 7启动）
- 🔲 Judgment Pilot启动
- 🔲 从9个Condition提取Judgment候选
- 🔲 Red-Team审查
- 🔲 Claude独立审计
- 🔲 GPT最终裁决

---

## 里程碑意义

> **"算 → 辨 → 解"正式进入"辨"**
> 
> Primitive = 算（计算基础概念）
> Condition = 辨（辨别条件是否成立）
> Judgment = 解（解释命理事件）

**当前阶段**: 已完成"算"和"辨"的第一层  
**下一阶段**: 开始"辨"的第二层（Judgment提取）