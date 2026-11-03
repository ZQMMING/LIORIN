# V1.3 A3.1 Prediction Freeze

**日期**: 2026-08-22
**Git Commit**: 7f22f6dd2b71e4476e68bfb0d3a89e9a55544d91
**评估类型**: A3 Pilot Prediction Accuracy Evaluation

---

## 一、冻结清单

### 1.1 算法版本

| 组件 | 版本/状态 | 说明 |
|------|---------|------|
| HeluoCanonical | v2.0 (FROZEN) | 河洛理数核心算法 |
| HeluoTemporal | V1.2 | 时间引擎 |
| BaziEngine | sxtwl v2.0.7 | 八字引擎（子初派） |
| ZiweiEngine | Stub + iztro | 紫微引擎（部分实现） |
| YiEngine | V1.0 | 易经解释引擎 |
| ForwardValidationEngine | V1.0 | 前瞻验证引擎 |

### 1.2 数据版本

| 数据集 | 版本 | 事件数 | 角色 |
|--------|------|--------|------|
| Pilot BLIND | A2-B4-v1.0 | 86 | PREDICTION_VALIDATION |
| Historical | A2-B3-P0-v1.0 | 270 | RECONSTRUCTION_EVIDENCE |
| Golden | V1.0.0 | 518 | CALIBRATION |

### 1.3 评估指标

| 指标 | 定义 | 用途 |
|------|------|------|
| Micro-F1 | 2TP / (2TP + FP + FN) | 主指标 |
| Precision | TP / (TP + FP) | 辅助 |
| Recall | TP / (TP + FN) | 辅助 |
| Macro-F1 | 各类别 F1 平均 | 辅助 |

### 1.4 评估范围

**A3 评估的是**：
> 在当前 86 个符合 Blind/O1 条件的 Pilot 事件上，顺天系统的方向预测能力。

**A3 不评估**：
- 系统整体准确率（无独立 HOLDOUT）
- 事件类型预测准确率（系统输出为方向标签，非事件类型）
- 具体时间预测准确率（系统输出为时间窗口，非具体年份）

---

## 二、评估协议

### 2.1 系统输出格式

顺天系统的预测输出为：
```python
PredictionRecord {
    prediction_direction: DirectionLabel  # POSITIVE | NEGATIVE | NEUTRAL | CHANGE
    prediction_window_start: int          # 起始年份
    prediction_window_end: int            # 结束年份
}
```

### 2.2 BLIND 数据集格式

fate-bench BLIND 事件为：
```python
{
    "event_type": str,           # 事件类型（如 LIFE_EVENT.TRAUMA）
    "event_year": Optional[int], # 事件年份（部分为 None）
    "event_direction": str,      # 事件方向（POSITIVE | NEGATIVE | NEUTRAL）
    "answer": str,               # 选择题答案（A/B/C/D/E）
    "description": str,          # 问题描述
}
```

### 2.3 评估映射

**问题**：系统输出方向标签，BLIND 数据集是选择题。

**解决方案**：
1. 提取 BLIND 事件的 `event_direction` 作为 Ground Truth
2. 系统预测方向标签
3. 比较预测方向 vs 实际方向

**限制**：
- 无法评估"哪一年发生"的预测能力
- 无法评估具体事件类型的预测能力
- 只能评估"方向"预测能力

---

## 三、评估流程

```text
BLIND Event (86 events)
        │
        ├─ Extract: person_id, birth_info, event_direction
        │
        ▼
HeluoCanonical.calculate(birth_info)
        │
        ├─ Output: Canonical Signal
        │
        ▼
YiEngine.interpret(canonical_signal)
        │
        ├─ Output: YiInterpretation (包含 direction prediction)
        │
        ▼
ForwardValidationEngine.create_prediction()
        │
        ├─ Output: PredictionRecord (direction + window)
        │
        ▼
Compare: predicted_direction vs actual_direction
        │
        ├─ Output: TP / FP / FN
        │
        ▼
Calculate: Micro-F1, Precision, Recall
```

---

## 四、分层评估矩阵

| Dimension | 评估内容 | 预期样本数 |
|-----------|---------|-----------|
| Event Type | EDUCATION / CAREER / FAMILY / LIFE_EVENT | ~86 |
| Direction | POSITIVE / NEGATIVE / NEUTRAL / CHANGE | ~86 |
| Year Precision | EXACT_YEAR / YEAR_RANGE | ~86 |

---

## 五、基线比较

| Baseline | 定义 | 预期 F1 |
|----------|------|---------|
| Random | 随机猜测方向 | ~0.25 |
| Majority | 总是预测最常见方向 | ~0.40 |
| Legacy Only | 仅使用 Legacy Engine | TBD |
| Shuntian Full | 完整 V1.3 Pipeline | TBD |

---

## 六、统计置信度

```text
N = 86
Confidence Level = 95%
Method = Bootstrap (1000 iterations)
```

**注意**：N=86 是 Pilot-scale validation，不是最终生产级 accuracy certification。

---

## 七、冻结确认

```text
┌─────────────────────────────────────────────────────────────┐
│              A3.1 PREDICTION FREEZE                          │
├─────────────────────────────────────────────────────────────┤
│  Git Commit: 7f22f6dd2b71e4476e68bfb0d3a89e9a55544d91      │
│  Date: 2026-08-22                                           │
│                                                              │
│  Frozen Components:                                          │
│    ✅ HeluoCanonical v2.0                                    │
│    ✅ HeluoTemporal V1.2                                     │
│    ✅ BaziEngine sxtwl v2.0.7                                │
│    ✅ YiEngine V1.0                                          │
│    ✅ ForwardValidationEngine V1.0                           │
│                                                              │
│  Frozen Data:                                                │
│    ✅ BLIND: 86 events                                       │
│    ✅ Historical: 270 events                                 │
│    ✅ Golden: 518 events                                     │
│                                                              │
│  Frozen Metrics:                                             │
│    ✅ Micro-F1 (primary)                                     │
│    ✅ Precision / Recall (auxiliary)                         │
│    ✅ Macro-F1 (auxiliary)                                   │
│                                                              │
│  Scope:                                                      │
│    ✅ Direction prediction accuracy                          │
│    ❌ Event type prediction (not supported)                  │
│    ❌ Exact year prediction (not supported)                  │
│    ❌ System-wide accuracy (no HOLDOUT)                      │
│                                                              │
│  Status: FROZEN                                              │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.1-Prediction-Freeze-v1
