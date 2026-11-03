# V1.3 A2-B3 Historical Event Quality Audit Report

**日期**: 2026-08-22
**审计对象**: Historical Dataset (40 persons, 270 events)
**审计类型**: READ-ONLY Data Quality Audit
**状态**: ⚠️ CONDITIONAL — 需修复 P0/P1 问题

---

## 一、审计摘要

| 指标 | 数值 | 状态 |
|------|------|------|
| Total Persons | 59 | — |
| Persons with Events | 40 | ✅ |
| Unresolved Persons | 19 | ⚠️ UNRESOLVED |
| Total Events | 270 | — |
| Evidence Grade A | 270 (100%) | ❌  inflated |
| Oracle Grade O1 | 270 (100%) | ❌ inflated |
| Date Precision YEAR | 270 (100%) | ⚠️ no granularity |
| Leakage CLEAN | 270 (100%) | ⚠️ suspicious |

---

## 二、P0 问题 (必须修复)

### P0-1: CAREER.* 通配符滥用

**严重程度**: CRITICAL
**涉及范围**: 124/270 事件 (46%)

**问题描述**: 大量事件使用 `CAREER.*` 通配符而非具体子类型。这违反了 G1 Ontology 映射规则。

**当前分布**:
```text
CAREER.*:                    124 (46%) ← 问题
EDUCATION.GRADUATE:           58 (21%)
LIFE_EVENT.DEATH:             40 (15%)
LIFE_EVENT.SOCIAL_ACHIEVE:    37 (14%)
FAMILY.MARRIAGE:               4 (1.5%)
LIFE_EVENT.TRAUMA:             3 (1%)
LIFE_EVENT.HEALTH_CRISIS:      2 (0.7%)
LIFE_EVENT.LEGAL_ISSUE:        1 (0.4%)
FAMILY.CHILD_BIRTH:            1 (0.4%)
```

**应映射为**:
- `CAREER.CHANGE` — 任职、升迁、罢职
- `CAREER.WEALTH_CHANGE` — 创业、破产
- `CAREER.STARTUP` — 创办企业/机构
- `CAREER.POLITICAL` — 政治活动

**影响**: 无法进行 Event-Type Stratified Metrics 分析。

### P0-2: Evidence Grade 膨胀

**严重程度**: HIGH
**涉及范围**: 270/270 事件 (100%)

**问题描述**: 所有事件都标记为 Grade A（一手/权威资料），但实际上：
- 部分事件来自 Wikipedia/百度百科（应标为 Grade B）
- 部分事件来自二手研究论文（应标为 Grade B/C）
- 只有少数事件有明确的一手史料引用（如族谱、奏折）

**应重新分级**:
| Grade | 定义 | 当前 | 应调整为 |
|-------|------|------|---------|
| A | 一手/权威资料，日期明确 | 270 | ~50 |
| B | 权威二手资料，日期明确 | 0 | ~150 |
| C | 可信资料，只有年份 | 0 | ~70 |

### P0-3: Oracle Grade 膨胀

**严重程度**: HIGH
**涉及范围**: 270/270 事件 (100%)

**问题描述**: 所有事件都标记为 O1（最高 Oracle 等级），但历史人物事件本质上是 POST_HOC 记录，不是事前预测。

**应调整为**:
- O1: 有明确事前预测记录的事件（极少）
- O2: 有可靠历史记录但非事前预测（大多数）
- O3: 古典文献记载（部分）
- OX: 不可验证（部分）

---

## 三、P1 问题 (应修复)

### P1-1: 事件独立性违规

**严重程度**: MEDIUM
**涉及范围**: 多人物存在因果链事件

**问题描述**: 同一人物的多个事件存在因果关系，不是独立样本。

**示例**:
```text
张之洞:
  1850 - 中秀才
  1852 - 中举人
  1863 - 中进士
  ↑ 这是因果链，不是3个独立事件
```

**影响**: 如果将每个事件作为独立样本计算 Accuracy，会高估样本量。

**修复方案**: 
- Event-level metrics: 保留所有事件
- Person-level metrics: 每人只计1次
- Event-type stratified: 按类型分层

### P1-2: Date Precision 单一

**严重程度**: MEDIUM
**涉及范围**: 270/270 事件 (100%)

**问题描述**: 所有事件都是 YEAR 精度，没有 MONTH 或 DAY。

**原因**: 当前提取脚本只从问题文本中提取年份。

**影响**: 无法进行高精度时间对齐验证。

### P1-3: POST_HOC 污染

**严重程度**: MEDIUM
**涉及范围**: ~100 事件

**问题描述**: 部分事件描述包含回顾性措辞，如：
- "发动护国战争" — 事后命名
- "参与戊戌变法" — 事后归类
- "创办复旦公学" — 事后确认

**影响**: 这些事件的 `prediction_cutoff` 计算可能不准确。

### P1-4: Prediction Cutoff 计算过于简化

**严重程度**: LOW
**涉及范围**: 270/270 事件

**问题描述**: 所有事件的 `prediction_cutoff` 都是 `event_year - 1`，这是最简化的计算。

**应改进为**:
- 从事件描述中提取具体日期
- 考虑事件的可预测性窗口
- 对于"中进士"等事件，cutoff 应为考试前一年

---

## 四、数据质量评分

### 4.1 修正后的质量评分

```text
HISTORICAL DATA QUALITY (修正后):
├── Provenance 完整性: 270/270 (100%) — 全部有来源
├── Evidence Grade 准确性: ~50/270 (18%) — Grade A 膨胀
├── Oracle Grade 准确性: ~50/270 (18%) — O1 膨胀
├── Event Type 具体性: 146/270 (54%) — CAREER.* 过多
├── Date Precision: 270/270 (100%) — 但全部 YEAR
├── Event Independence: ~200/270 (74%) — 因果链问题
├── Leakage 清洁度: 270/270 (100%) — 但 POST_HOC 污染
└── 总体可用率: ~100/270 (37%) — 严格标准下
```

### 4.2 Accuracy-Eligible Events

```text
ACCURACY-ELIGIBLE HISTORICAL EVENTS:
├── Total Raw: 270
├── After Evidence Grade correction: ~150 (Grade A+B)
├── After Oracle Grade correction: ~100 (O1+O2)
├── After Event Type correction: ~80 (specific types)
├── After Independence check: ~60 (independent events)
└── Final Accuracy-Eligible: ~50-60 events
```

---

## 五、Unresolved Persons Registry

19 位人物标记为 `UNRESOLVED_PUBLIC_EVIDENCE`：

| Person ID | Name | Reason |
|-----------|------|--------|
| HIST-0023 | 吴景祺 | 身份歧义（清末官员 vs 1937北大学生） |
| HIST-0025 | 吴景祯 | 公开史料不足 |
| HIST-0027 | 李道溥 | 需进一步核验（有地方志资料） |
| HIST-0028 | 万庆淦 | 公开史料不足 |
| HIST-0030 | 邓维翰 | 公开史料不足 |
| HIST-0035 | 邓维垣 | 公开史料不足 |
| HIST-0037 | 黄明疆 | 公开史料不足 |
| HIST-0039 | 廖耀宗 | 现代人物，来源结构不同 |
| HIST-0043 | 廖耀华 | 公开史料不足 |
| HIST-0047 | 黄子蕴 | 公开史料不足 |
| HIST-0049 | 陈启源 | 公开史料不足 |
| HIST-0050 | 何瑞莲 | 公开史料不足 |
| HIST-0052 | 陈涌伟 | 现代海外华人 |
| HIST-0054 | 陈涌川 | 现代海外华人 |
| HIST-0055 | 陈敬南 | 现代海外华人 |
| HIST-0056 | 陈斯婷 | 现代海外华人 |
| HIST-0057 | 陈敬天 | 现代海外华人 |
| HIST-0058 | 陈斯真 | 现代海外华人 |

**状态**: `UNRESOLVED_PUBLIC_EVIDENCE`
**后续**: 找到地方志、档案、论文时可重新升级

---

## 六、决策建议

### 6.1 修复优先级

```text
P0 (必须修复):
├── 重新映射 CAREER.* 为具体子类型
├── 重新评估 Evidence Grade (A/B/C)
├── 重新评估 Oracle Grade (O1/O2/O3)
└── 更新 Source Registry

P1 (应修复):
├── 标记因果链事件
├── 改进 prediction_cutoff 计算
├── 标记 POST_HOC 事件
└── 添加 MONTH/DAY precision（如有）
```

### 6.2 数据集分层

```text
HISTORICAL DATASET LAYERS:
├── Layer 1: Accuracy-Eligible (~50-60 events)
│   ├── Grade A evidence
│   ├── O1/O2 oracle
│   ├── Specific event types
│   └── Independent events
│
├── Layer 2: Cross-Validation (~100 events)
│   ├── Grade B evidence
│   ├── O2/O3 oracle
│   └── May include causal chains
│
└── Layer 3: Reference Only (~120 events)
    ├── Grade C evidence
    ├── POST_HOC events
    └── Low precision
```

---

## 七、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│            A2-B3 HISTORICAL EVENT AUDIT                       │
├─────────────────────────────────────────────────────────────┤
│  Status:  ⚠️ CONDITIONAL FAIL                                │
│                                                              │
│  P0 Issues Found:                                            │
│    ❌ CAREER.* wildcard overuse (124 events)                 │
│    ❌ Evidence Grade inflation (all A)                       │
│    ❌ Oracle Grade inflation (all O1)                        │
│                                                              │
│  P1 Issues Found:                                            │
│    ⚠️ Event independence violations (causal chains)         │
│    ⚠️ Date precision all YEAR (no granularity)              │
│    ⚠️ POST_HOC contamination (~100 events)                  │
│    ⚠️ Prediction cutoff oversimplified                      │
│                                                              │
│  Accuracy-Eligible Events: ~50-60 (not 270)                 │
│                                                              │
│  Decision:                                                   │
│    Historical dataset needs P0 fixes before A2 Final Gate.  │
│    Current 270 events cannot be used as-is for Accuracy.    │
│    19 unresolved persons marked as UNRESOLVED.              │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A2-B3-Audit-v1
