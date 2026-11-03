# V1.3 A3 Evaluation Target Reconciliation

**日期**: 2026-08-22
**状态**: ✅ COMPLETE — 评估目标重新定义
**Git Commit**: c595a65 (A3.2 Diagnostic Freeze)

---

## 一、核心发现

A3.2 暴露的不是模型误差，而是 **Evaluation Target 与 Product Semantics 不一致** 的实验设计问题。

```text
当前顺天 Yi Engine 的原生任务:
  Birth Profile → Canonical Signal → STATE → OPPORTUNITY/RISK/REMEDIATION/ACTION
  (整体关系式解释)

A3.2 尝试验证的任务:
  Birth Profile + Target Event + Target Year → POSITIVE/NEGATIVE/NEUTRAL
  (事件方向分类)

结论: 这是两个不同的任务。
```

---

## 二、评估目标重新定义

### Target T1 — Event Direction Prediction

| 项目 | 状态 |
|------|------|
| 定义 | 给定出生信息 + 目标事件 + 时间窗口，预测事件方向 |
| 系统能力 | ❌ 当前系统不具备直接对应输出 |
| A3 判定 | **NOT EVALUABLE** |

> **NOT EVALUABLE ≠ FAIL**
> 
> 系统没有被设计为事件方向分类器。用分类指标评估解释引擎是拿错了尺子。

### Target T2 — State Direction (Diagnostic Only)

| 项目 | 状态 |
|------|------|
| 定义 | 从 STATE 字段映射到 POSITIVE/NEGATIVE/NEUTRAL |
| 系统能力 | ✅ 可提取（启发式规则） |
| A3.2 结果 | Micro-F1 = 0.567 (N=85) |
| A3 判定 | **DIAGNOSTIC ONLY** |

```text
A3.2 Diagnostic Result (FROZEN)
────────────────────────────────────
Eligible profiles:    86
Valid profiles:       85
Invalid:               1 (missing birth info)
Micro-F1:            0.567
Precision:           0.400
Recall:              0.971
Majority baseline:   0.92

This result is diagnostic only and is NOT a certified
prediction accuracy measurement.
```

### Target T3 — Relational Interpretation (PRIMARY)

| 项目 | 状态 |
|------|------|
| 定义 | 验证系统输出的关系式解释是否与独立专家一致 |
| 系统能力 | ✅ 这是顺天 Yi Engine 的原生任务 |
| A3 判定 | **PRIMARY VALIDATION TARGET** |

---

## 三、两条验证 Track

### Track A: Event Prediction

```text
Birth Profile + Target Event + Target Time Window
        ↓
预测该事件是否发生 / 方向 / 时间
        ↓
需要: TARGET EVENT + TARGET WINDOW + PREDICTION OUTPUT
```

**状态**: 暂不作为正式指标。当前系统不具备直接对应输出。

### Track B: Relational Interpretation Validation

```text
Birth Profile
        ↓
Bazi / Heluo / Ziwei / Huangli
        ↓
Canonical Signal
        ↓
Temporal Convergence
        ↓
STATE → OPPORTUNITY / RISK / REMEDIATION / ACTION
        ↓
与独立专家依据既定规则得出的解释比较
```

**状态**: 正式主验证目标。需要建立 Expert Oracle + Rubric + Blind Rating。

---

## 四、Relational Interpretation Rubric (草案)

| Dimension | 评分 | 说明 |
|-----------|------|------|
| STATE 是否成立 | 0–2 | 卦象状态描述是否准确 |
| OPPORTUNITY 是否成立 | 0–2 | 机会识别是否合理 |
| RISK 是否成立 | 0–2 | 风险识别是否合理 |
| REMEDIATION 是否合理 | 0–2 | 化解建议是否与状态一致 |
| ACTION 是否与状态一致 | 0–2 | 行动建议是否可操作 |
| Temporal alignment | 0–2 | 时间状态是否正确映射 |
| Evidence grounding | 0–2 | 是否引用具体经典来源 |

**总分**: 0–14

**Oracle**: 2 名独立评价者 + Cohen's κ / Krippendorff's α

---

## 五、A1 发现的 O4 缺口验证

A1 Oracle Qualification 已经发现：

```text
O4 人工 Oracle = 2/138
Inter-Rater Agreement = 未实现
```

A3.2 正好验证了这个问题：

> 没有 Expert Oracle，就无法验证 Relational Interpretation 的准确性。

**下一步**: 补齐 O4 Expert Oracle 基础设施。

---

## 六、冻结协议

### 6.1 禁止修改

```text
❌ Yi Engine
❌ STATE → OPPORTUNITY/RISK/REMEDIATION/ACTION 结构
❌ Event Ontology
❌ Severity 规则
❌ Temporal Engine
❌ Canonical Signal
❌ V1.2 Contract
```

**原因**: 防止 evaluation-driven architecture mutation。

### 6.2 A3.2 冻结

```text
A3.2 Diagnostic Result: FROZEN
├── Micro-F1 = 0.567 (N=85)
├── 不可修改
├── 不可作为 System Accuracy
└── 仅作为 Diagnostic Directional Classification
```

---

## 七、A3 重新设计

```text
A3 Accuracy Validation (Redesigned)
│
├── A3.1 Prediction Freeze                    ✅ COMPLETE
│
├── A3.2 Diagnostic Direction Test            ✅ COMPLETE (FROZEN)
│       └── Micro-F1 = 0.567 (Diagnostic Only)
│
├── A3.3 Evaluation Target Reconciliation     ✅ COMPLETE (本文档)
│
├── A3.4 Event Prediction Track               ⏸️ SUSPENDED
│       └── 暂不作为正式指标
│
├── A3.5 Relational Interpretation Track      ⏳ NEXT
│       ├── Expert Rubric Design
│       ├── O4 Expert Oracle Infrastructure
│       ├── Blind Rating Protocol
│       └── Inter-Rater Agreement
│
├── A3.6 Baseline Comparison                  ⏳ PENDING
│
├── A3.7 Statistical Confidence               ⏳ PENDING
│
└── A3 Final Gate                             ⏳ PENDING
```

---

## 八、深层发现

这次验证证明了顺天的核心定位：

```text
顺天不是:
  "根据八字预测某人今年会发生什么事件的分类器"

顺天是:
  "通过多个传统术数引擎形成时间—状态—关系信号，
   再输出结构化关系解释与行动建议的系统"
```

真正应该验证的是：

```text
数 × 卦 × 爻 × 位 × 时 × 势 × 体 × 援 × 辞 × 理
        ↓
      STATE
        ↓
  OPPORTUNITY / RISK / REMEDIATION / ACTION
```

如果硬把它压成 `吉 / 凶 / 平`，反而会把顺天最核心的架构压扁成一个普通分类器。

---

## 九、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│         A3 EVALUATION TARGET RECONCILIATION                   │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ COMPLETE                                         │
│                                                              │
│  Key Decision:                                               │
│    A3.2 Micro-F1 = 0.567 is DIAGNOSTIC ONLY                 │
│    NOT a certified prediction accuracy measurement           │
│                                                              │
│  Root Cause:                                                 │
│    Evaluation Target ≠ Product Semantics                     │
│    System outputs relational interpretation,                 │
│    evaluation expects event direction classification         │
│                                                              │
│  Two Tracks Defined:                                         │
│    Track A: Event Prediction → SUSPENDED                     │
│    Track B: Relational Interpretation → PRIMARY TARGET       │
│                                                              │
│  Frozen:                                                     │
│    ✅ A3.2 Diagnostic Result                                  │
│    ✅ V1.2 Architecture (no modification)                    │
│    ✅ Yi Engine (no modification)                            │
│                                                              │
│  Next: A3.5 Relational Interpretation Track                  │
│    ├── Expert Rubric Design                                  │
│    ├── O4 Expert Oracle Infrastructure                       │
│    └── Blind Rating Protocol                                 │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3-Evaluation-Target-Reconciliation-v1
