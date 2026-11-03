# Step 6 Condition Extraction Pilot - 执行计划

**时间**: 2026-08-31  
**阶段**: Step 6启动  
**依据**: GPT裁决 71d29ed  
**状态**: 🟢 APPROVED启动

---

## 核心原则（GPT裁决明确）

### 1. 小批量Pilot验证
```
❌ 一次性提取全部35个Primitive的Condition
✅ 先提取10-20条验证Condition Mapper/Evaluator
```

### 2. 禁止自动组合
```
❌ Primitive A + Primitive B → 推导Condition C
✅ 只有原典明确说出"A + B → C"才能提取Condition C
```

### 3. 严格区分
```
Primitive: 天干有阴阳属性（事实描述）
Condition: 若天干为阳 + 月令为春 → 用丙火（条件判断）

禁止从Primitive自动推导Condition
```

---

## Pilot范围选择

### 选择标准
1. **原典明确定义Condition** - 排除建议性描述
2. **无L4风险** - 排除涉及力量比较
3. **无任注混入** - 只选ORIGINAL_TEXT
4. **无工程推断** - 排除组合推导

### Pilot候选（从35个中选10-20个）

#### 滴天髓（6个候选）
| # | Primitive ID | 名称 | 原典原文 | Condition可行性 |
|---|--------------|------|----------|----------------|
| 1 | DTS-PRIM-004 | 天干阴阳属性 | "五阳皆阳丙为最，五阴皆阴癸为至" | ✅ 可提取：若天干∈{甲丙戊庚壬}→属性=阳 |
| 2 | DTS-PRIM-008 | 五阳 | "五阳皆阳丙为最" | ✅ 可提取：若天干∈{甲丙戊庚壬}→分类=五阳 |
| 3 | DTS-PRIM-009 | 五阴 | "五阴皆阴癸为至" | ✅ 可提取：若天干∈{乙丁己辛癸}→分类=五阴 |
| 4 | DTS-PRIM-015 | 阳支 | "阳支动且强" | ✅ 可提取：若地支∈{子寅辰午申戌}→性质=阳 |
| 5 | DTS-PRIM-016 | 阴支 | "阴支静且弱" | ✅ 可提取：若地支∈{丑卯巳未酉亥}→性质=阴 |
| 6 | DTS-PRIM-010 | 丙 | "五阳皆阳丙为最" | ✅ 可提取：若天干=丙→属性=最阳 |

#### 三命通会（4个候选）
| # | Primitive ID | 名称 | 原典原文 | Condition可行性 |
|---|--------------|------|----------|----------------|
| 7 | SMTH-PRIM-001 | 甲木总论 | "甲木者..." | ⚠️ 需验证是否为定义性内容 |
| 8 | SMTH-PRIM-002 | 乙木总论 | "乙木者..." | ⚠️ 需验证是否为定义性内容 |
| 9 | SMTH-PRIM-011 | 子水总论 | "子水者..." | ⚠️ 需验证是否为定义性内容 |
| 10 | SMTH-PRIM-012 | 丑土总论 | "丑土者..." | ⚠️ 需验证是否为定义性内容 |

---

## Condition提取规范

### 允许的Condition格式
```json
{
  "condition_id": "DTS-COND-001",
  "source_primitive_id": "DTS-PRIM-004",
  "condition_logic": "IF 天干 IN {甲,丙,戊,庚,壬} THEN 阴阳属性 = 阳",
  "original_text": "五阳皆阳丙为最",
  "text_layer": "ORIGINAL_TEXT",
  "source_location": "通神论·天干篇",
  "condition_type": "DEFINITION",
  "confidence": "HIGH",
  "risk_flags": []
}
```

### 禁止的Condition格式
```json
{
  "condition_id": "INVALID-001",
  "condition_logic": "IF 天干为阳 AND 月令为春 THEN 用丙火",
  "risk_flags": ["COMBINATION_INFERENCE", "SUGGESTION包装"]
}
```
**原因**: 原典没说"必须用丙火"，只是说"宜丙火"

---

## Pilot执行流程

### Phase 1: 选择Pilot条目（当前）
- [ ] 从35个Approved Primitive中选择10-20个
- [ ] 验证每个条目的原典是否明确定义Condition
- [ ] 排除任注、建议性描述、L4风险

### Phase 2: 提取Condition（待启动）
- [ ] 对每个Pilot条目提取Condition
- [ ] 验证Condition是否忠实于原典
- [ ] 验证无工程推断

### Phase 3: Red-Team审查（待启动）
- [ ] 检查是否把描述变成判断
- [ ] 检查是否隐含Condition
- [ ] 检查是否触碰L4
- [ ] 检查是否使用任注Condition

### Phase 4: Claude独立审计（待启动）
- [ ] 验证原典是否真正授权这个Condition
- [ ] 验证Condition是否忠实于原典
- [ ] 验证无工程推断

### Phase 5: GPT裁决（待启动）
- [ ] 最终裁决哪些Condition进入Production

---

## 关键验证点

### 验证1: 原典是否明确定义Condition
```
✅ 允许: "五阳皆阳丙为最" → 若天干∈五阳→属性=阳
❌ 禁止: "甲木春月宜丙火" → 若甲木春月→必用丙火
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

---

## 输出文件

### 1. Pilot选择报告
```
docs/audit/STEP6_PILOT_SELECTION.md
```

### 2. Condition提取规范
```
docs/audit/STEP6_CONDITION_EXTRACTION_SPEC.md
```

### 3. Pilot执行结果
```
docs/audit/STEP6_PILOT_RESULT.md
```

---

## 时间线

### 当前（Phase 1）
- ⏳ 选择Pilot条目
- ⏳ 验证原典明确性

### 下一步（Phase 2-5）
- 🔲 Condition提取
- 🔲 Red-Team审查
- 🔲 Claude审计
- 🔲 GPT裁决

---

## 核心原则重申

> **Primitive → Condition 是"辨规律"的开始**
> 
> 从这里开始比Primitive层更严格
> 
> 因为要回答："原典说的这个事实，在什么条件下成立？"

**当前状态**:
- ✅ Primitive Registry Frozen（35个）
- ⏳ Step 6 Pilot启动中
- 🔴 Condition Production 🔴 HOLD（待Pilot验证）