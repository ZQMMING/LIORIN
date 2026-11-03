# V1.3 A3.5.5 Inter-Rater Agreement Protocol

**日期**: 2026-08-22
**状态**: ✅ FROZEN
**版本**: A3.5.5-v1

---

## 一、一致性指标

### 1.1 主要指标

| 指标 | 适用场景 | 说明 |
|------|---------|------|
| **Cohen's κ** | 2 位 Rater | 分类一致性（去除随机因素） |
| **Weighted κ** | 2 位 Rater, 有序评分 | 考虑评分距离（0-1-2） |
| **Krippendorff's α** | ≥3 位 Rater | 多位评价者一致性 |

### 1.2 计算公式

#### Cohen's κ

```text
κ = (p_o - p_e) / (1 - p_e)

其中:
  p_o = 观察一致性 (实际一致比例)
  p_e = 期望一致性 (随机一致比例)
```

#### Weighted κ

```text
κ_w = 1 - (Σ w_ij * x_ij) / (Σ w_ij * m_ij)

其中:
  w_ij = 权重矩阵 (|i-j| 距离)
  x_ij = 观察频数
  m_ij = 期望频数
```

### 1.3 解释标准

| κ 值 | 一致性等级 | 说明 |
|------|-----------|------|
| < 0 | Poor | 低于随机 |
| 0.00-0.20 | Slight | 极低一致性 |
| 0.21-0.40 | Fair | 低一致性 |
| 0.41-0.60 | Moderate | 中等一致性 |
| 0.61-0.80 | Substantial | 高一致性 |
| 0.81-1.00 | Almost Perfect | 几乎完美 |

---

## 二、Oracle 合格标准

### 2.1 最低要求

```text
Cohen's κ ≥ 0.60 (Substantial)

如果 κ < 0.60:
  ❌ Oracle 不合格
  ❌ 不能用于正式评估
  ❌ 需要重新培训 Rater 或修改 Rubric
```

### 2.2 推荐标准

```text
Weighted κ ≥ 0.70 (高一致性)

如果 0.60 ≤ κ < 0.70:
  ⚠️ Oracle 条件合格
  ⚠️ 可用于 Pilot，但需改进
  ⚠️ 记录分歧原因
```

### 2.3 为什么需要高一致性

```text
如果专家之间一致性很低:
  ├── 说明 Rubric 不够清晰
  ├── 说明 Rater 培训不足
  ├── 说明评估任务本身模糊
  └── 那么 Oracle 本身就不合格

不能只报告:
  "专家平均评分 78%"

必须同时回答:
  "专家自己是否高度一致？"
```

---

## 三、分歧分析

### 3.1 分歧类型

| 类型 | 定义 | 处理 |
|------|------|------|
| **Minor** | 差异 = 1 | 记录，不裁决 |
| **Major** | 差异 ≥ 2 | Adjudicator 裁决 |
| **Critical** | 差异 = 2 (0 vs 2) | 必须 Adjudicator |

### 3.2 分歧原因分析

```text
对每个 Major/Critical 分歧:
  ├── 记录 Rater A 理由
  ├── 记录 Rater B 理由
  ├── 分析分歧维度
  └── 归类原因:
      ├── Rubric 不清晰
      ├── 样本模糊
      ├── Rater 理解偏差
      └── 其他
```

### 3.3 分歧报告

```json
{
  "disagreement_analysis": {
    "total_samples": 40,
    "minor_disagreements": 8,
    "major_disagreements": 3,
    "critical_disagreements": 1,
    "agreement_rate": 0.875,
    "cohens_kappa": 0.72,
    "weighted_kappa": 0.78,
    "disagreement_reasons": {
      "rubric_unclear": 2,
      "ambiguous_sample": 1,
      "rater_bias": 1
    }
  }
}
```

---

## 四、Adjudication Protocol

### 4.1 Adjudicator 选择

```text
Adjudicator 必须:
  ✅ 符合 O4 资质 (A3.5.1)
  ✅ 独立于 Rater A/B
  ✅ 不知晓分歧原因 (盲评)
  ✅ 不知晓 Rater 身份
```

### 4.2 Adjudication 流程

```text
Step 1: 识别分歧样本
  └── 差异 ≥ 2 分

Step 2: 准备 Adjudication 包
  ├── 样本信息 (匿名化)
  ├── Rater A 评分 + 理由 (去除 Rater 标识)
  ├── Rater B 评分 + 理由 (去除 Rater 标识)
  └── Rubric 标准

Step 3: Adjudicator 独立评分
  ├── 按 Rubric 评分
  ├── 提供理由
  └── 不得与 Rater 沟通

Step 4: 最终评分
  ├── 多数决定 (2/3)
  ├── 如果三方都不同 → 取中位数
  └── 记录最终理由
```

### 4.3 Adjudication 记录

```json
{
  "sample_id": "SAMPLE_017",
  "dimension": "opportunity",
  "rater_a_score": 0,
  "rater_a_reason": "未识别具体机会",
  "rater_b_score": 2,
  "rater_b_reason": "识别合作机会，符合卦象",
  "adjudicator_score": 1,
  "adjudicator_reason": "识别机会但缺乏经典依据",
  "final_score": 1,
  "decision_method": "median"
}
```

---

## 五、报告格式

### 5.1 必须报告

```text
1. 样本总数
2. 可评维度数 (去除 NOT_EVALUABLE)
3. Cohen's κ (整体)
4. Weighted κ (整体)
5. 各维度 κ
6. 分歧数量 (Minor/Major/Critical)
7. 分歧原因分析
8. Adjudication 数量
9. 最终评分分布
```

### 5.2 禁止报告

```text
❌ 只报告平均评分
❌ 不报告一致性指标
❌ 不报告分歧分析
❌ 不报告 NOT_EVALUABLE 比例
```

### 5.3 示例报告

```text
Inter-Rater Agreement Report
════════════════════════════════════════
Total Samples: 40
Evaluable Dimensions: 252 (40 × 7 - 28 NOT_EVALUABLE)

Overall Agreement:
  Cohen's κ: 0.72 (Substantial)
  Weighted κ: 0.78 (High)

Per-Dimension κ:
  STATE: 0.85 (Almost Perfect)
  OPPORTUNITY: 0.68 (Substantial)
  RISK: 0.75 (Substantial)
  REMEDIATION: 0.62 (Substantial)
  ACTION: 0.70 (Substantial)
  TEMPORAL: 0.80 (Almost Perfect)
  EVIDENCE: 0.65 (Substantial)

Disagreements:
  Minor (diff=1): 8 (20%)
  Major (diff≥2): 3 (7.5%)
  Critical (diff=2): 1 (2.5%)

Disagreement Reasons:
  Rubric unclear: 2
  Ambiguous sample: 1
  Rater bias: 1

Adjudication: 4 cases resolved

Oracle Status: ✅ QUALIFIED (κ ≥ 0.60)
```

---

## 六、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│           A3.5.5 INTER-RATER AGREEMENT PROTOCOL                │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ FROZEN                                           │
│                                                              │
│  Metrics:                                                    │
│    ✅ Cohen's κ (2 Raters)                                   │
│    ✅ Weighted κ (ordered scoring)                           │
│    ✅ Krippendorff's α (≥3 Raters, future)                  │
│                                                              │
│  Oracle Qualification:                                       │
│    ✅ κ ≥ 0.60 (Substantial) required                       │
│    ✅ κ < 0.60 → Oracle NOT QUALIFIED                       │
│                                                              │
│  Disagreement Handling:                                      │
│    ✅ Minor (diff=1): record only                            │
│    ✅ Major (diff≥2): Adjudicator                            │
│    ✅ Critical (diff=2): mandatory Adjudicator               │
│                                                              │
│  Reporting:                                                  │
│    ✅ Must report κ + disagreement analysis                  │
│    ❌ Cannot report only average score                       │
│                                                              │
│  Next: A3.5.6 Gate Audit                                     │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.5.5-v1
