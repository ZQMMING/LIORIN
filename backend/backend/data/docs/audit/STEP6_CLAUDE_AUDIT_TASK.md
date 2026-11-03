# Claude独立审计任务 - 12个APPROVED Condition

**时间**: 2026-08-31  
**阶段**: Phase 4 Claude独立审计  
**依据**: GPT裁决 271761f  
**状态**: 🟢 APPROVED启动

---

## 审计范围

**输入**: 12个Red-Team APPROVED Condition  
**排除**: 4个BLOCKED + 4个PENDING_CLARIFICATION（不得绕过）  
**目标**: 逐条验证原典授权、Condition忠实度、无工程推断

---

## 12个APPROVED Condition清单

### 滴天髓（6个）
| # | Condition ID | Source Primitive | Original Text | Condition Logic |
|---|--------------|------------------|---------------|-----------------|
| 1 | DTS-COND-006 | DTS-PRIM-010 | "五阳皆阳丙为最" | IF天干=丙THEN属性=最阳 |
| 2 | DTS-COND-009 | DTS-PRIM-007 | "五阳皆阳丙为最，五阴皆阴癸为至" | IF天干∈{甲丙戊庚壬}THEN阴阳分类=阳 |
| 3 | DTS-COND-010 | DTS-PRIM-011 | "五阴皆阴癸为至" | IF天干=癸THEN属性=最阴 |
| 4 | DTS-COND-012 | DTS-PRIM-018 | "阴支静且弱" | IF地支IN{丑卯巳未酉亥}THEN阴阳属性=阴 |
| 5 | ZPZQ-COND-001 | ZPZQ-PRIM-001 | "格局者，月令之提纲也" | IF月令地支IN{子丑寅卯辰巳午未申酉戌亥}THEN格局基础=月令格 |
| 6 | ZPZQ-COND-004 | ZPZQ-PRIM-007 | "财官印食，何以别之？" | IF日干所克=财AND克日干=官AND日干生=食AND生日干=印THEN十神关系=确立 |

### 子平真诠（2个）
| # | Condition ID | Source Primitive | Original Text | Condition Logic |
|---|--------------|------------------|---------------|-----------------|
| 7 | ZPZQ-COND-001 | ZPZQ-PRIM-001 | "格局者，月令之提纲也" | IF月令地支IN{子丑寅卯辰巳午未申酉戌亥}THEN格局基础=月令格 |
| 8 | ZPZQ-COND-004 | ZPZQ-PRIM-007 | "财官印食，何以别之？" | IF日干所克=财AND克日干=官AND日干生=食AND生日干=印THEN十神关系=确立 |

### 三命通会（暂缺）
- 本次Pilot未包含三命通会条目（需后续扩展）

---

## Claude审计维度

### 维度1: 原典授权验证
```
问题: 原典是否明确说出这个Condition？
✅ 允许: "五阳皆阳丙为最" → 丙是最阳
❌ 禁止: "五阳皆阳丙为最" → 若天干为五阳则必从气不从势
```

### 维度2: Condition忠实度验证
```
问题: Condition是否忠实于原典原文？
✅ 允许: IF天干=丙THEN属性=最阳（忠实）
❌ 禁止: IF天干=丙THEN必用丙火（扩大）
```

### 维度3: 工程推断检测
```
问题: 是否有Primitive组合、问句包装、定义扩大？
✅ 允许: 原典明确说"A→B"
❌ 禁止: 原典说"A"且"C"，工程组合"A+C→B+D"
```

### 维度4: L4 Strength风险检测
```
问题: 是否涉及旺/弱/强/弱/势等力量比较？
✅ 允许: 分类性定义（如阴阳）
❌ 禁止: 力量判定（如旺衰判断）
```

### 维度5: 任注混入检测
```
问题: 是否使用任注作为Condition依据？
✅ 允许: 原典原文
❌ 禁止: 任注解释作为Condition依据
```

---

## 审计输出格式

### 审计结果JSON
```json
{
  "audit_id": "CLAUDE-AUDIT-STEP6-001",
  "auditor_agent": "Claude Code CLI (sonnet)",
  "execution_method": "Claude CLI",
  "independent": true,
  "audit_date": "2026-08-31",
  "input_conditions": 12,
  "results": [
    {
      "condition_id": "DTS-COND-006",
      "verdict": "APPROVED|DENIED|PENDING_CLARIFICATION",
      "reason": "原典明确授权，无工程推断",
      "risk_flags": [],
      "original_text_verified": true,
      "condition_logic_verified": true
    }
  ],
  "summary": {
    "approved": 0,
    "denied": 0,
    "pending_clarification": 0,
    "approval_rate": "0%"
  }
}
```

---

## 执行计划

### Phase 1: 审计准备（当前）
- [x] 选择12个APPROVED Condition
- [x] 排除BLOCKED/PENDING条目
- [ ] 构建审计任务文档
- [ ] 准备原典证据材料

### Phase 2: Claude独立审计（待执行）
- [ ] 逐条审计12个Condition
- [ ] 输出审计结果
- [ ] 记录审计日志

### Phase 3: GPT最终裁决（待启动）
- [ ] 汇总Claude审计结果
- [ ] 裁决哪些Condition进入Production
- [ ] 输出Final Ruling

---

## 关键约束（GPT裁决明确）

### 禁止行为
```
❌ 绕过Red-Team直接给Claude
❌ 让BLOCKED/PENDING条目混入审计
❌ Claude自己宣布"通过"
❌ 用投票或多数决定替代独立审计
```

### 正确流程
```
Red-Team APPROVED
↓
Claude Independent Audit（独立执行）
↓
GPT Final Ruling（最终裁决）
↓
Condition Production（授权生产）
```

---

## 核心原则重申

> **Red-Team APPROVED ≠ Production Approved**
> 
> **Claude审计目的是证明：原典真正授权了这个Condition**
> 
> **不是"没发现问题"就通过，而是"有证据支持"才通过**

---

## 下一步行动

**执行Claude独立审计**：
- 使用Claude CLI（sonnet模型）
- 独立于Hermes执行
- 逐条输出审计结果
- 记录审计身份（auditor_agent + execution_method）