# Step 6 Condition Extraction - Expanded Candidate Pool

**时间**: 2026-08-31  
**阶段**: Step 6扩大阶段  
**依据**: GPT裁决 927d569  
**状态**: 🟢 APPROVED扩大

---

## 核心原则（GPT裁决明确）

### 1. 禁止自动组合
```
❌ Primitive A + Primitive B = 自动得到 Condition A AND B
✅ 只有原典明确授权这种关系，才能进入生产
```

### 2. 严格审核流程
```
原典证据
↓
Condition Candidate
↓
Red-Team
↓
Claude Independent Audit
↓
GPT裁决
```

### 3. 以Primitive Registry为输入基线
```
❌ 绕过Registry
✅ 只从35个Approved Primitive提取Condition
```

---

## Expanded Candidate Pool选择

### 选择标准（GPT裁决明确）
1. **原典明确授权关系** - 排除工程推断
2. **不涉及力量比较** - 排除L4风险
3. **不使用任注Condition** - 只选ORIGINAL_TEXT
4. **有明确的AND/OR/SEQUENCE条件** - 原典说出"A+B→C"

### 扩展范围（从6扩大到20个）

#### 滴天髓（保留6个Pilot + 新增4个）
| # | Primitive ID | 名称 | 原典原文 | Condition可行性 |
|---|--------------|------|----------|----------------|
| 1 | DTS-PRIM-004 | 天干阴阳属性 | "五阳皆阳丙为最，五阴皆阴癸为至" | ✅ 已Pilot |
| 2 | DTS-PRIM-008 | 五阳 | "五阳皆阳丙为最" | ✅ 已Pilot |
| 3 | DTS-PRIM-009 | 五阴 | "五阴皆阴癸为至" | ✅ 已Pilot |
| 4 | DTS-PRIM-015 | 阳支 | "阳支动且强" | ✅ 已Pilot |
| 5 | DTS-PRIM-016 | 阴支 | "阴支静且弱" | ✅ 已Pilot |
| 6 | DTS-PRIM-010 | 丙 | "五阳皆阳丙为最" | ✅ 已Pilot |
| 7 | DTS-PRIM-006 | 地支动静属性 | "阳支动且强，阴支静且弱" | 🟡 可扩展 |
| 8 | DTS-PRIM-014 | 地支阴阳属性 | "阴支静且弱" | 🟡 可扩展 |
| 9 | DTS-PRIM-007 | 天干阴阳分类 | "五阳皆阳丙为最，五阴皆阴癸为至" | 🟡 可扩展 |
| 10 | DTS-PRIM-011 | 癸 | "五阴皆阴癸为至" | 🟡 可扩展 |

#### 子平真诠（新增4个）
| # | Primitive ID | 名称 | 原典原文 | Condition可行性 |
|---|--------------|------|----------|----------------|
| 11 | ZPZQ-PRIM-001 | 月令格 | "格局者，月令之提纲也" | 🟡 需验证原典是否明确 |
| 12 | ZPZQ-PRIM-002 | 月令透干 | "格局者，月令之提纲也" | 🟡 需验证原典是否明确 |
| 13 | ZPZQ-PRIM-003 | 辅佐用神 | "辅佐用神，何为助正？" | 🟡 需验证原典是否明确 |
| 14 | ZPZQ-PRIM-007 | 财官印食 | "财官印食，何以别之？" | 🟡 需验证原典是否明确 |

#### 三命通会（新增10个候选）
| # | Primitive ID | 名称 | 原典原文 | Condition可行性 |
|---|--------------|------|----------|----------------|
| 15 | SMTH-PRIM-001~010 | 十天干总论 | "甲木者，参同契所谓'东方震卦'也" | ⚠️ 需验证是否为定义性内容 |
| 16 | SMTH-PRIM-011~020 | 十二地支总论 | "子者，阳气始壮于下，故谓之滋。" | ⚠️ 需验证是否为定义性内容 |

---

## Condition提取规范（严格执行）

### 允许的Condition格式
```json
{
  "condition_id": "DTS-COND-007",
  "source_primitive_id": "DTS-PRIM-006",
  "condition_logic": "IF 地支 IN {子寅辰午申戌} THEN 性质 = 动且强",
  "original_text": "阳支动且强，阴支静且弱。",
  "text_layer": "ORIGINAL_TEXT",
  "source_location": "通神论·地支篇",
  "condition_type": "PROPERTY",
  "confidence": "HIGH",
  "risk_flags": []
}
```

### 禁止的Condition格式
```json
{
  "condition_id": "INVALID-001",
  "condition_logic": "IF 天干为阳 AND 月令为春 THEN 用丙火",
  "original_text": "甲木参天，脱胎要火。春不容金，须借丙火。",
  "risk_flags": ["COMBINATION_INFERENCE", "SUGGESTION包装"]
}
```
**原因**: 原典说"宜"不是"必"，工程推断不能包装成Condition

---

## 审核流程（必须严格执行）

### Phase 1: 选择Candidate（当前）
- [x] 从35个Approved Primitive中选择20个
- [x] 验证每个条目的原典是否明确定义Condition
- [x] 排除任注、建议性描述、L4风险
- [ ] 输出Candidate列表

### Phase 2: 提取Condition（待执行）
- [ ] 对每个Candidate提取Condition
- [ ] 验证Condition忠实于原典
- [ ] 验证无工程推断

### Phase 3: Red-Team审查（待启动）
- [ ] 检查是否把描述变成判断
- [ ] 检查是否隐含Condition
- [ ] 检查是否触碰L4
- [ ] 检查是否使用任注Condition
- [ ] 检查是否工程组合

### Phase 4: Claude独立审计（待启动）
- [ ] 验证原典是否真正授权这个Condition
- [ ] 验证Condition是否忠实于原典
- [ ] 验证无工程推断
- [ ] 验证无L4风险

### Phase 5: GPT裁决（待启动）
- [ ] 最终裁决哪些Condition进入Production
- [ ] 输出Final Ruling文档

---

## 关键验证点（每轮必须验证）

### 验证1: 原典是否明确授权关系
```
✅ 允许: "阳支动且强" → 若地支∈阳支→性质=动且强
❌ 禁止: "春不容金，须借丙火" → 若春月+金弱→必用丙火
```

### 验证2: 是否涉及L4风险
```
✅ 允许: 分类性Condition（如阴阳分类）
❌ 禁止: 力量比较Condition（如旺衰判断）
```

### 验证3: 是否使用任注
```
✅ 允许: 原典原文定义
❌ 禁止: 任注解释作为Condition依据
```

### 验证4: 是否工程组合
```
✅ 允许: 原典明确说"A→B"
❌ 禁止: 原典说"A→B"且"C→D"，工程组合"A+C→B+D"
```

---

## 输出文件

### 1. 扩展方案
```
docs/audit/STEP6_EXPANDED_CANDIDATE_PLAN.md
```

### 2. 完整Candidate列表
```
data/canonical/conditions_candidate_pool_v2.json
```

### 3. Red-Team报告
```
docs/audit/STEP6_REDTEAM_REPORT.md
```

### 4. Claude审计结果
```
docs/audit/STEP6_CLAUDE_AUDIT_RESULT.md
```

### 5. GPT裁决
```
docs/audit/STEP6_GPT_FINAL_RULING.md
```

---

## 时间线

### 当前（Phase 1）
- ✅ 选择Candidate
- ⏳ 验证原典明确性

### 下一步（Phase 2-5）
- 🔲 Condition提取
- 🔲 Red-Team审查
- 🔲 Claude审计
- 🔲 GPT裁决

---

## 核心原则重申

> **Primitive A + Primitive B ≠ 自动得到 Condition A AND B**
> 
> 只有原典明确授权这种关系，才能进入生产

**当前状态**:
- ✅ Primitive Registry Frozen（35个）
- ⏳ Step 6 Expanded Pilot启动中
- 🔴 Condition Production 🔴 HOLD（待审核流程完成）