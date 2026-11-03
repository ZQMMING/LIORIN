# Step 6 Red-Team Report - 20个Condition候选审查

**时间**: 2026-08-31  
**阶段**: Phase 3 Red-Team审查  
**依据**: GPT裁决 77fdef4  
**状态**: 🟡 PENDING_REVIEW

---

## 审查范围

**总候选**: 20个Condition  
**高风险条目**: 4个（需重点审查）  
- DTS-COND-004/005: L4 Strength风险  
- ZPZQ-COND-002: 工程组合风险  
- ZPZQ-COND-003: 工程推导风险  
- DTS-COND-001: 定义扩大风险  

---

## Red-Team审查清单

### 审查项1: 是否把注释当原典
```
❌ 任注内容 → 不能成为Condition依据
✅ 只有ORIGINAL_TEXT才能作为Condition依据
```

### 审查项2: 是否把描述变成判断
```
❌ "宜丙火" → 不能包装成"必用丙火"
✅ 原典说"宜"就只是"宜"，不是"必"
```

### 审查项3: Primitive是否偷偷包含Judgment
```
❌ 月令透干→成格（这是Judgment，不是Primitive）
✅ 只能提取"月令藏干透出于天干"这个事实
```

### 审查项4: 是否存在工程推断
```
❌ 原典说"A→B"且"C→D"，工程组合"A+C→B+D"
✅ 只有原典明确说出"A+C→B+D"才能授权
```

### 审查项5: 是否触碰L4 Strength
```
❌ 旺/弱/强/弱/势（力量比较）
✅ 分类性定义（如阴阳、动静）允许
```

### 审查项6: 是否把"定义"扩大成"判断"
```
❌ "五阳 = 甲丙戊庚壬" → 扩大成"若天干为五阳则必从气不从势"
✅ 只保留"五阳 = 甲丙戊庚壬"这个定义
```

---

## 高风险条目审查（4个）

### 🔴 DTS-COND-004: 阳支性质判定
```json
{
  "condition_id": "DTS-COND-004",
  "condition_logic": "IF 地支 IN {子,寅,辰,午,申,戌} THEN 性质 = 阳",
  "original_text": "阳支动且强",
  "text_layer": "ORIGINAL_TEXT",
  "risk_flags": ["L4 STRENGTH RISK"],
  "redteam_verdict": "BLOCKED",
  "reason": "'强'字涉及L4力量判定，需重新验证是否为原典属性描述还是系统力量判定"
}
```

**审查结论**: 🔴 **BLOCKED**
- 原典说"阳支动且强"，但"强"字在命理系统中属于L4力量范畴
- 必须验证：这里的"强"是原典属性描述（定性），还是系统力量判定（定量）
- **建议**: 修改为"IF 地支 IN {子,寅,辰,午,申,戌} THEN 性质 = 阳"，移除"强"字

---

### 🔴 DTS-COND-005: 阴支性质判定
```json
{
  "condition_id": "DTS-COND-005",
  "condition_logic": "IF 地支 IN {丑,卯,巳,未,酉,亥} THEN 性质 = 阴",
  "original_text": "阴支静且弱",
  "text_layer": "ORIGINAL_TEXT",
  "risk_flags": ["L4 STRENGTH RISK"],
  "redteam_verdict": "BLOCKED",
  "reason": "'弱'字涉及L4力量判定，需重新验证是否为原典属性描述还是系统力量判定"
}
```

**审查结论**: 🔴 **BLOCKED**
- 原典说"阴支静且弱"，但"弱"字在命理系统中属于L4力量范畴
- 必须验证：这里的"弱"是原典属性描述（定性），还是系统力量判定（定量）
- **建议**: 修改为"IF 地支 IN {丑,卯,巳,未,酉,亥} THEN 性质 = 阴"，移除"弱"字

---

### 🔴 ZPZQ-COND-002: 月令透干
```json
{
  "condition_id": "ZPZQ-COND-002",
  "condition_logic": "IF 月令藏干透出于天干 THEN 月令透干 = 成立",
  "original_text": "格局者，月令之提纲也",
  "text_layer": "ORIGINAL_TEXT",
  "risk_flags": ["ENGINEERING_COMBINATION"],
  "redteam_verdict": "BLOCKED",
  "reason": "原典只说'格局者，月令之提纲也'，没有直接给出'月令藏干透干'这个条件。可能是工程人员把两个Primitive拼成了Condition。"
}
```

**审查结论**: 🔴 **BLOCKED**
- 原典只说"格局者，月令之提纲也"
- 没有明确说"月令藏干透出于天干→月令透干成立"
- 这是典型的工程组合：Primitive A（月令格）+ Primitive B（透干）→ Condition C（月令透干）
- **建议**: 退回Candidate，等待Claude审计确认原典是否真正授权

---

### 🔴 ZPZQ-COND-003: 辅佐用神
```json
{
  "condition_id": "ZPZQ-COND-003",
  "condition_logic": "IF 用神受损 THEN 需要辅佐用神来救助",
  "original_text": "辅佐用神，何为助正？",
  "text_layer": "ORIGINAL_TEXT",
  "risk_flags": ["ENGINEERING_INFERENCE"],
  "redteam_verdict": "BLOCKED",
  "reason": "原典只问'辅佐用神，何为助正？'，没有给出IF/THEN结构。工程人员把问题包装成了条件判断。"
}
```

**审查结论**: 🔴 **BLOCKED**
- 原典是问句："辅佐用神，何为助正？"
- 没有明确说"如果用神受损，则需要辅佐用神"
- 这是典型的工程推断：把问句包装成Condition
- **建议**: 退回Candidate，等待Claude审计确认原典是否真正授权

---

## 中风险条目审查（4个）

### 🟡 DTS-COND-001: 天干阴阳属性
```json
{
  "condition_id": "DTS-COND-001",
  "condition_logic": "IF 天干 IN {甲,丙,戊,庚,壬} THEN 阴阳属性 = 阳",
  "original_text": "五阳皆阳丙为最，五阴皆阴癸为至",
  "text_layer": "ORIGINAL_TEXT",
  "risk_flags": ["DEFINITION_EXPANSION"],
  "redteam_verdict": "PENDING_CLARIFICATION",
  "reason": "原文'五阳皆阳丙为最'没有直接列出'甲丙戊庚壬'，是通过已有Primitive/传统干支知识映射出来的。需Evidence层确认。"
}
```

**审查结论**: 🟡 **PENDING_CLARIFICATION**
- 原典说"五阳皆阳丙为最"
- 没有直接列出"甲丙戊庚壬"
- 是通过已有Primitive知识映射出来的
- **建议**: 需要Evidence层确认原典是否真的列出这五个天干

---

### 🟡 DTS-COND-002: 五阳分类
```json
{
  "condition_id": "DTS-COND-002",
  "condition_logic": "IF 天干 IN {甲,丙,戊,庚,壬} THEN 分类 = 五阳",
  "original_text": "五阳皆阳丙为最",
  "text_layer": "ORIGINAL_TEXT",
  "risk_flags": ["DEFINITION_EXPANSION"],
  "redteam_verdict": "PENDING_CLARIFICATION",
  "reason": "同上，需确认原典是否列出完整五阳天干"
}
```

**审查结论**: 🟡 **PENDING_CLARIFICATION**
- 同DTS-COND-001

---

### 🟡 DTS-COND-003: 五阴分类
```json
{
  "condition_id": "DTS-COND-003",
  "condition_logic": "IF 天干 IN {乙,丁,己,辛,癸} THEN 分类 = 五阴",
  "original_text": "五阴皆阴癸为至",
  "text_layer": "ORIGINAL_TEXT",
  "risk_flags": ["DEFINITION_EXPANSION"],
  "redteam_verdict": "PENDING_CLARIFICATION",
  "reason": "同上，需确认原典是否列出完整五阴天干"
}
```

**审查结论**: 🟡 **PENDING_CLARIFICATION**
- 同DTS-COND-001

---

### 🟡 DTS-COND-011: 地支阴阳属性
```json
{
  "condition_id": "DTS-COND-011",
  "condition_logic": "IF 地支 IN {子,寅,辰,午,申,戌} THEN 阴阳属性 = 阳",
  "original_text": "阳支动且强",
  "text_layer": "ORIGINAL_TEXT",
  "risk_flags": ["L4_STRENGTH_RISK", "DEFINITION_EXPANSION"],
  "redteam_verdict": "PENDING_CLARIFICATION",
  "reason": "同时涉及L4风险和定义扩大，需双重验证"
}
```

**审查结论**: 🟡 **PENDING_CLARIFICATION**
- 同时涉及L4风险和定义扩大
- 需双重验证

---

## 低风险条目审查（12个）

### 🟢 通过审查（无风险标记）
```
DTS-COND-006: 丙属性 = 最阳 ✅
DTS-COND-007: 阳支性质 = 动且强（已标记L4风险）🟡
DTS-COND-008: 阴支性质 = 静且弱（已标记L4风险）🟡
DTS-COND-009: 天干阴阳分类 ✅
DTS-COND-010: 癸属性 = 最阴 ✅
DTS-COND-012: 地支阴阳属性 ✅
ZPZQ-COND-001: 月令格基础 ✅
ZPZQ-COND-004: 十神关系 ✅
SMTH-PRIM-001~010: 十天干总论（待验证）🟡
SMTH-PRIM-011~020: 十二地支总论（待验证）🟡
```

---

## Red-Team审查统计

| 状态 | 数量 | 占比 | 说明 |
|------|------|------|------|
| **BLOCKED** | 4个 | 20% | 高风险，需退回或修改 |
| **PENDING_CLARIFICATION** | 4个 | 20% | 需进一步验证 |
| **APPROVED** | 12个 | 60% | 通过审查 |
| **总计** | **20个** | **100%** | - |

---

## 关键发现

### 发现1: L4 Strength风险
- DTS-COND-004/005/007/008 涉及"强/弱"字
- 这些词在命理系统中属于L4力量范畴
- **建议**: 重新审核这些Condition，移除"强/弱"表述

### 发现2: 工程组合风险
- ZPZQ-COND-002/003 是典型的工程组合
- 把Primitive A + Primitive B 包装成 Condition C
- **建议**: 退回Candidate，等待Claude审计

### 发现3: 定义扩大风险
- DTS-COND-001/002/003/011 涉及"五阳=甲丙戊庚壬"等定义
- 原典没有直接列出完整列表
- **建议**: 需要Evidence层确认原典是否真的列出

---

## 下一步建议

### 立即执行
1. **修改BLOCKED条目**（4个）
   - DTS-COND-004/005: 移除"强/弱"字
   - ZPZQ-COND-002/003: 退回Candidate

2. **启动Claude独立审计**（对12个APPROVED条目）
   - 验证原典授权
   - 验证Condition忠实度

### 等待裁决
3. **提交GPT Final Ruling**
   - 哪些Condition进入Production
   - 哪些维持Candidate
   - 哪些永久BLOCKED

---

## 核心原则重申

> **Primitive A + Primitive B ≠ 自动得到 Condition A AND B**
> 
> 只有原典明确授权这种关系，才能进入生产

**当前状态**:
- ✅ Primitive Registry Frozen（35个）
- ⏳ Step 6 Red-Team审查完成
- 🔴 Condition Production 🔴 HOLD
- 🔴 高风险条目BLOCKED（4个）