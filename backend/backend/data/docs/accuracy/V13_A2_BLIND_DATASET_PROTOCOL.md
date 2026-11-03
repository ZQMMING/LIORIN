# V1.3 A2.5 — Blind Dataset Construction

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档定义四层数据集构建策略。
禁止修改任何代码或数据集。

---

## 一、数据集分层定义

```text
DATASET LAYERS:
├── DEV: 开发/调试用 (可频繁修改)
├── CALIBRATION: 参数与规则校准 (可微调)
├── BLIND: 正式 Accuracy 评估 (冻结)
└── HOLDOUT: 最终不可碰数据 (永久冻结)
```

---

## 二、DEV 数据集规范

```yaml
dev_dataset:
  purpose: "开发调试、pipeline 验证"
  size_target: "20-50 cases"
  source_requirement: "Tier 3 minimum"
  leakage_requirement: "CLEAN or REVIEWED"
  update_policy: "can be modified anytime"
  approval_required: false
  
  # 示例来源
  sources:
    - GOLDEN-V1 (部分)
    - BNDARY
    - 自建测试案例
```

---

## 三、CALIBRATION 数据集规范

```yaml
calibration_dataset:
  purpose: "参数校准、规则微调、阈值调整"
  size_target: "50-100 cases"
  source_requirement: "Tier 2 minimum"
  leakage_requirement: "CLEAN only for BLIND candidates"
  update_policy: "can be modified with approval"
  approval_required: true
  
  # 示例来源
  sources:
    - GOLDEN-V1 (完整)
    - FB-OFFICIAL (降权使用)
    - MLB
    - CHQ
```

---

## 四、BLIND 数据集规范

```yaml
blind_dataset:
  purpose: "正式 Accuracy 评估"
  size_target: "100-300 cases (Phase 1)"
  source_requirement: "Tier 1 minimum (A grade preferred)"
  leakage_requirement: "CLEAN only"
  update_policy: "MUST NOT be modified after lock"
  approval_required: true
  
  # 锁定机制
  lock_policy:
    - "一旦进入正式评估，禁止修改"
    - "任何规则修改不得查看 BLIND 结果"
    - "只读访问"
  
  # 示例来源
  sources:
    - FB-OFFICIAL (fate-bench 官方答案)
    - GOLDEN-V1 (纪晓岚等历史名人)
    - MLB (MingLi-Bench)
  
  # 分层要求
  tier_distribution:
    tier_a_cases: "> 70%"
    tier_b_cases: "20-30%"
    tier_c_cases: "< 10%"
```

---

## 五、HOLDOUT 数据集规范

```yaml
holdout_dataset:
  purpose: "最终不可碰数据、独立验证"
  size_target: "50-100 cases (Phase 1)"
  source_requirement: "Tier 1 only (A grade required)"
  leakage_requirement: "CLEAN only"
  update_policy: "PERMANENTLY FROZEN"
  approval_required: true
  
  # 冻结机制
  freeze_policy:
    - "一旦建立，永久不可修改"
    - "任何规则修改不得查看 HOLDOUT 结果"
    - "仅用于最终独立验证"
    - "Guardian 监督冻结状态"
  
  # 示例来源
  sources:
    - 独立第三方案例库 (待建立)
    - 新收集的高质量历史案例
  
  # 分层要求
  tier_distribution:
    tier_a_cases: "100%"
    tier_b_cases: "0%"
    tier_c_cases: "0%"
```

---

## 六、数据集构建工作流

```text
DATASET CONSTRUCTION WORKFLOW:
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: Source Collection                                         │
│   ├── 从合格数据源收集案例                                           │
│   ├── 执行 Source Qualification (A2.1)                             │
│   └── 记录 provenance                                             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 2: Event Normalization                                       │
│   ├── 映射到 G1 4 Domains + 17 Event Types                        │
│   ├── 验证 Single-Parent Ontology                                 │
│   └── 完成 Event Schema (A2.2)                                    │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 3: Temporal Alignment                                        │
│   ├── 转换日期到公历                                                 │
│   ├── 声明时间精度                                                   │
│   ├── 确定 prediction_cutoff                                       │
│   └── 完成 Temporal Alignment (A2.3)                              │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 4: Leakage Classification                                    │
│   ├── 检测 L01-L12 全部类型                                         │
│   ├── 分类为 CLEAN/REVIEWED/CONTAMINATED                          │
│   └── 完成 Leakage Audit (A2.4)                                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 5: Tier Assignment                                          │
│   ├── 根据 provenance 和 leakage 分配 Tier                         │
│   ├── 检查数据质量                                                  │
│   └── 标注可进入的数据集层                                           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 6: Dataset Assembly                                          │
│   ├── 分配到 DEV/CALIBRATION/BLIND/HOLDOUT                        │
│   ├── 执行去重 (L05/L06)                                           │
│   └── 生成数据集清单                                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 7: Gate Approval                                             │
│   ├── Gate Keeper 审核                                               │
│   ├── 验证数据质量                                                   │
│   └── 签字确认                                                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 七、第一阶段数据集规模目标

```text
PHASE 1 TARGETS (A2 Completion):
├── DEV: 30 cases (已验证 pipeline)
├── CALIBRATION: 80 cases (参数校准)
├── BLIND: 150 cases (正式评估)
├── HOLDOUT: 50 cases (永久冻结)
└── TOTAL: 310 cases
```

---

## 八、数据集文档结构

```text
dataset/accuracy/
├── dev.jsonl                    # DEV 数据集
├── calibration.jsonl            # CALIBRATION 数据集
├── blind_v1.jsonl               # BLIND 数据集 v1
├── holdout_frozen.jsonl         # HOLDOUT 数据集 (永久冻结)
├── manifest.md                  # 数据集清单与说明
└── provenance/
    ├── source_registry.json     # 数据来源注册表
    ├── case_provenance.json     # 案例来源记录
    └── leakage_report.json      # 泄漏审计报告
```

---

**报告结束**
**下一步**: A2.6 Blind/Holdout Separation Protocol
