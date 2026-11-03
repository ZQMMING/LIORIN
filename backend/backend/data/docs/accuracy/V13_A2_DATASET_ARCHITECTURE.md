# V1.3 A2 — Dataset Architecture

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档定义 A2 数据工程总体架构，为后续6个 Gate 提供框架基础。
禁止修改任何代码或数据集。

---

## 一、A2 目标

建立独立于算法的、可审计的事实验证数据基础设施。

```text
目标 = 可追溯的事实数据 + 严格的时间边界 + 防泄漏设计
NOT = 大规模数据集 + 自动准确率计算 + 算法调优
```

---

## 二、数据流架构

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        A2 DATA FLOW                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   PUBLIC SOURCES                                                    │
│   ├── 历史人物出生资料                                                │
│   ├── 生卒资料                                                       │
│   ├── 任职/婚姻/迁移/重大事件                                         │
│   ├── 古籍命例                                                        │
│   ├── 公开案例                                                        │
│   └── 外部 benchmark                                                 │
│                     │                                               │
│                     ▼                                               │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                   SOURCE QUALIFICATION (A2.1)               │   │
│   │   source_id | name | URL/文献 | owner | publish_date        │   │
│   │   event_date | access_date | public | license | commercial  │   │
│   │   evidence_grade | primary/secondary/tertiary | accuracy_ok │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                     │                                               │
│                     ▼                                               │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                   PROVENANCE / EVIDENCE (A2.2)              │   │
│   │   Evidence Level 1-5                                         │   │
│   │   Source Chain: Primary → Secondary → Tertiary              │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                     │                                               │
│                     ▼                                               │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                   EVENT NORMALIZATION (A2.2)                │   │
│   │   PERSON → birth/death/education/career/marriage/etc.       │   │
│   │   ↓映射到 G1 4 Domains + 17 Event Types                      │   │
│   │   Single-Parent Ontology 强制                                │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                     │                                               │
│                     ▼                                               │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                   TEMPORAL ALIGNMENT (A2.3)                 │   │
│   │   event_date_exact | month | year | precision              │   │
│   │   timezone | calendar_system | source_date                 │   │
│   │   禁止伪造精确日期，仅记录可用精度                              │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                     │                                               │
│                     ▼                                               │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                   LEAKAGE CLASSIFICATION (A2.4)             │   │
│   │   L01-L12 全部检测                                             │   │
│   │   event_date vs source_publication_date vs prediction_cutoff│   │
│   └─────────────────────────────────────────────────────────────┘   │
│                     │                                               │
│                     ▼                                               │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                   BLIND DATASET (A2.5-A2.6)                 │   │
│   │   DEV | CALIBRATION | BLIND | HOLDOUT                      │   │
│   │   BLIND: PRE_EVENT 可用于 Accuracy                         │   │
│   │   HOLDOUT: 冻结，任何规则修改不得查看结果                     │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                     │                                               │
│                     ▼                                               │
│                 ACCURACY EVALUATION (A3)                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、数据分层模型

### 3.1 数据层级定义

```text
Tier 1: GOLD_STANDARD (证据等级 A)
├── 特征: 单一可靠来源，多源交叉验证
├── 用途: BLIND 数据集主体
├── 要求: 必须通过 Leakage Audit
└── 示例: fate-bench 官方答案、纪晓岚等历史名人传记

Tier 2: HIGH_CONFIDENCE (证据等级 B)
├── 特征: 可靠来源，单一证据链
├── 用途: BLIND 数据集补充
├── 要求: 必须标注来源限制
└── 示例: CBDB (需降权)、Wikipedia 可信引用

Tier 3: MODERATE_CONFIDENCE (证据等级 C)
├── 特征: 二手/三手资料
├── 用途: CALIBRATION 数据集
├── 要求: 禁止进入 BLIND
└── 示例: 命理网站案例、现代研究引用

Tier 4: LOW_CONFIDENCE (证据等级 D)
├── 特征: 传闻、未证实
├── 用途: 禁止用于 Accuracy
├── 要求: 仅作为 Evidence Reference
└── 示例: 民间传说、网络故事

Tier 5: UNSUITABLE (证据等级 X)
├── 特征: 合成数据、自证循环
├── 用途: 完全禁止
├── 要求: 明确拒绝
└── 示例: 项目生成的"黄金案例"、命理大师"预测"
```

### 3.2 分层决策规则

```text
DECISION RULES:
├── PRE_EVENT 数据集必须 ≥ Tier 2
├── HISTORICAL_BLIND 数据集必须 ≥ Tier 2
├── POST_HOC 数据集可以是 Tier 3-4
├── HOLDOUT 数据集必须 ≥ Tier 2
└── 任何 Tier 5 数据立即排除
```

---

## 四、数据集规模策略

### 4.1 分阶段目标

```text
Phase 1 (A2): 50-100 高质量历史人物 + 100-300 明确时间事件
├── 目标: 验证完整 pipeline
├── 标准: 100% provenance + 0% leakage
└── 输出: DEV + CALIBRATION 数据集

Phase 2 (A3): 扩展至 300-500 案例
├── 目标: 建立有效 Accuracy 评估
├── 标准: ≥ Tier 2 占比 > 80%
└── 输出: BLIND 数据集 + 初始 HOLDOUT

Phase 3 (A4): 扩展至 1000+ 案例
├── 目标: 统计显著性
├── 标准: 多来源独立验证
└── 输出: 正式 HOLDOUT (冻结)
```

### 4.2 规模不追求指标

```text
❌ 错误目标: "收集 10,000 案例"
✅ 正确目标: "收集 100 个 provenance 完整、leakage 为零的案例"

质量优先于规模。
一个不可靠的数据集会污染整个 V1.3 结论。
```

---

## 五、关键角色与职责

```text
ROLE DEFINITIONS:
├── Data Steward: 负责数据来源审核、证据等级判定
├── Temporal Auditor: 负责时间对齐、精度声明、时区处理
├── Leakage Analyst: 负责 L01-L12 检测、泄漏分类
├── Ontology Mapper: 负责事件→4 Domains + 17 Types 映射
├── Gate Keeper: 负责 A2.1-A2.7 各 Gate 审批
└── Holdout Guardian: 负责 HOLDOUT 冻结状态监督
```

---

## 六、禁止事项清单

```text
STRICTLY PROHIBITED:
├── ❌ 修改八字/河洛/紫微/黄历/Yi 算法
├── ❌ 根据历史案例调整参数
├── ❌ 根据 Accuracy 结果修改规则
├── ❌ 将命理"预测"作为 Ground Truth
├── ❌ 伪造精确日期（不知道就说不知道）
├── ❌ 混合多 Domain 解释同一事件
├── ❌ 让模型看到目标事件后生成预测
├── ❌ 修改 HOLDOUT 数据
└── ❌ 使用 Tier 5 数据进入任何评估
```

---

**报告结束**
**下一步**: A2.1 Dataset Source Qualification
