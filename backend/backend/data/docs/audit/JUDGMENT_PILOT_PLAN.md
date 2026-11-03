# Judgment Pilot - 执行计划

**时间**: 2026-08-31  
**阶段**: Step 7 Judgment Extraction启动  
**依据**: GPT裁决 12a66b4  
**状态**: 🟢 APPROVED启动

---

## 核心原则（GPT裁决明确）

> **Condition成立 ≠ 原典一定授权某个Judgment**
> 
> **不能因为A成立 + B成立就自动生成→ 主财 / 主官 / 主灾**
> 
> **只有原典明确给出对应判断，才能进入Judgment Production**

---

## Judgment提取规范

### 允许的Judgment格式
```json
{
  "judgment_id": "DTS-JUDG-001",
  "source_condition_ids": ["DTS-COND-006"],
  "judgment_logic": "IF天干=丙THEN丙为最阳（这是条件，不是Judgment）",
  "original_text": "五阳皆阳丙为最",
  "text_layer": "ORIGINAL_TEXT",
  "source_location": "通神论·天干篇",
  "judgment_type": "PROPERTY_STATEMENT",
  "confidence": "HIGH",
  "risk_flags": []
}
```

**关键**: 这实际上是Condition，不是Judgment。真正的Judgment应该回答"因此会发生什么"。

### 禁止的Judgment格式
```json
{
  "judgment_id": "INVALID-001",
  "source_condition_ids": ["DTS-COND-006", "DTS-COND-010"],
  "judgment_logic": "IF天干=丙AND天干=癸THEN命主贵显",
  "original_text": "（无原典支持）",
  "risk_flags": ["ENGINEERING_COMBINATION", "UNAUTHORIZED_JUDGMENT"]
}
```
**原因**: 原典没有说"丙+癸→贵显"，这是工程组合推导

---

## 从9个Condition提取Judgment候选

### 分析策略

对于每个Condition，检查：
1. **原典是否在该Condition基础上进一步推断？**
2. **原典是否说出"若X成立，则Y事件发生"？**
3. **是否有明确的Cause-Effect关系？**

### 9个Condition的Judgment潜力评估

| # | Condition ID | Original Text | Judgment潜力 | 评估 |
|---|--------------|---------------|--------------|------|
| 1 | DTS-COND-006 | "五阳皆阳丙为最" | 低 | 只是定义丙的属性，无事件推断 |
| 2 | DTS-COND-010 | "五阴皆阴癸为至" | 低 | 只是定义癸的属性，无事件推断 |
| 3 | DTS-COND-002 | "五阳皆阳丙为最" | 低 | 只是分类，无事件推断 |
| 4 | DTS-COND-009 | "五阳皆阳丙为最，五阴皆阴癸为至" | 低 | 只是分类，无事件推断 |
| 5 | DTS-COND-001 | "五阳皆阳丙为最，五阴皆阴癸为至" | 低 | 只是定义，无事件推断 |
| 6 | DTS-COND-012 | "阴支静且弱" | 中 | "静且弱"可能隐含事件倾向，但原典未明确 |
| 7 | ZPZQ-COND-001 | "格局者，月令之提纲也" | 中 | 月令格定义，但未说"成格则贵" |
| 8 | ZPZQ-COND-004 | "财官印食，何以别之？" | 低 | 只是定义十神，无事件推断 |
| 9 | DTS-COND-003 | "五阴皆阴癸为至" | 低 | 只是分类，无事件推断 |

---

## 初步结论

### 当前9个Condition大多数是"定义性"的
- 它们回答"是什么"（定性），不回答"会怎样"（定量）
- 这些是Primitive级别的Condition，不是Judgment级别的Condition

### Judgment提取需要更多原典证据
- 需要从其他原典段落提取真正的Judgment
- 例如："若成格则贵"、"若破格则贫"等

### 建议下一步
1. **扩展Condition Pool**: 从35个Primitive中找到有Judgment潜力的条目
2. **原典挖掘**: 搜索五部经典中明确说出"若X则Y"的段落
3. **Judgment Candidate提取**: 基于原典明确授权的Judgment

---

## 执行流程

### Phase 1: 扩展分析（当前）
- [x] 建立Condition Registry（9个）
- [x] 分析9个Condition的Judgment潜力
- [ ] 识别有Judgment潜力的Condition

### Phase 2: 原典挖掘（待启动）
- [ ] 搜索五部经典中"若X则Y"结构
- [ ] 提取Judgment Candidate
- [ ] 建立Judgment Candidate Pool

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
❌ Condition A + Condition B → 自动产生 Judgment C
❌ 从Condition推导"主财/主官/主灾"
❌ 用工程知识补充原典没说出的Judgment
❌ 把"宜/喜"包装成"必"
```

### 正确流程
```
原典明确说"若X则Y"
↓
Judgment Candidate
↓
Red-Team
↓
Claude Independent Audit
↓
GPT裁决
↓
Judgment Production
```

---

## 输出文件

1. `docs/audit/JUDGMENT_PILOT_PLAN.md` - 本文件
2. `data/canonical/judgment_candidate_pool.json` - Judgment候选池
3. `docs/audit/JUDGMENT_REDTTEAM_REPORT.md` - Red-Team报告
4. `docs/audit/CLAUDE_AUDIT_JUDGMENT_RESULT.md` - Claude审计结果
5. `docs/audit/GPT_RULING_JUDGMENT_FINAL.md` - GPT最终裁决

---

## 里程碑意义

> **"算 → 辨 → 解"正式进入"辨"**
> 
> Primitive = 算（计算基础概念）✅ 完成  
> Condition = 辨第一层（辨别条件是否成立）✅ 完成  
> Judgment = 辨第二层（辨别命理事件）🔄 启动  
> Production = 解（最终解释输出）🔴 待启动

**当前阶段**: 已完成"算"和"辨"的第一层  
**下一阶段**: 开始"辨"的第二层（Judgment提取）