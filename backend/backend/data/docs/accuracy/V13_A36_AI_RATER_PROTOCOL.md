# V1.3 A3.6-A AI Expert Simulation Protocol

**日期**: 2026-08-22
**状态**: ✅ FROZEN
**版本**: A3.6-A-v1

---

## 一、定义

### 1.1 AI Expert Simulation

```text
AI Expert Simulation ≠ O4 Human Expert Oracle

用途:
  ✅ 内部校准
  ✅ 发现 Rubric 问题
  ✅ 测试评分稳定性
  ✅ 压力测试评价体系

禁止:
  ❌ 宣称为"真实专家 Oracle"
  ❌ 作为正式 Accuracy 指标
  ❌ 替代人类专家验证
```

### 1.2 角色分工

| 角色 | 职责 | 禁止 |
|------|------|------|
| **Hermes** | 生成案例、固化输入、收集评分、计算一致性 | 不参与评分裁决 |
| **GPT** | Rater A，独立评分 | 不能看到 Qwen 评分 |
| **Qwen** | Rater B，独立评分 | 不能看到 GPT 评分 |

---

## 二、评分维度

### 2.1 七维度 (0-2 分)

| Dimension | 说明 |
|-----------|------|
| STATE | 卦象状态描述准确性 |
| OPPORTUNITY | 机会识别合理性 |
| RISK | 风险识别合理性 |
| REMEDIATION | 化解建议一致性 |
| ACTION | 行动建议可操作性 |
| TEMPORAL | 时间状态映射正确性 |
| EVIDENCE | 经典引用具体性 |

### 2.2 评分输出

```json
{
  "dimension": "state",
  "status": "SCORED",
  "score": 2,
  "reason": "准确引用卦名和体用关系",
  "evidence_reference": "周易·天火同人",
  "confidence": "HIGH"
}
```

### 2.3 NOT_EVALUABLE

```json
{
  "dimension": "remediation",
  "status": "NOT_EVALUABLE",
  "not_evaluable_reason": "MISSING",
  "reason": "系统未输出化解建议"
}
```

---

## 三、盲评协议

### 3.1 GPT 输入

```text
CASE_xxxx_BLIND.md
  ├── 人物基本信息
  ├── 出生年月日时
  ├── 系统原始输出
  └── Rubric 评分标准

禁止包含:
  ❌ Ground Truth
  ❌ Qwen 评分
  ❌ 系统内部计算链
```

### 3.2 Qwen 输入

```text
CASE_xxxx_BLIND.md (相同文件)
  ├── 人物基本信息
  ├── 出生年月日时
  ├── 系统原始输出
  └── Rubric 评分标准

禁止包含:
  ❌ Ground Truth
  ❌ GPT 评分
  ❌ 系统内部计算链
```

---

## 四、一致性指标

### 4.1 计算

```text
Cohen's κ (GPT vs Qwen)
Weighted κ (有序评分)
各维度 κ
NOT_EVALUABLE 一致性
```

### 4.2 判定

```text
κ ≥ 0.60 → AI Inter-Rater Agreement: Substantial
0.40 ≤ κ < 0.60 → Moderate
κ < 0.40 → Poor
```

### 4.3 报告格式

```text
AI Expert Simulation Agreement Report
════════════════════════════════════════
Total Cases: 40
Raters: GPT + Qwen

Overall Agreement:
  Cohen's κ: 0.xx
  Weighted κ: 0.xx

Per-Dimension κ:
  STATE: 0.xx
  OPPORTUNITY: 0.xx
  ...

Disagreements:
  Minor (diff=1): N
  Major (diff≥2): N

Status:
  AI-Simulation: 0.xx (NOT O4 Human Oracle)
  Human Expert: NOT YET QUALIFIED
  Formal Accuracy: NOT CERTIFIED
```

---

## 五、Oracle 分类

| Oracle | 用途 | 是否正式 Accuracy |
|--------|------|------------------|
| O1 Deterministic | 算法计算 | ✅ |
| O2 Historical | 历史事实 | reconstruction |
| O3 Classical | 经典一致性 | alignment |
| **AI-Simulation** | GPT/Qwen内部测试 | ❌ |
| **O4 Human Expert** | 独立专家评价 | ✅ |
| OX | 不可验证 | ❌ |

---

## 六、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│           A3.6-A AI EXPERT SIMULATION PROTOCOL                 │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ FROZEN                                           │
│                                                              │
│  Raters: GPT + Qwen (independent)                            │
│  Cases: 40 (from frozen_sample.json)                         │
│  Rubric: V13_A35_RELATIONAL_RUBRIC.md                        │
│                                                              │
│  Hermes Role:                                                │
│    ✅ Generate cases                                         │
│    ✅ Collect ratings                                        │
│    ✅ Calculate agreement                                    │
│    ❌ Cannot rate                                            │
│                                                              │
│  Output:                                                     │
│    AI Expert Simulation Agreement (NOT O4 Human Oracle)      │
│                                                              │
│  Next: Generate 40 Blind Cases                               │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.6-A-v1
