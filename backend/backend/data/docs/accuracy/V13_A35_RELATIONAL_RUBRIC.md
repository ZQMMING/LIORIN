# V1.3 A3.5.2 Relational Interpretation Rubric

**日期**: 2026-08-22
**状态**: ✅ FROZEN
**版本**: A3.5.2-v1

---

## 一、评分维度

### 1.1 七维度评分表

| Dimension | 评分 | 说明 |
|-----------|------|------|
| **STATE** | 0–2 | 卦象状态描述是否准确 |
| **OPPORTUNITY** | 0–2 | 机会识别是否合理 |
| **RISK** | 0–2 | 风险识别是否合理 |
| **REMEDIATION** | 0–2 | 化解建议是否与状态一致 |
| **ACTION** | 0–2 | 行动建议是否可操作 |
| **TEMPORAL ALIGNMENT** | 0–2 | 时间状态是否正确映射 |
| **EVIDENCE GROUNDING** | 0–2 | 是否引用具体经典来源 |

**总分**: 0–14

### 1.2 评分标准

#### 2 分 (优秀)

| 维度 | 标准 |
|------|------|
| STATE | 准确引用卦名、卦象、体用关系，符合经典规则 |
| OPPORTUNITY | 识别具体机会，与卦象逻辑一致，有经典依据 |
| RISK | 识别具体风险，与卦象逻辑一致，有经典依据 |
| REMEDIATION | 建议与 RISK 对应，符合易理，可操作 |
| ACTION | 建议具体、可执行、与 STATE 一致 |
| TEMPORAL | 正确映射当前时间状态（流日/流月/流年） |
| EVIDENCE | 引用具体经典（周易卦辞、说卦传、注疏） |

#### 1 分 (合格)

| 维度 | 标准 |
|------|------|
| STATE | 卦象描述基本正确，但有 minor 遗漏 |
| OPPORTUNITY | 识别机会但缺乏经典依据或过于笼统 |
| RISK | 识别风险但缺乏经典依据或过于笼统 |
| REMEDIATION | 建议合理但不够具体 |
| ACTION | 建议可操作但与 STATE 关联不强 |
| TEMPORAL | 时间映射基本正确但有 minor 偏差 |
| EVIDENCE | 有引用但不够具体或来源不明确 |

#### 0 分 (不合格)

| 维度 | 标准 |
|------|------|
| STATE | 卦象描述错误或缺失 |
| OPPORTUNITY | 未识别机会或识别错误 |
| RISK | 未识别风险或识别错误 |
| REMEDIATION | 建议与状态矛盾或缺失 |
| ACTION | 建议不可操作或与状态矛盾 |
| TEMPORAL | 时间映射错误或缺失 |
| EVIDENCE | 无引用或引用错误 |

---

## 二、NOT_EVALUABLE 独立标记

### 2.1 与 FAIL 严格分离

```text
0 分 (FAIL):
  - 维度存在但质量不合格
  - 计入总分
  - 需要改进

NOT_EVALUABLE:
  - 维度缺失或无法评估
  - 不计入总分
  - 需要补充信息
```

### 2.2 NOT_EVALUABLE 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **INSUFFICIENT_EVIDENCE** | 系统未提供足够信息 | 系统输出"需结合具体领域分析" |
| **AMBIGUOUS** | 输出模糊无法判断 | "可能有机会也可能有风险" |
| **NOT_APPLICABLE** | 该维度不适用 | 某些卦象无明确 OPPORTUNITY |
| **MISSING** | 维度完全缺失 | 系统未输出 ACTION |

### 2.3 记录格式

```json
{
  "dimension": "opportunity",
  "status": "NOT_EVALUABLE",
  "reason": "INSUFFICIENT_EVIDENCE",
  "detail": "系统输出'需结合具体人生领域分析'，未提供具体机会识别"
}
```

---

## 三、评分示例

### 3.1 示例 1: 高质量输出

**系统输出**:
```text
STATE: 天火同人卦，体用关系：用克体（凶）
OPPORTUNITY: 同人卦象征与人合作，利于团队协作
RISK: 用克体表示外部压力，需防小人
REMEDIATION: 以诚待人，保持谦逊
ACTION: 本周宜主动沟通，避免独断
SOURCE: 周易·天火同人、说卦传
```

**评分**:
| Dimension | Score | Reason |
|-----------|-------|--------|
| STATE | 2 | 准确引用卦名和体用关系 |
| OPPORTUNITY | 2 | 识别合作机会，符合卦象 |
| RISK | 2 | 识别外部压力，符合体用关系 |
| REMEDIATION | 1 | 建议合理但缺乏经典依据 |
| ACTION | 2 | 具体可操作 |
| TEMPORAL | 1 | "本周"映射不够精确 |
| EVIDENCE | 1 | 有引用但不够具体 |
| **Total** | **11/14** | |

### 3.2 示例 2: NOT_EVALUABLE

**系统输出**:
```text
STATE: 需结合具体人生领域分析
OPPORTUNITY: 参考爻辞与经典注解
RISK: 咨询专业易学顾问
```

**评分**:
| Dimension | Score | Reason |
|-----------|-------|--------|
| STATE | NOT_EVALUABLE | INSUFFICIENT_EVIDENCE: 未提供具体状态 |
| OPPORTUNITY | NOT_EVALUABLE | INSUFFICIENT_EVIDENCE: 套话 |
| RISK | NOT_EVALUABLE | INSUFFICIENT_EVIDENCE: 套话 |
| REMEDIATION | NOT_EVALUABLE | MISSING |
| ACTION | NOT_EVALUABLE | MISSING |
| TEMPORAL | NOT_EVALUABLE | MISSING |
| EVIDENCE | 0 | 引用了但无实质内容 |
| **Total** | **0/2** (仅 EVIDENCE 可评) | |

---

## 四、总分计算规则

### 4.1 有效维度

```text
有效维度数 = 7 - NOT_EVALUABLE 数量
```

### 4.2 归一化评分

```text
Normalized Score = (实际总分 / (有效维度数 × 2)) × 100%
```

### 4.3 示例

```text
7 维度全部可评:
  Total = 11/14
  Normalized = 11/14 × 100% = 78.6%

3 维度 NOT_EVALUABLE:
  Total = 8/8 (仅 4 维度可评)
  Normalized = 8/8 × 100% = 100%
  但标记: "4/7 dimensions NOT_EVALUABLE"
```

---

## 五、禁止行为

### 5.1 禁止

```text
❌ 因为系统输出"看起来合理"就给高分
❌ 因为系统引用了经典就给 EVIDENCE 高分（需检查引用是否正确）
❌ 因为用户可能满意就给高分（Oracle 评估质量，不是满意度）
❌ 因为系统复杂就给高分（复杂性 ≠ 质量）
```

### 5.2 必须

```text
✅ 严格按照 Rubric 评分
✅ 提供具体理由
✅ 标记 NOT_EVALUABLE（不强迫给分）
✅ 保持独立性（不看其他 Rater 评分）
```

---

## 六、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│           A3.5.2 RELATIONAL INTERPRETATION RUBRIC             │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ FROZEN                                           │
│                                                              │
│  7 Dimensions:                                               │
│    STATE / OPPORTUNITY / RISK / REMEDIATION / ACTION /       │
│    TEMPORAL ALIGNMENT / EVIDENCE GROUNDING                   │
│                                                              │
│  Scoring: 0-2 per dimension, Total 0-14                      │
│                                                              │
│  NOT_EVALUABLE:                                              │
│    ✅ 独立于 FAIL                                            │
│    ✅ 不计入总分                                             │
│    ✅ 4 types: INSUFFICIENT_EVIDENCE / AMBIGUOUS /           │
│              NOT_APPLICABLE / MISSING                        │
│                                                              │
│  Next: A3.5.3 Blind Rating Protocol                          │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.5.2-v1
