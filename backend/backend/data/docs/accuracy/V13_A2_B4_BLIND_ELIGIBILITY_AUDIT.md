# V1.3 A2-B4 Blind Eligibility Audit Report

**日期**: 2026-08-22
**审计对象**: Pilot (130 events) + Historical (270 events) = 400 events
**审计类型**: Blind Eligibility Assessment
**状态**: ✅ PASS

---

## 一、核心原则

> **Historical 270 条全部 O2，不得进入"预测准确率"的 Ground Truth。**

它们可以作为 **Evidence / Historical Reconstruction / Oracle-independent factual validation**，但不能与 Pilot 的 O1 预测 Oracle 混合计算一个 Accuracy Score。

---

## 二、筛选结果

| 分类 | 数量 | 占比 | 说明 |
|------|------|------|------|
| **BLIND_ELIGIBLE** | 86 | 21.5% | O1 + PRE_EVENT + OFFICIAL provenance |
| **EVIDENCE_ONLY** | 308 | 77.0% | O2 (历史记录) 或 THIRD_PARTY |
| **EXCLUDED** | 6 | 1.5% | OX (静态特征) |
| **总计** | 400 | 100% | — |

---

## 三、按数据集分布

| Dataset | BLIND | EVIDENCE | EXCLUDED | 总计 |
|---------|-------|----------|----------|------|
| **PILOT** | 86 | 38 | 6 | 130 |
| **HISTORICAL** | 0 | 270 | 0 | 270 |
| **总计** | 86 | 308 | 6 | 400 |

---

## 四、按 Oracle Type 分布

| Oracle Type | 数量 | 说明 |
|-------------|------|------|
| **O1** | 86 | 预测 Oracle (全部进入 BLIND) |
| **O2** | 308 | 历史记录 (全部进入 EVIDENCE) |
| **OX** | 6 | 静态特征 (全部排除) |

---

## 五、关键决策

### 5.1 Pilot 数据分类

```text
PILOT (130 events):
├── O1 + OFFICIAL + PRE_EVENT → BLIND_ELIGIBLE (86)
│   └── 可用于预测准确率验证
│
├── O1 + THIRD_PARTY → EVIDENCE_ONLY (38)
│   └── 第三方答案，不作为主要 Ground Truth
│
└── OX (静态特征) → EXCLUDED (6)
    └── 性格/外貌等问题，不可时间验证
```

### 5.2 Historical 数据分类

```text
HISTORICAL (270 events):
└── O2 (全部) → EVIDENCE_ONLY (270)
    └── 历史记录，不是预测 Oracle
    └── 可用于历史事实还原验证
    └── 不可用于预测准确率验证
```

---

## 六、B4 五级准入检查

| Gate | 条件 | 结果 |
|------|------|------|
| B4.1 | Person identity verified | ✅ 全部通过 |
| B4.2 | Event ontology = V1.2 17 types | ✅ 全部通过 |
| B4.3 | Event date precision ≥ YEAR | ✅ 全部通过 |
| B4.4 | Provenance complete | ✅ 全部通过 |
| B4.5 | Oracle qualification 明确 | ✅ 全部通过 |
| B4.6 | PRE_EVENT / POST_EVENT 明确 | ✅ 全部通过 |
| B4.7 | 无 L01–L12 leakage | ✅ 全部通过 |
| B4.8 | 无 duplicate / near-duplicate | ✅ 全部通过 |
| B4.9 | Event cluster dependency 已标记 | ✅ Historical 已标记 |
| B4.10 | Blind cutoff 可证明早于 event | ✅ Pilot 已验证 |
| B4.11 | 禁止使用预测后资料 | ✅ 全部通过 |
| B4.12 | 可复现 | ✅ 全部通过 |

---

## 七、数据集分层

```text
A2 DATASET POOL (400 events)
          │
          ├─────────────────────────────────────┐
          ▼                                     ▼
     Pilot / O1                           Historical / O2
     130 events                           270 events
          │                                     │
          ├─ BLIND_ELIGIBLE (86)                ├─ EVIDENCE_ONLY (270)
          │  └─ 预测准确率验证                   │  └─ 历史事实还原验证
          │                                     │
          ├─ EVIDENCE_ONLY (38)                 │
          │  └─ 第三方答案交叉验证               │
          │                                     │
          └─ EXCLUDED (6)                       │
             └─ 静态特征，不可验证               │
```

---

## 八、A3 评估策略

### 8.1 预测准确率 (Prediction Accuracy)

```text
数据来源: BLIND_ELIGIBLE (86 events)
├── 全部来自 PILOT
├── Oracle Type: O1
├── Provenance: OFFICIAL
└── 用途: 验证算法预测能力
```

### 8.2 历史事实还原 (Historical Reconstruction)

```text
数据来源: EVIDENCE_ONLY (308 events)
├── PILOT THIRD_PARTY: 38 events
├── HISTORICAL: 270 events
├── Oracle Type: O2
└── 用途: 验证算法还原历史事实的能力
```

### 8.3 独立报告

```text
A3 必须分别报告:
├── Accuracy_Prediction (86 events)
├── Accuracy_Reconstruction (308 events)
└── 不得混合计算单一 Accuracy Score
```

---

## 九、输出文件

```text
dataset/accuracy/blind/
├── blind_candidates.json      (86 events)
├── blind_manifest.json        (统计摘要)
└── excluded_events.json       (6 events)

dataset/accuracy/evidence_only/
└── historical_evidence.json   (308 events)
```

---

## 十、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│               A2-B4 BLIND ELIGIBILITY AUDIT                   │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ PASS                                             │
│                                                              │
│  BLIND_ELIGIBLE: 86 events (21.5%)                           │
│    └── All from PILOT, O1 + PRE_EVENT + OFFICIAL             │
│                                                              │
│  EVIDENCE_ONLY: 308 events (77.0%)                           │
│    └── 38 PILOT THIRD_PARTY + 270 HISTORICAL O2              │
│                                                              │
│  EXCLUDED: 6 events (1.5%)                                   │
│    └── All OX static traits                                  │
│                                                              │
│  Key Decision:                                               │
│    Historical 270 events CANNOT be used for prediction       │
│    accuracy validation. They are EVIDENCE_ONLY.              │
│                                                              │
│  Ready for A2 Final Dataset Gate.                            │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A2-B4-Blind-Eligibility-v1
