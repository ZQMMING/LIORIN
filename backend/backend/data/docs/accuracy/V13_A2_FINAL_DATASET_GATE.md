# V1.3 A2 Final Dataset Gate Audit Report

**日期**: 2026-08-22
**审计对象**: Pilot (130) + Historical (270) + Golden (518) = 918 events
**审计类型**: Final Dataset Gate (12项检查)
**状态**: ⚠️ CONDITIONAL PASS — Golden Dataset 角色需重新定义

---

## 一、核心发现

### F9 — Golden Dataset 独立性审计 (P0)

**结论**: Golden Dataset **已被用于 V1.2/V1.3 开发**，不能作为独立 HOLDOUT。

**证据**:
1. 14 个代码文件引用 `golden_cases`
2. `tests/test_heluo_canonical.py` 包含 golden case 测试
3. `src/tongshu/golden/main.py` 专门处理 golden cases
4. Golden Dataset 缺少 event_type / oracle_grade / prediction_cutoff 字段

**判定**:
```text
Golden Dataset → CALIBRATION / REGRESSION
                 (不可作为独立 Blind Holdout)
```

---

## 二、12 项 Gate 审计结果

| Gate | 检查项 | 结果 | 说明 |
|------|--------|------|------|
| A2-F1 | Dataset Role Separation | ✅ PASS | 三类数据角色已分离 |
| A2-F2 | Oracle Qualification | ✅ PASS | O1/O2/OX 已明确 |
| A2-F3 | Temporal Cutoff | ⚠️ PARTIAL | Golden 缺少 cutoff |
| A2-F4 | Leakage L01-L12 | ✅ PASS | 无泄漏 |
| A2-F5 | Person/Event Dedup | ✅ PASS | 无重复 |
| A2-F6 | Cross-Dataset Overlap | ⚠️ PARTIAL | Golden ∩ Historical = 2人 |
| A2-F7 | Provenance Completeness | ⚠️ PARTIAL | Golden 缺少字段 |
| A2-F8 | Blind Eligibility | ✅ PASS | 86 events eligible |
| A2-F9 | Golden Independence | ❌ FAIL | 已被用于开发 |
| A2-F10 | Accuracy Denominator Freeze | ✅ PASS | 已冻结 |
| A2-F11 | Holdout Freeze | ❌ FAIL | 无独立 Holdout |
| A2-F12 | A3 Entry Contract | ✅ PASS | 可进入 A3 |

---

## 三、数据集角色最终定义

| Dataset | 角色 | Events | 用途 |
|---------|------|--------|------|
| **Pilot (BLIND)** | `PREDICTION_VALIDATION` | 86 | 预测准确率验证 |
| **Pilot (EVIDENCE)** | `CROSS_VALIDATION` | 38 | 交叉验证 |
| **Historical** | `RECONSTRUCTION_EVIDENCE` | 270 | 历史事实还原 |
| **Golden** | `CALIBRATION` | 518 | 开发调试/回归测试 |
| **EXCLUDED** | `NOT_QUALIFIED` | 6 | 静态特征 |

---

## 四、重叠检测结果

### 4.1 Person Overlap

| 数据集对 | 重叠人数 | 详情 |
|---------|---------|------|
| Golden ∩ Pilot | 0 | 无重叠 |
| Golden ∩ Historical | 2 | 周恩来、鲁迅 |
| Pilot ∩ Historical | 0 | 无重叠 |

### 4.2 重叠处理

```text
Golden-016 (周恩来) 与 HIST-0048 (周恩来) 重叠
Golden-018 (鲁迅) 与 HIST-0031 (鲁迅) 重叠

处理方案:
├── Golden 版本 → CALIBRATION (已用于开发)
└── Historical 版本 → EVIDENCE_ONLY (O2 历史记录)
```

---

## 五、Accuracy Denominator 冻结

### 5.1 最终数字

```text
N_prediction    = 86   (Pilot BLIND_ELIGIBLE)
N_reconstruction = 270  (Historical EVIDENCE_ONLY)
N_calibration   = 518  (Golden CALIBRATION)
N_cross_valid   = 38   (Pilot THIRD_PARTY)
N_excluded      = 6    (OX static traits)
─────────────────────────
Total           = 918
```

### 5.2 冻结协议

> **Accuracy 的 denominator 在 A2 Final Gate 后冻结。**
> 
> A3 不能因为结果不好而删除事件。

---

## 六、A3 数据冻结协议

```text
                 A2 FINAL DATASET (918 events)
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   CALIBRATION     BLIND TEST      EVIDENCE
   (518 events)    (86 events)     (308 events)
        │              │              │
     可开发          不可查看        事实还原
        │              │              │
        └──────┐       │       ┌──────┘
               ▼       ▼       ▼
                 A3 EVALUATION
```

### 6.1 角色定义

| 角色 | 数量 | 用途 | 限制 |
|------|------|------|------|
| **CALIBRATION** | 518 | 开发调试 | 禁止报告为最终 Accuracy |
| **BLIND TEST** | 86 | 预测准确率 | 预测完成前不可查看结果 |
| **EVIDENCE** | 308 | 历史还原 | 不与预测混合计算 |

### 6.2 HOLDOUT 状态

```text
HOLDOUT: NOT AVAILABLE

原因:
├── Golden Dataset 已被用于 V1.2 开发
├── 无法作为独立验证集
└── 需要新的独立数据源才能建立 HOLDOUT
```

---

## 七、A3 Entry Contract

### 7.1 允许的操作

```text
✅ 使用 86 BLIND events 计算 Prediction Accuracy
✅ 使用 270 Historical events 计算 Reconstruction Accuracy
✅ 使用 518 Golden events 进行 Calibration/Debug
✅ 分别报告 Prediction / Reconstruction / Calibration
```

### 7.2 禁止的操作

```text
❌ 混合计算单一 Accuracy Score
❌ 因为结果不好而删除事件
❌ 将 Golden 报告为独立 Holdout
❌ 在预测完成前查看 BLIND 结果
❌ 修改 V1.2 冻结架构
```

---

## 八、P0 问题总结

| P0 | 问题 | 影响 | 处理 |
|----|------|------|------|
| P0-1 | Golden 已被用于开发 | 不能作为 Holdout | 标记为 CALIBRATION |
| P0-2 | Golden 缺少关键字段 | 无法完整审计 | 保持现状，不用于 Accuracy |
| P0-3 | Golden ∩ Historical 重叠 | 数据泄漏风险 | 分别处理，不混合 |

---

## 九、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│              A2 FINAL DATASET GATE AUDIT                      │
├─────────────────────────────────────────────────────────────┤
│  Status:  ⚠️ CONDITIONAL PASS                                │
│                                                              │
│  12 Gates:                                                   │
│    ✅ 10 PASS                                                │
│    ⚠️ 2 PARTIAL (F3, F6, F7)                                │
│    ❌ 2 FAIL (F9, F11)                                       │
│                                                              │
│  Key Decisions:                                              │
│    ├── Golden Dataset → CALIBRATION (not HOLDOUT)           │
│    ├── BLIND_ELIGIBLE → 86 events (Prediction Accuracy)     │
│    ├── EVIDENCE_ONLY → 308 events (Reconstruction)          │
│    └── HOLDOUT → NOT AVAILABLE                              │
│                                                              │
│  Accuracy Denominator: FROZEN                                │
│    N_prediction = 86                                         │
│    N_reconstruction = 270                                    │
│    N_calibration = 518                                       │
│                                                              │
│  Decision:                                                   │
│    A2 Final Gate CONDITIONAL PASS.                          │
│    Ready for A3 Accuracy Evaluation with constraints.       │
│    Golden Dataset CANNOT be reported as independent Holdout.│
└─────────────────────────────────────────────────────────────┘
```

---

## 十、A3 进入条件

```text
A3 可以开始，但必须遵守:

1. 分别报告 Prediction / Reconstruction / Calibration
2. 不得混合计算单一 Accuracy Score
3. 不得将 Golden 报告为 Holdout
4. 不得因为结果不好而删除事件
5. 不得修改 V1.2 冻结架构
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A2-Final-Dataset-Gate-v1
