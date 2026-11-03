# V1.3 A3.6.3 Rubric Calibration Protocol

**日期**: 2026-08-22
**状态**: ✅ FROZEN
**版本**: A3.6.3-v1

---

## 一、校准目标

确保所有 Rater 对 Rubric 理解一致，评分标准统一。

---

## 二、校准流程

### 2.1 校准样本

```text
数量: 5 个样本
来源: 从 Pilot BLIND 中选取
特点:
  ├── 2 个高质量输出 (预期 2 分)
  ├── 2 个中等质量输出 (预期 1 分)
  └── 1 个 NOT_EVALUABLE 样本 (测试标记能力)
```

### 2.2 校准步骤

```text
Step 1: Rubric 培训 (30 min)
  ├── 讲解 7 维度评分标准
  ├── 讲解 NOT_EVALUABLE 标记规则
  └── 示例评分演示

Step 2: 独立校准评分 (60 min)
  ├── 每位 Rater 独立评分 5 个样本
  ├── 不得互相讨论
  └── 记录评分理由

Step 3: 校准结果分析
  ├── 计算 Rater 间一致性
  ├── 识别分歧维度
  └── 分析分歧原因

Step 4: 校准讨论 (30 min)
  ├── 讨论分歧样本
  ├── 澄清 Rubric 理解
  └── 统一评分标准

Step 5: 二次校准 (如需要)
  ├── 如果 κ < 0.60
  ├── 重新培训 + 重新评分
  └── 直到 κ ≥ 0.60
```

---

## 三、校准通过标准

### 3.1 整体一致性

```text
Cohen's κ ≥ 0.60 (Substantial)

如果 κ < 0.60:
  ❌ 校准未通过
  ❌ 需要重新培训
  ❌ 不得进入正式评分
```

### 3.2 维度一致性

```text
每个维度 κ ≥ 0.50

如果某维度 κ < 0.50:
  ⚠️ 该维度需要额外培训
  ⚠️ 可能需要修改 Rubric
  ⚠️ 记录分歧原因
```

### 3.3 NOT_EVALUABLE 一致性

```text
NOT_EVALUABLE 标记一致性 ≥ 80%

如果不一致:
  ⚠️ 澄清 NOT_EVALUABLE 标准
  ⚠️ 提供额外示例
```

---

## 四、校准记录格式

```json
{
  "calibration_date": "2026-08-22",
  "raters": ["RATER_001", "RATER_002"],
  "samples": 5,
  "results": {
    "overall_kappa": 0.72,
    "per_dimension_kappa": {
      "state": 0.85,
      "opportunity": 0.68,
      "risk": 0.75,
      "remediation": 0.62,
      "action": 0.70,
      "temporal": 0.80,
      "evidence": 0.65
    },
    "not_evaluable_agreement": 0.90,
    "disagreements": [
      {
        "sample_id": "CALIB_003",
        "dimension": "opportunity",
        "rater_a_score": 1,
        "rater_b_score": 2,
        "reason": "Rubric unclear on specific vs general opportunity"
      }
    ]
  },
  "passed": true,
  "notes": "Calibration passed after one round of discussion"
}
```

---

## 五、校准失败处理

### 5.1 如果 κ < 0.60

```text
Step 1: 分析分歧原因
  ├── Rubric 不清晰？
  ├── Rater 理解偏差？
  └── 样本本身模糊？

Step 2: 针对性培训
  ├── 澄清 Rubric
  ├── 提供额外示例
  └── 重新讲解标准

Step 3: 二次校准
  ├── 重新评分 5 个样本
  └── 重新计算 κ

Step 4: 如果仍然 κ < 0.60
  ├── 考虑修改 Rubric (A3.5.2)
  ├── 考虑更换 Rater
  └── 记录原因
```

### 5.2 禁止行为

```text
❌ 调整 Rubric 使 κ "通过"
❌ 删除分歧样本
❌ 强迫 Rater 达成一致
❌ 忽略低 κ 继续正式评分
```

---

## 六、当前状态

```text
Rubric Calibration:
  ├── RATER_001: NOT_CALIBRATED (等待招募)
  ├── RATER_002: NOT_CALIBRATED (等待招募)
  └── (需要真实独立评价者后才能执行校准)
```

---

## 七、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│              A3.6.3 CALIBRATION PROTOCOL                       │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ FROZEN (Protocol)                                │
│                                                              │
│  Calibration Process:                                        │
│    ✅ 5 个校准样本                                            │
│    ✅ Rubric 培训 (30 min)                                   │
│    ✅ 独立评分 (60 min)                                      │
│    ✅ 一致性分析                                             │
│    ✅ 校准讨论 (30 min)                                      │
│                                                              │
│  Pass Criteria:                                              │
│    ✅ Overall κ ≥ 0.60                                       │
│    ✅ Per-dimension κ ≥ 0.50                                 │
│    ✅ NOT_EVALUABLE agreement ≥ 80%                          │
│                                                              │
│  Current Status:                                             │
│    ⏳ NOT_CALIBRATED (等待真实独立评价者)                     │
│                                                              │
│  Next: A3.6.4 Sample Freeze                                  │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.6.3-v1

**重要声明**: 本文档定义了校准协议，但**未执行实际校准**。真正的校准必须在真实 Rater 招募后进行。
