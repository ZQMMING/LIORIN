# Step 2 Primitive Extraction - 《滴天髓·通神论》

**时间**: 2026-08-31  
**阶段**: M3 Phase 3.1-R Step 2  
**依据**: GPT裁决 b7bc424  
**状态**: 🟢 APPROVED启动

---

## Step 2核心限制（GPT裁决明确）

### ✅ Primitive可以回答：
> "原典明确描述了什么最小语义事实？"

### ❌ Primitive不能回答：
> "根据这些事实，我们认为应该怎样判断。"

### 示例对比
```
✅ 可以提取：日主、月令、透干、根、天干五合、地支六合
❌ 不能提取：透干+得令→成格（这是Condition/Judgment）
```

---

## 输出格式要求

每个Primitive必须追溯：
```json
{
  "primitive_id": "DTS-PRIM-XXX",
  "original_text": "原典原文引用",
  "text_layer": "ORIGINAL_TEXT | ORIGINAL_COMMENTARY | LATER_COMMENTARY",
  "source_location": "章节位置",
  "semantic_definition": "语义定义",
  "canonical_state_mapping": "UNRESOLVED | CANONICAL | PARTIAL"
}
```

### Canonical State Mapping规则
- **CANONICAL**: Canonical State可以明确表达
- **PARTIAL**: 部分可表达，需要补充定义
- **UNRESOLVED**: 无法证明Canonical State能表达，禁止进入生产

---

## 禁止事项（GPT裁决明确）

🔴 **禁止提取以下概念作为Primitive**：
- 成格
- 破格
- 从格
- 化气成功
- 救应成功
- 旺/弱（这是Judgment，不是Primitive）
- 势（这是L4力量问题）
- 主某事（这是Judgment）

---

## 提取范围

**只处理《滴天髓·通神论》**，不扩大到006-020，不进入其他四书。

---

## 执行步骤

### Step 2.1: 逐句扫描《通神论》全文
对每个句子：
1. 识别最小语义单元
2. 判断是否为"事实描述"而非"条件判断"
3. 标注原文位置和text_layer
4. 验证Canonical State可表达性

### Step 2.2: 提取Primitive候选
只提取：
- 实体（日主、月令、天干、地支）
- 关系（相生、相克、相合、相冲）
- 属性（阴阳、五行、十神）
- 状态（透干、通根、得令）

### Step 2.3: 验证Primitive真实性
对每个候选Primitive：
1. 回原典确认是否明确描述
2. 检查是否涉及条件判断
3. 检查是否涉及力量比较
4. 检查是否涉及格局判定

### Step 2.4: 生成Primitive库
输出：
- `data/canonical/primitives.json` - Primitive库
- `docs/audit/STEP2_PRIMITIVE_EXTRACTION.md` - 提取报告

---

## 开始提取

### 第一章：天道
```
原文：欲识三元万法宗，先观帝载与神功。
任注：三元者，天干也。帝载者，天道也。神功者，地道也。

语义单元：
- 三元 = 天干（任注明确定义）
- 帝载 = 天道（任注明确定义）
- 神功 = 地道（任注明确定义）

Primitive提取：
✅ DTS-PRIM-001: 三元（天干）
   - original_text: "欲识三元万法宗，先观帝载与神功"
   - text_layer: ORIGINAL_COMMENTARY（任注定义）
   - semantic_definition: 十天干
   - canonical_state_mapping: CANONICAL

✅ DTS-PRIM-002: 帝载（天道）
   - original_text: "欲识三元万法宗，先观帝载与神功"
   - text_layer: ORIGINAL_COMMENTARY（任注定义）
   - semantic_definition: 天道（时间循环）
   - canonical_state_mapping: PARTIAL（需要补充定义）

✅ DTS-PRIM-003: 神功（地道）
   - original_text: "欲识三元万法宗，先观帝载与神功"
   - text_layer: ORIGINAL_COMMENTARY（任注定义）
   - semantic_definition: 地道（空间方位）
   - canonical_state_mapping: PARTIAL（需要补充定义）
```

### 第二章：地道
```
原文：坤元合德机缄通，五气偏全定吉凶。
任注：坤元者，地势也。五气者，五行也。偏全者，得偏得全也。

语义单元：
- 坤元 = 地势（任注明确定义）
- 五气 = 五行（任注明确定义）
- 偏全 = 得偏得全（任注定义，但抽象）

Primitive提取：
✅ DTS-PRIM-004: 坤元（地势）
   - original_text: "坤元合德机缄通，五气偏全定吉凶"
   - text_layer: ORIGINAL_COMMENTARY（任注定义）
   - semantic_definition: 地势（空间基础）
   - canonical_state_mapping: PARTIAL

⚠️ DTS-PRIM-005: 五气（五行）
   - original_text: "坤元合德机缄通，五气偏全定吉凶"
   - text_layer: ORIGINAL_COMMENTARY（任注定义）
   - semantic_definition: 五行（木火土金水）
   - canonical_state_mapping: CANONICAL
   - 注意：不是"五气偏全"，只是"五气"
   - "偏全"是后续Condition，不是Primitive

❌ 不提取：偏全
   - 原因：这是Condition概念，不是Primitive
   - 任注说"得偏得全"，但这是抽象描述
   - 需要先定义什么是"偏"、什么是"全"
```

### 第三章：人道
```
原文：戴天履地人为贵，顺则吉兮凶则悖。
任注：人禀天地之气以生，故人为贵。顺者，顺天地之气也。

语义单元：
- 人为贵（属性陈述）
- 顺/悖（状态描述）
- 天地之气（概念）

Primitive提取：
⚠️ DTS-PRIM-006: 人（日主）
   - original_text: "戴天履地人为贵"
   - text_layer: ORIGINAL_TEXT
   - semantic_definition: 出生时刻的天干（日主）
   - canonical_state_mapping: CANONICAL
   - 注意：原典没说"日主"，这是现代术语
   - 但"人"在原典中确实指日主

❌ 不提取：贵/贱
   - 原因：这是Judgment，不是Primitive
   - "人为贵"是属性陈述，不是判断条件

❌ 不提取：顺/悖
   - 原因：这是Condition概念
   - 原典没说如何判断"顺"或"悖"
   - 任注也只说"顺天地之气"，未定义判断标准
```

### 第七章：天干（重点）
```
原文：五阳皆阳丙为最，五阴皆阴癸为至。
任注：丙火纯阳，癸水纯阴，皆其至极者也。

语义单元：
- 五阳：甲丙戊庚壬
- 五阴：乙丁己辛癸
- 丙为最：丙是五阳中最阳的
- 癸为至：癸是五阴中最阴的

Primitive提取：
✅ DTS-PRIM-007: 天干阴阳属性
   - original_text: "五阳皆阳丙为最，五阴皆阴癸为至"
   - text_layer: ORIGINAL_TEXT
   - semantic_definition: 十天干分为阴阳两组
   - canonical_state_mapping: CANONICAL

✅ DTS-PRIM-008: 五阳（天干组）
   - original_text: "五阳皆阳丙为最"
   - text_layer: ORIGINAL_TEXT
   - semantic_definition: 甲丙戊庚壬
   - canonical_state_mapping: CANONICAL

✅ DTS-PRIM-009: 五阴（天干组）
   - original_text: "五阴皆阴癸为至"
   - text_layer: ORIGINAL_TEXT
   - semantic_definition: 乙丁己辛癸
   - canonical_state_mapping: CANONICAL

✅ DTS-PRIM-010: 丙（最阳天干）
   - original_text: "五阳皆阳丙为最"
   - text_layer: ORIGINAL_TEXT + ORIGINAL_COMMENTARY
   - semantic_definition: 丙火，纯阳之极
   - canonical_state_mapping: CANONICAL

✅ DTS-PRIM-011: 癸（最阴天干）
   - original_text: "五阴皆阴癸为至"
   - text_layer: ORIGINAL_TEXT + ORIGINAL_COMMENTARY
   - semantic_definition: 癸水，纯阴之极
   - canonical_state_mapping: CANONICAL
```

### 第七章：天干（核心）
```
原文：五阳从气不从势，五阴从势无情义。
任注：五阳得阳之气，即能成乎阳刚之势，不畏财杀之势；五阴得阴之气，即能成乎阴顺之义...

语义单元：
- 五阳：甲丙戊庚壬
- 五阴：乙丁己辛癸
- 从气：顺从气的方向
- 从势：顺从势的方向
- 气：原典未明确定义
- 势：原典未明确定义

Primitive提取：
✅ DTS-PRIM-012: 从气（倾向性）
   - original_text: "五阳从气不从势"
   - text_layer: ORIGINAL_TEXT
   - semantic_definition: 五阳干的倾向性特征
   - canonical_state_mapping: UNRESOLVED
   - 原因："气"的定义不明确，无法建立Canonical映射

⚠️ DTS-PRIM-013: 从势（倾向性）
   - original_text: "五阴从势无情义"
   - text_layer: ORIGINAL_TEXT
   - semantic_definition: 五阴干的倾向性特征
   - canonical_state_mapping: UNRESOLVED
   - 原因："势"的定义不明确，无法建立Canonical映射

❌ 不提取：阳气盛
   - 原因：GPT裁决明确质疑，原典未授权此Condition
   - 任注补充了"得阳之气"，但不是明确定义
   - 这是工程推断，不是Primitive

❌ 不提取：从格
   - 原因：这是Judgment，不是Primitive
   - 原典说"从气/从势"，是倾向性描述
   - 不是说"成格"
```

### 第八章：地支
```
原文：阳支动且强，速达显灾祥。阴支静且专，否泰每经年。
任注：阳支子寅辰午申戌，其性动，其势强；阴支丑卯巳未酉亥，其性静，其气专。

语义单元：
- 阳支：子寅辰午申戌
- 阴支：丑卯巳未酉亥
- 动/强：阳支属性
- 静/专：阴支属性

Primitive提取：
✅ DTS-PRIM-014: 地支阴阳属性
   - original_text: "阳支动且强，速达显灾祥。阴支静且专，否泰每经年"
   - text_layer: ORIGINAL_TEXT
   - semantic_definition: 十二地支分为阴阳两组
   - canonical_state_mapping: CANONICAL

✅ DTS-PRIM-015: 阳支（地支组）
   - original_text: "阳支动且强"
   - text_layer: ORIGINAL_TEXT + ORIGINAL_COMMENTARY
   - semantic_definition: 子寅辰午申戌
   - canonical_state_mapping: CANONICAL

✅ DTS-PRIM-016: 阴支（地支组）
   - original_text: "阴支静且专"
   - text_layer: ORIGINAL_TEXT + ORIGINAL_COMMENTARY
   - semantic_definition: 丑卯巳未酉亥
   - canonical_state_mapping: CANONICAL

✅ DTS-PRIM-017: 动（阳支属性）
   - original_text: "阳支动且强"
   - text_layer: ORIGINAL_TEXT
   - semantic_definition: 阳支的特性：主动
   - canonical_state_mapping: PARTIAL（需要补充定义）

✅ DTS-PRIM-018: 静（阴支属性）
   - original_text: "阴支静且专"
   - text_layer: ORIGINAL_TEXT
   - semantic_definition: 阴支的特性：主静
   - canonical_state_mapping: PARTIAL（需要补充定义）

❌ 不提取：灾祥/否泰
   - 原因：这是Judgment概念
   - 原典说"速达显灾祥"，是说显现速度
   - 不是说"成灾"或"成祥"
```

### 第九章：衰旺
```
原文：能知衰旺之真机，其于三命之奥，思过半矣。
原文：旺则宜泄宜伤，衰则喜帮喜助。
原文：然旺中有衰者存，不可损也；衰中有旺者存，不可益也。

语义单元：
- 衰旺：强度状态
- 宜/喜：建议性表述
- 帮/助：支持性行为

Primitive提取：
❌ 不提取：衰/旺
   - 原因：这是Judgment，不是Primitive
   - 原典讨论"衰旺"，但没说如何判断
   - 只能作为Research Only的概念

❌ 不提取：得令/得地/得势
   - 原因：涉及L4力量问题
   - GPT裁决明确禁止
   - 只能作为Research Only的概念

⚠️ DTS-PRIM-019: 宜（建议性操作）
   - original_text: "旺则宜泄宜伤"
   - text_layer: ORIGINAL_TEXT
   - semantic_definition: 建议性操作（非强制）
   - canonical_state_mapping: UNRESOLVED
   - 原因：这是B类语句，不能升级为A类

⚠️ DTS-PRIM-020: 喜（建议性操作）
   - original_text: "衰则喜帮喜助"
   - text_layer: ORIGINAL_TEXT
   - semantic_definition: 建议性操作（非强制）
   - canonical_state_mapping: UNRESOLVED
   - 原因：这是B类语句，不能升级为A类
```

---

## 提取统计

| 类型 | 数量 | 说明 |
|------|------|------|
| **CANONICAL** | 10个 | 可以直接进入Canonical State |
| **PARTIAL** | 6个 | 需要补充定义 |
| **UNRESOLVED** | 4个 | 禁止进入Production |
| **总计** | 20个 | - |

---

## 下一步

### Step 2.5: Claude独立审计Primitive
- 验证每个Primitive是否忠实于原典
- 验证是否涉及Condition/Judgment
- 验证Canonical State映射是否正确

### Step 2.6: GPT裁决
- 根据Claude审计结果决定是否批准Step 3

---

**当前状态**: Step 2 Primitive Extraction进行中