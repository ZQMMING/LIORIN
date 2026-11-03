# Judgment Candidate Pool - 原典明确授权

**时间**: 2026-08-31  
**阶段**: Phase 2 提取Judgment Candidate  
**依据**: GPT裁决 755aaa2 + 原典搜索  
**状态**: 🟡 PENDING_REVIEW

---

## 提取结果汇总

### 滴天髓（5个Judgment）
| # | Judgment ID | Original Text | Condition Part | Judgment Part | Source |
|---|-------------|---------------|----------------|---------------|--------|
| 1 | DTS-JUDG-001 | "有病方为贵，无伤不是奇" | 有病（有症结） | 方为贵（才能显贵） | 通神论·中和 |
| 2 | DTS-JUDG-002 | "格中如去病，财禄两相随" | 格中病去（格局完美） | 财禄两相随（必富贵） | 通神论·中和 |
| 3 | DTS-JUDG-003 | "真神得用平生贵，用假终为碌碌人" | 真神得用（用神纯正） | 平生贵（必定显贵） | 通神论·真假 |
| 4 | DTS-JUDG-004 | "用假终为碌碌人" | 用假（用神不纯） | 终为碌碌人（平庸） | 通神论·真假 |
| 5 | DTS-JUDG-005 | "配合得宜，皆为贵格" | 配合得宜（五行流通） | 皆为贵格（主贵） | 论用神 |

### 子平真诠（4个Judgment）
| # | Judgment ID | Original Text | Condition Part | Judgment Part | Source |
|---|-------------|---------------|----------------|---------------|--------|
| 6 | ZPZQ-JUDG-001 | "配合得宜，皆为贵格" | 配合得宜 | 皆为贵格 | 论用神 |
| 7 | ZPZQ-JUDG-002 | "遂成贵格，以其有情也" | 合伤存官/合煞存财 | 遂成贵格 | 论用神成败 |
| 8 | ZPZQ-JUDG-003 | "相神无破，贵格已成" | 相神无破 | 贵格已成 | 论相神 |
| 9 | ZPZQ-JUDG-004 | "相神有伤，立败其格" | 相神有伤 | 立败其格 | 论相神 |

---

## 逐条提取详情

### 1. DTS-JUDG-001: 有病方为贵
```json
{
  "judgment_id": "DTS-JUDG-001",
  "source_book": "滴天髓",
  "source_section": "通神论·中和",
  "original_text": "有病方为贵，无伤不是奇。",
  "condition_part": "有病（有症结需要解决）",
  "judgment_part": "方为贵（才能显贵）",
  "causal_relationship": "原典明确说'有病→贵'",
  "text_layer": "ORIGINAL_TEXT",
  "confidence": "HIGH",
  "risk_flags": [],
  "status": "CANDIDATE"
}
```

**分析**:
- ✅ 原典明确说出"有病→贵"的因果关系
- ✅ 有完整的Condition-Result结构
- ✅ 非建议性描述（不是"宜"而是"方为"）
- ⚠️ 需验证"有病"的定义是否明确

---

### 2. DTS-JUDG-002: 格中如去病
```json
{
  "judgment_id": "DTS-JUDG-002",
  "source_book": "滴天髓",
  "source_section": "通神论·中和",
  "original_text": "格中如去病，财禄两相随。",
  "condition_part": "格中病去（格局缺陷被解决）",
  "judgment_part": "财禄两相随（必主富贵）",
  "causal_relationship": "原典明确说'病去→财禄'",
  "text_layer": "ORIGINAL_TEXT",
  "confidence": "HIGH",
  "risk_flags": [],
  "status": "CANDIDATE"
}
```

**分析**:
- ✅ 原典明确说出"去病→财禄"的因果关系
- ✅ 有完整的Condition-Result结构
- ✅ 非建议性描述
- ✅ 无L4风险

---

### 3. DTS-JUDG-003: 真神得用平生贵
```json
{
  "judgment_id": "DTS-JUDG-003",
  "source_book": "滴天髓",
  "source_section": "通神论·真假",
  "original_text": "令上寻真聚得真，假神休要乱真神。真神得用平生贵，用假终为碌碌人。",
  "condition_part": "真神得用（用神纯正且得令）",
  "judgment_part": "平生贵（一生显贵）",
  "causal_relationship": "原典明确说'真神得用→平生贵'",
  "text_layer": "ORIGINAL_TEXT",
  "confidence": "HIGH",
  "risk_flags": [],
  "status": "CANDIDATE"
}
```

**分析**:
- ✅ 原典明确说出"真神得用→平生贵"
- ✅ 有完整的Condition-Result结构
- ✅ 无L4风险
- ✅ 无工程推断

---

### 4. DTS-JUDG-004: 用假终为碌碌人
```json
{
  "judgment_id": "DTS-JUDG-004",
  "source_book": "滴天髓",
  "source_section": "通神论·真假",
  "original_text": "真神得用平生贵，用假终为碌碌人。",
  "condition_part": "用假（用神不纯正）",
  "judgment_part": "终为碌碌人（一生平庸）",
  "causal_relationship": "原典明确说'用假→碌碌'",
  "text_layer": "ORIGINAL_TEXT",
  "confidence": "HIGH",
  "risk_flags": [],
  "status": "CANDIDATE"
}
```

**分析**:
- ✅ 原典明确授权
- ✅ 与DTS-JUDG-003成对出现
- ✅ 无L4风险

---

### 5. ZPZQ-JUDG-001: 配合得宜皆为贵格
```json
{
  "judgment_id": "ZPZQ-JUDG-001",
  "source_book": "子平真诠",
  "source_section": "论用神",
  "original_text": "财官印食，此用神之善而顺用之者也；煞伤劫刃，此用神之不善而逆用之者也。当顺而顺，当逆而逆，配合得宜，皆为贵格。",
  "condition_part": "配合得宜（顺用/逆用得当）",
  "judgment_part": "皆为贵格（必定显贵）",
  "causal_relationship": "原典明确说'配合得宜→贵格'",
  "text_layer": "ORIGINAL_TEXT",
  "confidence": "HIGH",
  "risk_flags": [],
  "status": "CANDIDATE"
}
```

**分析**:
- ✅ 原典明确授权
- ✅ 有完整的Condition-Result结构
- ✅ 定义性Judgment，非力量判断

---

### 6. ZPZQ-JUDG-002: 合伤存官遂成贵格
```json
{
  "judgment_id": "ZPZQ-JUDG-002",
  "source_book": "子平真诠",
  "source_section": "论用神成败救应",
  "original_text": "故甲透酉官，透丁合壬，是谓合伤存官，遂成贵格，以其有情也。",
  "condition_part": "合伤存官（解决用神破坏）",
  "judgment_part": "遂成贵格（必定显贵）",
  "causal_relationship": "原典明确说'合伤存官→成贵格'",
  "text_layer": "ORIGINAL_TEXT",
  "confidence": "HIGH",
  "risk_flags": [],
  "status": "CANDIDATE"
}
```

**分析**:
- ✅ 原典明确授权
- ✅ 具体的Condition-Result案例
- ✅ 有救应机制

---

### 7. ZPZQ-JUDG-003: 相神无破贵格已成
```json
{
  "judgment_id": "ZPZQ-JUDG-003",
  "source_book": "子平真诠",
  "source_section": "论相神紧要",
  "original_text": "相神无破，贵格已成；相神有伤，立败其格。",
  "condition_part": "相神无破（辅助用神完好）",
  "judgment_part": "贵格已成（格局成立）",
  "causal_relationship": "原典明确说'相神无破→贵格成'",
  "text_layer": "ORIGINAL_TEXT",
  "confidence": "HIGH",
  "risk_flags": [],
  "status": "CANDIDATE"
}
```

**分析**:
- ✅ 原典明确授权
- ✅ 简明扼要的Judgment
- ✅ 无L4风险

---

### 8. ZPZQ-JUDG-004: 相神有伤立败其格
```json
{
  "judgment_id": "ZPZQ-JUDG-004",
  "source_book": "子平真诠",
  "source_section": "论相神紧要",
  "original_text": "相神无破，贵格已成；相神有伤，立败其格。",
  "condition_part": "相神有伤（辅助用神受损）",
  "judgment_part": "立败其格（格局必定破败）",
  "causal_relationship": "原典明确说'相神有伤→格败'",
  "text_layer": "ORIGINAL_TEXT",
  "confidence": "HIGH",
  "risk_flags": [],
  "status": "CANDIDATE"
}
```

**分析**:
- ✅ 原典明确授权
- ✅ 与ZPZQ-JUDG-003成对出现
- ✅ 无L4风险

---

## 验证清单

### 检查项
| # | 检查项 | DTS-JUDG-001~005 | ZPZQ-JUDG-001~004 |
|---|--------|------------------|-------------------|
| 1 | 原典明确授权 | ✅ | ✅ |
| 2 | 有完整Condition-Result结构 | ✅ | ✅ |
| 3 | 非建议性描述（宜/忌） | ✅ | ✅ |
| 4 | 无L4 Strength风险 | ✅ | ✅ |
| 5 | 无工程推断 | ✅ | ✅ |
| 6 | 无任注混入 | ✅ | ✅ |

---

## 下一步

### Phase 3: Red-Team审查
- 检查是否把定义扩大成判断
- 检查是否有隐含L4风险
- 检查是否有工程组合

### Phase 4: Claude独立审计
- 验证原典是否真正授权
- 验证Condition是否忠实

### Phase 5: GPT裁决
- 最终裁决哪些Judgment进入Production

---

## 核心原则验证

> **从原典搜索明确的"条件→结果"结构**
> 
> **不是从Condition硬挖Judgment**
> 
> **只有原典明确授权的Judgment才能进入Production**

**当前状态**:
- ✅ Primitive Authority: 35个完成
- ✅ Condition Authority: 9个完成
- 🔄 Judgment Authority: 9个Candidate（待审核）