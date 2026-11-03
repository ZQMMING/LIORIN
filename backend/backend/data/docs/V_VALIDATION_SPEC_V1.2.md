# SHUNTIAN V-Validation Specification V1.2

> **状态**: CONTRACT-FROZEN（正式冻结）  
> **冻结日期**: 2026-08-22  
> **基准版本**: V-Validation V1.0 (1af23fe) / Failure Analysis V1.1  
> **审计修正**: V1.2-Corrected (3dab6cf)
> **本轮修正**: 8项冻结前修正 + 6项契约细节修正（契约层级/L0-L4）

---

## 一、核心契约：Schema ≠ Validation Dimension

这是 V1.2 最重要的架构纪律，必须首先确立。

### 1.1 Schema（契约对象）

Schema 是**被实现、被引用、被测试的结构定义**。
一个 Schema 是一个 Python module / SQL table / JSON 模板。

### 1.2 Validation Dimension（审计观察面）

Dimension 是**用来诊断、衡量、评分的视角**。
它读取多个 Schema 的运行时数据，综合判断系统状态。

**禁止混淆**。以后任何文档出现"9个X"时，必须标注是 Schema 还是 Dimension。

---

## 二、9套 Schema（契约对象）

```text
┌─────────────────────────────────────────────────────────────┐
│  S Ch e m a  （9件套）                                      │
├─────────────────────────────────────────────────────────────┤
│  1. VALIDATION STATUS    — 系统状态的描述性枚举               │
│  2. FAILURE TAXONOMY     — 失败类型的分类体系                 │
│  3. EVENT ONTOLOGY       — 事件的领域本体（Domain/Type/Dir）  │
│  4. CANONICAL SIGNAL     — 信号的结构定义                     │
│  5. TEMPORAL EVIDENCE    — 时间证据的结构定义                 │
│  6. SEVERITY             — 事件严重度的计算规范               │
│  7. EVIDENCE CHAIN       — 证据链的完整定义                   │
│  8. RELATIONAL INTERPRET — 关系解释的LLM介入规范             │
│  9. VALIDATION DIMENSIONS— 审计维度的定义                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、9+1个 Validation Dimension（审计观察面）

```text
┌─────────────────────────────────────────────────────────────┐
│  D i m e n s i o n  （9+1个）                              │
├─────────────────────────────────────────────────────────────┤
│  1. CALCULATION         — 计算层正确性                       │
│  2. SIGNAL              — 信号生成覆盖度                     │
│  3. ONTOLOGY            — 事件本体映射精度                    │
│  4. TEMPORAL            — 时间预测精度                        │
│  5. SEVERITY            — 严重度评估质量                      │
│  6. EVIDENCE            — 证据链完整性                        │
│  7. INTERPRETATION      — 关系解释质量                        │
│  8. CROSS_ENGINE_AGREE  — 多引擎一致性                        │
│  9. DIRECTIONALITY      — 方向性正确性                        │
│  + VALIDATION STATUS    — 各Dimension的系统状态报告           │
└─────────────────────────────────────────────────────────────┘
```

**注意**: `VALIDATION STATUS` 不是第10个Dimension，而是对全部Dimension的状态汇总视图，由Dimension 1-9的运行结果聚合生成。

---

## 四、Schema 1：Validation Status

### 4.1 状态枚举

```python
VALIDATION_STATUS = {
    "NOT_IMPLEMENTED": "组件尚未实现，该Dimension不计入诊断分母",
    "NOT_EVALUABLE":   "数据不足，无法评估",
    "BLOCKED":         "因上游Schema未实现而无法继续诊断",
    "PASS":            "诊断通过，无失败记录",
    "FAIL":            "诊断失败，有明确失败记录",
    "PARTIAL":         "部分通过，标注覆盖比例",
}
```

### 4.2 Dimension 状态矩阵（V1.1基线 → V1.2目标）

| Dimension | V1.1 Status | V1.1 Score | V1.2 目标 Status | 备注 |
|-----------|-------------|------------|------------------|------|
| CALCULATION | PASS | 1.00 | PASS | 八字/河洛/紫微计算均已验证 |
| SIGNAL | PARTIAL | 0.56 | PARTIAL→PASS | Phase 3接入五大引擎信号 |
| ONTOLOGY | PARTIAL | 0.44 | PARTIAL→PASS | Phase 3扩展至三层本体 |
| TEMPORAL | BLOCKED | N/A | BLOCKED→PARTIAL | Phase 4实现时间收敛 |
| SEVERITY | NOT_IMPLEMENTED | N/A | NOT_IMPLEMENTED→PARTIAL | Phase 5实现严重度 |
| EVIDENCE | PARTIAL | 0.20 | PARTIAL→PASS | Phase 2+6建立证据链 |
| INTERPRETATION | NOT_IMPLEMENTED | N/A | NOT_IMPLEMENTED→PARTIAL | Phase 6实现Yi Engine |
| CROSS_ENGINE_AGREE | NOT_IMPLEMENTED | N/A | NOT_IMPLEMENTED→PARTIAL | Phase 5实现多引擎聚合 |
| DIRECTIONALITY | NOT_EVALUABLE | N/A | NEW: 独立Dimension | 新增，检查方向匹配 |

### 4.3 诊断公式纪律

```text
// 正式 F1（Harmonic Mean of Precision and Recall）— Micro-Averaging

// 第一步：按Dimension分别计算TP/FP/FN
For each Dimension D (Status ≠ NOT_IMPLEMENTED):
    TP_D = count(Status=PASS or Status=PARTIAL)
    FP_D = count(Status=FAIL, failure_type=FALSE_POS)
    FN_D = count(Status=FAIL, failure_type=FALSE_NEG)

// 第二步：Micro-Aggregation（所有Dimension合并计算）
TP_total = Σ TP_D
FP_total = Σ FP_D
FN_total = Σ FN_D

// 第三步：最终F1（Micro-F1）
Precision = TP_total / (TP_total + FP_total)       if (TP_total + FP_total) > 0 else 0.0
Recall    = TP_total / (TP_total + FN_total)        if (TP_total + FN_total) > 0 else 0.0
F1        = 2 × TP_total / (2 × TP_total + FP_total + FN_total)

// 禁止使用Macro-F1（各Dimension F1求平均）作为Overall F1
// Macro-F1仅作为辅助指标，不得与Overall F1混用
```

**关键规则**:
- Overall F1 = Micro-F1（先合并TP/FP/FN再计算）
- 每个Dimension的失败率 = count(failure_type) / total_events
- 只计入 Status ≠ NOT_IMPLEMENTED 的Dimension
- **禁止**: 把 NOT_IMPLEMENTED 的Dimension 当作 FAIL 计入分子/分母

// 可选辅助指标（不要混淆为 F1）
Jaccard = TP_total / (TP_total + FP_total + FN_total)
          ↑ 这就是原来版本里错误地命名为 "F1" 的公式
          如需保留，必须正式命名为 JACCARD_MATCH_RATE
```

---

## 五、Schema 2：Failure Taxonomy

### 5.1 失败类型枚举

```python
FAILURE_TYPE = {
    # 信号层
    "SIGNAL_MISSING":       "没有为该事件生成任何信号",
    "SIGNAL_FALSE_POS":     "生成了信号但实际无此事件",

    # 本体层
    "ONTOLOGY_MISMATCH":    "预测类别与实际类别不匹配",
    "DIRECTION_MISMATCH":   "方向正确但类型错误（如PROMOTION vs RESIGNATION）",

    # 时间层
    "TEMPORAL_MISMATCH":    "预测年份超出时间窗口",
    "TEMPORAL_GRANULARITY": "时间粒度不匹配（年vs月vs日）",

    # 严重度层
    "SEVERITY_MISMATCH":    "严重程度分类错误",
    "SEVERITY_MISSING":     "缺少严重程度字段",

    # 证据层
    "EVIDENCE_CHAIN_BREAK": "证据链断裂（有Claim无Source或反之）",
    "EVIDENCE_LEVEL_VIOL":  "证据跨级（跳过Level直接到Level N）",
    "EVIDENCE_NO_SOURCE":   "Claim无可追溯的来源",

    # 解释层
    "INTERPRETATION_ORPHAN":"解释无证据支撑（LLM自由发挥）",
    "INTERPRETATION_TERM":  "使用了禁止的玄学术语",

    # 多引擎
    "AGREEMENT_LOW":        "多引擎信号冲突且无裁决",

    # 计算层（理论不应失败）
    "CALCULATION_ERROR":    "引擎计算结果与参考实现不一致",
}
```

### 5.2 失败分析公式

```text
每个Dimension的失败率 = count(failure_type) / total_events

但只计入 Status ≠ NOT_IMPLEMENTED 的Dimension
```

---

## 六、Schema 3：Event Ontology

### 6.1 三层结构

```text
Domain（领域）
  └── Event Type（事件类型）
        ├── Direction（方向）
        └── Temporal Granularity（时间粒度）
```

### 6.2 Single-Parent Domain Ontology 约束

**V1.2 重要约束**: 本 Ontology 采用 **Single-Parent Domain** 设计。

```text
每个 Event Type ∈ exactly one Domain
```

即：
```python
EVENT_TYPES[i].domain 是单值，不是列表
```

**原因**:
- 简化 Validation Matching Policy 实现
- 避免 Golden Dataset 标注歧义（如 PARENT_DEATH 不应同时标注 FAMILY 和 LIFE_EVENT）
- 为未来 V1.3 预留 secondary_domain / cross_domain_tags 扩展空间

**未来扩展**（V1.3+）:
```python
# 暂不实现，仅预留结构
EVENT_TYPE_WITH_CROSS_DOMAIN = {
    "id": "PARENT_DEATH",
    "primary_domain": "FAMILY",
    "secondary_domains": ["LIFE_EVENT", "LOSS"],  # 未来支持
    "cross_domain_tags": ["death", "family_change"],  # 未来支持
}
```

### 6.3 Domain 定义（4个）

```python
DOMAIN = {
    "EDUCATION": {
        "description": "学业、考试、升学相关事件",
        "signal_pattern": "木旺/文昌/科星激活",
    },
    "CAREER": {
        "description": "职场、晋升、离职、收入变化",
        "signal_pattern": "官星/财星/印星激活",
    },
    "FAMILY": {
        "description": "婚姻、生育、家庭关系变化",
        "signal_pattern": "夫妻宫/子女宫/田宅宫激活",
    },
    "LIFE_EVENT": {
        "description": "搬迁、健康、法律等人生重大事件",
        "signal_pattern": "流迁移/疾厄/官非触发",
    },
}
```

### 6.3 Event Type 定义（17个，含Direction）

```python
EVENT_TYPES = [
    # EDUCATION (4)
    {"id": "EXAM",          "domain": "EDUCATION", "direction": "NEUTRAL", "granularity": "MONTHLY"},
    {"id": "ADMISSION",     "domain": "EDUCATION", "direction": "POSITIVE", "granularity": "YEARLY"},
    {"id": "GRADUATION",    "domain": "EDUCATION", "direction": "POSITIVE", "granularity": "YEARLY"},
    {"id": "DEGREE",        "domain": "EDUCATION", "direction": "POSITIVE", "granularity": "YEARLY"},

    # CAREER (5)
    {"id": "PROMOTION",     "domain": "CAREER",    "direction": "POSITIVE", "granularity": "YEARLY"},
    {"id": "JOB_CHANGE",    "domain": "CAREER",    "direction": "CHANGE",   "granularity": "YEARLY"},
    {"id": "RESIGNATION",   "domain": "CAREER",    "direction": "CHANGE",   "granularity": "YEARLY"},
    {"id": "DEMOTION",      "domain": "CAREER",    "direction": "NEGATIVE", "granularity": "YEARLY"},
    {"id": "MAJOR_INCOME",  "domain": "CAREER",    "direction": "POSITIVE", "granularity": "YEARLY"},

    # FAMILY (5)
    {"id": "NEW_RELATIONSHIP", "domain": "FAMILY", "direction": "POSITIVE", "granularity": "YEARLY"},
    {"id": "MARRIAGE",          "domain": "FAMILY", "direction": "POSITIVE", "granularity": "YEARLY"},
    {"id": "CHILD_BIRTH",       "domain": "FAMILY", "direction": "POSITIVE", "granularity": "YEARLY"},
    {"id": "FAMILY_CHANGE",     "domain": "FAMILY", "direction": "CHANGE",   "granularity": "YEARLY"},
    {"id": "PARENT_DEATH",      "domain": "FAMILY", "direction": "NEGATIVE", "granularity": "YEARLY"},

    # LIFE_EVENT (3)
    {"id": "RELOCATION",  "domain": "LIFE_EVENT", "direction": "CHANGE",   "granularity": "YEARLY"},
    {"id": "HEALTH_ISSUE","domain": "LIFE_EVENT", "direction": "NEGATIVE", "granularity": "YEARLY"},
    {"id": "LEGAL_ISSUE", "domain": "LIFE_EVENT", "direction": "NEGATIVE", "granularity": "YEARLY"},
]
```

### 6.4 Direction 语义

```python
DIRECTION = {
    "POSITIVE": "向有利状态演进（升级、获得、进入）",
    "NEGATIVE": "向不利状态演进（降级、失去、退出）",
    "CHANGE":   "中性状态转换（变动、迁移、替换）",
    "NEUTRAL":  "状态本身不强调方向（考试、学位）",
    "UNKNOWN":  "无法从信号判断方向",
}
```

**禁止**: 用 INCREASE/DECREASE 代替 POSITIVE/NEGATIVE。前者隐含价值判断，后者描述状态变化。

### 6.5 Validation Event Matching Policy（非Ontology Mapper）

```text
此表仅用于 V-Validation 诊断评估，不属于 Ontology 本体定义。
它描述的是：某个预测信号在 Golden Dataset 验证时，是否允许被计为匹配。
Ontology 本体（6.2-6.4）独立存在，不受此表影响。
```

| 预测信号类别 | 允许匹配的实际 Event Type（验证时计数为 Match） |
|-------------|-----------------------------------------------|
| EXAM | EXAM, GRADUATION, ADMISSION, DEGREE |
| PROMOTION | PROMOTION, MAJOR_INCOME |
| JOB_CHANGE | JOB_CHANGE, RESIGNATION, DEMOTION |
| FAMILY_CHANGE | FAMILY_CHANGE, NEW_RELATIONSHIP, MARRIAGE |
| CHILD_BIRTH_SIGNAL | CHILD_BIRTH |
| RELOCATION_SIGNAL | RELOCATION |
| HEALTH_ISSUE_SIGNAL | HEALTH_ISSUE |
| LEGAL_ISSUE_SIGNAL | LEGAL_ISSUE |

**方向校验**: 预测方向与实际事件方向不一致时标记为 `DIRECTION_MISMATCH`。

**禁止反向污染**: 此表不能反过来修改 EVENT_TYPES 的 Domain/Direction 定义。Ontology 定义优先于匹配策略。

---

## 七、Schema 4：Canonical Signal

### 7.1 Signal 结构

```python
CANONICAL_SIGNAL = {
    "signal_id":       "UUID",
    "source_engine":   "Bazi | Heluo | Ziwei | Huangli | Knowledge",
    "ontology_type":   "USO类型: ACTION|OUTPUT|CONSTRAINT|RESOURCE|SUPPORT|RELATION|REFLECTION|CHANGE",
    "event_types":     ["PROMOTION", "JOB_CHANGE"],  # 该信号可触发的Event Type列表
    "direction":       "POSITIVE|NEGATIVE|CHANGE|NEUTRAL|UNKNOWN",
    "confidence":      0.0-1.0,
    "temporal_scope": {
        "start_year":  int,
        "end_year":    int,
        "granularity": "YEARLY|MONTHLY|DAILY",
    },
    "evidence_refs":   ["evidence_id_1", "evidence_id_2"],
    "rule_refs":       ["rule_id_1"],
    "layer":           "BASELINE|CYCLE_CONTEXT|DAILY_ACTIVATION",
    "extracted_at":    "ISO8601",
}
```

### 7.2 信号源接入顺序（Phase 3）

```text
Phase 3.1: Bazi Signal（已有，接入流年/大运信号）
Phase 3.2: Knowledge Signal（基于知识库USO映射）
Phase 3.3: Huangli Signal（宜忌→USO）
Phase 3.4: Heluo Signal（卦象→USO，需Yi Engine部分就绪）
Phase 3.5: Ziwei Signal（星曜→USO，需Yi Engine部分就绪）
```

### 7.3 信号聚合策略（Phase 5，非Phase 3）

**Phase 3 只做信号提取和保存，不做聚合。**

聚合策略在 Phase 5 独立实现，当前禁止预设权重。

---

## 八、Schema 5：Temporal Evidence

### 8.1 架构约束

```text
Temporal Orchestrator（编排层）
    ├── 不拥有任何领域算法
    ├── 只定义接口：interface TemporalEngine { compute(profile, time_ref) → TimeSignal }
    └── 只负责调度各领域引擎并整合结果

BaziTimeEngine（领域引擎，独立实现，不修改）
    ├── 大运（10年周期）
    ├── 流年（每年）
    └── 流月/流日/流时

HeluoTimeEngine（领域引擎，独立实现，不修改）
    ├── 本命 → 元堂 → 后天 → 流年/月/日/时
    ├── 节候卦
    └── 卦气时间链

ZiweiTimeEngine（领域引擎，独立实现，不修改）
    ├── 大限（10年）
    ├── 流年
    └── 流月/流日
```

### 8.2 Temporal Signal 结构

```python
TEMPORAL_SIGNAL = {
    "engine":          "Bazi | Heluo | Ziwei",
    "time_type":       "DAYUN | LIUNIAN | LIUYUE | LIRI | LISHI | JIEHOU_GUA | GUAQI",
    "year":            int,
    "month":           int | None,
    "day":             int | None,
    "hour":            int | None,
    "window": {
        "start": "ISO8601",
        "end":   "ISO8601",
    },
    "signals":         [signal_id_1, signal_id_2],  # 该时间窗内的信号引用
    # 注意：convergence 不在 TEMPORAL_SIGNAL 内，见下文 TEMPORAL_CONVERGENCE
}
```

### 8.3 Temporal Convergence（独立于 Temporal Signal）

```python
TEMPORAL_CONVERGENCE = {
    "case_id":                "UUID",
    "time_reference":         {"year": int, "month": int | None, "day": int | None},
    "participating_engines":  ["Bazi", "Heluo", "Ziwei"],
    "overlapping_window": {
        "start": "ISO8601",
        "end":   "ISO8601",
    },
    "overlap_ratio":          0.0-1.0,
    "convergence_score":      0.0-1.0,  # 综合各引擎时间信号的一致性
    "signal_ids_by_engine": {
        "Bazi":  ["sig_1", "sig_2"],
        "Heluo": ["sig_3"],
        "Ziwei": ["sig_4", "sig_5"],
    },
}
```

**架构原则**: Temporal Signal 是各领域引擎的独立输出。Temporal Convergence 由 Temporal Orchestrator 聚合生成，不得嵌入单个 Temporal Signal 中。

### 8.3 时间窗口策略（严格区分两种窗口）

```text
【概念定义】
Prediction_Window:
  - 由系统 Temporal Engine 计算得出，代表系统预测的时间范围
  - 格式: {"start": "ISO8601", "end": "ISO8601"}
  - 例: {"start": "2027-03-01", "end": "2027-08-31"}
  - 由 Canonical Signal 和 Temporal Evidence 合成

Evaluation_Tolerance_Window:
  - 由验证体系定义，代表"什么才算正确"的判断宽容度
  - 格式: {"offset_start": "-N months/years", "offset_end": "+N months/years"}
  - 例: EXAM ±3个月, PROMOTION ±1年
  - 仅用于 Validation Dimension 的 TEMPORAL_MATCH 判断
  - 不可反向影响系统预测，避免 Evaluation Leakage
```

```text
每个 Event Type 有固定 temporal_granularity：
- MONTHLY 型（EXAM）:  评估宽容度 = ±3个月
- YEARLY  型（PROMOTION, MARRIAGE等）: 评估宽容度 = ±1年（初始），随Temporal Engine成熟可收紧

⚠️ 重要: 评估宽容度不是系统预测结果的扩展窗口
  系统预测的结果必须来自 Calculation → Signal → Temporal Evidence 链路
  Evaluation_Tolerance_Window 仅用于判断"预测是否命中"
```

---

## 九、Schema 6：Severity

### 9.1 分离两个概念

```text
┌─────────────────────────────────────────────────────────────┐
│  Evidence Completeness（证据完整度）                        │
│  ─────────────────────────────────                          │
│  仅基于证据链本身，不依赖 LLM 可用性：                         │
│                                                             │
│  Evidence_Completeness =                                    │
│      source_completeness × passage_completeness             │
│    × claim_traceability × evidence_level_completeness       │
│    × signal_traceability                                    │
│                                                             │
│  各子项定义：                                                 │
│  - source_completeness     : 该证据是否有可追溯的SOURCE        │
│  - passage_completeness    : SOURCE是否有完整PASSAGE引用      │
│  - claim_traceability      : CLAIM是否可追溯至PASSAGE        │
│  - evidence_level_completeness : 每级Evidence是否有level标注  │
│  - signal_traceability     : SIGNAL是否追溯至EVIDENCE       │
│                                                             │
│  用途: 告诉我们\"证据链本身有多完整\"                           │
│  与LLM可用性完全无关                                          │
├─────────────────────────────────────────────────────────────┤
│  Interpretation Availability（解释能力可用性）               │
│  ─────────────────────────────────                          │
│  描述系统是否已具备处理证据链的能力                            │
│                                                             │
│  Interpretation_Available =                                  │
│      LLM_engine_ready (bool)                                  │
│    × evidence_chain_readable (bool)                           │
│                                                             │
│  用途: 告诉我们\"系统现在能否解释这些证据\"                     │
│  与Evidence Completeness完全分离                              │
├─────────────────────────────────────────────────────────────┤
│  Event Severity（事件严重度）                               │
│  ──────────────────────────                                 │
│  仅基于已验证的客观证据计算                                   │
│  不依赖Interpretation或Relational Coherence                 │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 Event Severity 公式（冻结）

```python
Event_Severity = (
    signal_strength       × 0.20    # 信号强度置信度
  + temporal_convergence  × 0.15    # 多引擎时间收敛度
  + ontology_specificity  × 0.20    # 预测类别具体程度
  + evidence_quality      × 0.25    # 证据可信度等级
  + agreement_evidence    × 0.20    # 多引擎一致性证据
)

# 权重总和 = 0.20 + 0.15 + 0.20 + 0.25 + 0.20 = 1.00
# 每个因子范围 [0, 1]
# 结果范围 [0, 1]
# 使用加权算术平均（weighted arithmetic mean），不使用加权乘积
```

**输入来源约束**:
- `signal_strength` ← Schema 4 (Canonical Signal)
- `temporal_convergence` ← Schema 5 (Temporal Convergence)
- `ontology_specificity` ← Ontology Specificity Policy V1（见14.1）
- `evidence_quality` ← Evidence Quality Policy V1（见14.2）
- `agreement_evidence` ← Agreement Evidence Engine（原始计算对象，非Validation输出）

**禁止循环依赖**:
```text
✗ 禁止读取 Validation Dimension CROSS_ENGINE_AGREE 的输出作为 Severity 输入
✓ 正确: 从 Agreement Evidence Engine 直接获取原始计算结果
```

**架构边界**:
```text
                    ┌──→ CROSS_ENGINE_AGREE Dimension（仅诊断）
                    │
Signal ─→ Agreement Evidence Engine
                    │
                    └──→ Severity Engine
```

#### 14.1 Ontology Specificity Policy V1（冻结）

```python
ONTOLOGY_SPECIFICITY_POLICY = {
    "version": "V1",
    "definition": "由EVENT_ONTOLOGY层级确定，不由Validation结果确定",
    "source": "Schema 3 (Event Ontology)",
    "range": [0.0, 1.0],
    "calculation": {
        "DOMAIN_ONLY":           0.25,  # 仅Domain（如CAREER）
        "DOMAIN + EVENT_TYPE":   0.75,  # Domain+Type（如CAREER:PROMOTION）
        "DOMAIN + EVENT_TYPE + DIRECTION": 0.90,  # 含方向
        "DOMAIN + EVENT_TYPE + DIRECTION + GRANULARITY": 1.00,  # 完整
    },
    "policy_file": "tongshu/spec/ontology_specificity_policy_v1.py",
}
```

**关键规则**:
- ontology_specificity 由 EVENT ONTOLOGY 结构决定，不是 Validation 输出
- 禁止通过修改 Ontology 来人为调整 Severity 分数

#### 14.2 Evidence Quality Policy V1（冻结）

```python
EVIDENCE_QUALITY_POLICY = {
    "version": "V1",
    "definition": "链条中证据本身的可信度/等级质量，非链条完整度",
    "source": "Schema 7 (Evidence Chain)",
    "range": [0.0, 1.0],
    
    # Evidence Quality ≠ Evidence Completeness
    # Completeness = 链条是否完整（5个子项乘积）
    # Quality = 每条证据的可信等级（由verification_status等决定）
    
    "quality_factors": [
        {"factor": "source_verification", "weight": 0.30, "description": "SOURCE是否VERIFIED"},
        {"factor": "passage_verification", "weight": 0.25, "description": "PASSAGE是否VERIFIED"},
        {"factor": "claim_support_score", "weight": 0.25, "description": "CLAIM的支持强度"},
        {"factor": "evidence_verification", "weight": 0.20, "description": "EVIDENCE是否verified"},
    ],
    "forbidden_formulas": [
        "evidence_level / 4",  # LEVEL_1不必然比LEVEL_4"质量高"
        "LEVEL_NUMBER / TOTAL_LEVELS",  # 等级编号≠质量
    ],
    "policy_file": "tongshu/spec/evidence_quality_policy_v1.py",
}
```

**关键规则**:
- Evidence Quality 是"可信度"，Evidence Completeness 是"完整性"
- LEVEL_1（经典原点）与 LEVEL_4（结构推导）是不同性质证据，不能简单按编号排序
- 必须追溯至 SOURCE/PASSAGE/EVIDENCE 的 verification_status 综合计算

### 9.3 Severity 分级

```python
SEVERITY_CLASS = {
    "LOW":       {"range": [0.0,  0.3], "label": "低关注"},
    "MODERATE":  {"range": [0.3,  0.6], "label": "中等关注"},
    "HIGH":      {"range": [0.6,  0.85],"label": "高度关注"},
    "CRITICAL":  {"range": [0.85, 1.0], "label": "临界关注"},
}
```

### 9.4 Interpretation Quality（与Severity分离）

```python
# Phase < 6: NOT_EVALUABLE
# Phase ≥ 6: Yi Engine 就绪后可计算

Interpretation_Quality = (
    evidence_chain_completeness × 0.40
    + source_attribution        × 0.25
    + relational_coherence      × 0.35   # 仅在 Phase 6 后可用
)
# 权重总和 = 0.40 + 0.25 + 0.35 = 1.00
# Phase < 6 时: relational_coherence = NOT_EVALUABLE
#              → Interpretation_Quality = NOT_EVALUABLE
```

**关键架构边界**:
- `Event Severity` 仅使用 Schema 1-6 的输出（Canonical Signal / Temporal Evidence / Evidence Chain）
- `Interpretation Quality` 在 Phase 6 后可引用 `relational_coherence`
- `Interpretation Availability` 描述系统状态，不影响任何计算值
- **禁止**: Validation Dimension 的输出（如 CROSS_ENGINE_AGREE）不得反向成为 Severity 或 Interpretation 的输入

---

## 十、Schema 7：Evidence Chain

### 10.1 五级证据结构（含 Claim 层）

```text
SOURCE（来源）
   ↓
PASSAGE（原文段落）
   ↓
CLAIM（主张：原文表达了什么）
   ↓
EVIDENCE（证据：支持/反对某预测）
   ↓
SIGNAL（信号：从证据中提取的预测信号）
```

### 10.2 SOURCE 定义

```python
SOURCE = {
    "source_id":          "UUID",
    "title":              "string",           # 书名/篇名
    "author":             "string | None",    # 作者（如无则None）
    "edition":            "string",           # 版本标识（如"王弼注本"）
    "publisher":          "string | None",    # 出版社/整理者
    "publication_year":   int | None,         # 出版/成书年份
    "source_type":        "PRIMARY | COMMENTARY | SECONDARY",
    "verification_status":"VERIFIED | PENDING | REJECTED",
    # PRIMARY  = 经典原典（《周易》经文、《说卦传》等）
    # COMMENTARY = 后世注疏（王弼、程颐、朱熹、来知德等）
    # SECONDARY  = 现代研究汇编
}
```

### 10.3 PASSAGE 定义

```python
PASSAGE = {
    "passage_id":       "UUID",
    "source_ref":       "FK → SOURCE.source_id",
    "chapter":          "string",             # 篇/章/卷名
    "location_ref":     "string",             # 具体位置（如"乾卦·初九"）
    "original_text":    "string",             # 原文内容
    "edition":          "string",             # 引用版本
    "evidence_level":   "LEVEL_1 | LEVEL_2 | LEVEL_3 | LEVEL_4",
    "verification_status":"VERIFIED | PENDING | REJECTED",
    # 注意：LEVEL_5 不进入 PASSAGE，见 10.7
}
```

**PASSAGE 是经典原文进入 Evidence 系统的最小可审计单位。**

### 10.4 CLAIM 定义

```python
CLAIM = {
    "claim_id":       "UUID",
    "passage_ref":    "FK → PASSAGE.passage_id",
    "claim_text":     "主张文本（自然语言）",
    "claim_type":     "DESCRIBE_STATE | PREDICT_TENDENCY | WARN_RISK | RECOMMEND_ACTION",
    "evidence_level": "LEVEL_1 | LEVEL_2 | LEVEL_3 | LEVEL_4",  # 不含LEVEL_5
    "support_score":  0.0-1.0,
    "created_by":     "HUMAN | RULE_ENGINE",  # 正式Claim禁止LLM直接生成
    "created_at":     "ISO8601",
}
```

**禁止**: LLM 生成正式 CLAIM。CLAIM 必须由 Rule Engine 从 PASSAGE 推导。

### 10.5 EVIDENCE 定义

```python
EVIDENCE = {
    "evidence_id":      "UUID",
    "claim_ref":        "FK → CLAIM.claim_id",
    "evidence_level":   "LEVEL_1 | LEVEL_2 | LEVEL_3 | LEVEL_4",
    "support_type":     "SUPPORT | CONTRADICT | CONTEXT",
    "support_score":    0.0-1.0,
    "provenance_refs":  ["passage_id_1", "passage_id_2", ...],
    "verified":         bool,
}
```

### 10.6 SIGNAL（证据链末端）

```python
# SIGNAL 在 Schema 4（Canonical Signal）中定义
# 此处仅说明其在 Evidence Chain 中的位置关系：
#   EVIDENCE → FK → EVIDENCE.evidence_id → CANONICAL_SIGNAL.evidence_refs
```

### 10.7 Evidence Level 重新定义（V1.2 修正）

```python
EVIDENCE_LEVEL = {
    "LEVEL_1": {
        "name": "经典原点",
        "type": "PRIMARY_CLASSICAL_SOURCE",
        "sources": ["《周易》经文（通行本）", "《说卦传》"],
        "requirement": "标注完整（书名/章节/版本），单源可信",
        "cross_verify_required": False,
        "note": "仅限确定属于经典原典体系的经传文本"
    },
    "LEVEL_2": {
        "name": "经典语境",
        "type": "INTERNAL_CLASSICAL_CONTEXT",
        "sources": ["同一卦在《易经》其他位置的用法", "卦序关系", "综卦/错卦关系", "经传互证"],
        "requirement": "来自《易经》内部结构交叉",
        "cross_verify_required": True,
    },
    "LEVEL_3": {
        "name": "注疏传统",
        "type": "COMMENTARY_TRADITION",
        "sources": ["王弼注", "程颐《易程传》", "朱熹《周易本义》", "来知德《周易集注》", "《周易折中》"],
        "requirement": "标注注家+出处+原文引用；《周易折中》属清代汇编，归入此类而非Level 1",
        "cross_verify_required": False,
    },
    "LEVEL_4": {
        "name": "结构推导",
        "type": "DERIVED_STRUCTURAL_REASONING",
        "sources": ["卦体分析", "爻位关系", "互体", "卦变"],
        "requirement": "必须追溯至Level 1-3的原文支撑",
        "cross_verify_required": False,
    },
    "LEVEL_5": {
        "name": "现代映射",
        "type": "MODERN_MAPPING",
        "sources": ["生活场景类比"],
        "requirement": "不可用于正式证据链，仅用于LLM补充解释",
        "forbidden_in_formal_chain": True,
        "allowed_as_interpretive_supplement": True,
    },
}
```

**关键规则**:
- 正式 CLAIM / PASSAGE / EVIDENCE 的 `evidence_level` 只能取 LEVEL_1 ~ LEVEL_4
- LEVEL_5 仅作 Interpretive Supplement（解释性补充），不得进入 Canonical Evidence Chain
- 《周易折中》属于清代汇编，归入 LEVEL_3（注疏传统），**不得**与《周易》经文并列于 LEVEL_1

### 10.3 Claim 定义

```python
CLAIM = {
    "claim_id":      "UUID",
    "passage_ref":   "FK → PASSAGE.passage_id",
    "claim_text":    "主张文本（自然语言）",
    "claim_type":    "DESCRIBE_STATE | PREDICT_TENDENCY | WARN_RISK | RECOMMEND_ACTION",
    "evidence_level": "LEVEL_1 | LEVEL_2 | LEVEL_3 | LEVEL_4",  # 不含LEVEL_5
    "support_score":  0.0-1.0,          # 该主张被支持的强度
    "created_by":    "HUMAN | RULE_ENGINE",  # 正式Claim禁止LLM直接生成
    "created_at":    "ISO8601",
}
```

**禁止**: LLM 生成正式 CLAIM。 CLAIM 必须由 Rule Engine 从 PASSAGE 推导。

**CLAIM_DRAFT（非正式占位符）**:
```python
CLAIM_DRAFT = {
    "draft_id":      "UUID",
    "passage_ref":   "FK → PASSAGE.passage_id",
    "draft_text":    "草稿主张文本",
    "draft_source":  "LLM | HUMAN_DRAFT",
    "review_status": "PENDING_REVIEW | APPROVED | REJECTED",
    # 仅 APPROVED 的 DRAFT 可经 Rule Engine canonicalization 后成为正式 CLAIM
}
```
**正式 Evidence Chain 中永远只能出现 Canonical Claim（created_by = HUMAN | RULE_ENGINE）。**

### 10.4 第六条铁律：Evidence ≠ Prediction

```text
Classical Evidence
      ↓
Claim（主张：原文表达了什么倾向）
      ↓
Interpretive Mapping（解释性映射：该主张对应什么生活领域）
      ↓
Signal（信号：可被预测引擎使用的结构化输出）
      ↓
Event Ontology（事件本体：信号映射到具体事件类型）
      ↓
Prediction（最终预测）
```

**禁止路径**:
```text
✗ 经典原文 → 直接预测（跳过Claim/Mapping/Signal三层）
✗ LLM自由解读原文 → 预测结果
✗ 单条爻辞 → 确定性事件断言
```

---

## 十一、Schema 8：Relational Interpretation

### 11.1 LLM 介入点约束

```python
RELATIONAL_INTERPRETATION_CONSTRAINTS = {
    "input": "只能消费 InterpInput，禁止直接访问 CalculationContext",
    "forbidden": [
        "玄学术语（'官鬼'、'忌神'、'冲合'等）",
        "自由联想（从爻辞跳到不相关的生活场景）",
        "确定性断言（'你一定会升职'）",
        "评分式输出（'事业得分85分'）",
    ],
    "required": [
        "evidence_references: 每条结论必须引用具体证据ID",
        "interpretation_chain: 说明推理过程（Signal→State→Opportunity/Risk）",
        "state_description: 描述当前整体态势（非分类标签）",
    ],
}
```

### 11.2 InterpInput 结构

**架构约束**: Interpretation 层禁止消费 CalculationContext。
只能消费已经过 Canonicalization 的结构化输出。

```python
INTERP_INPUT = {
    # 唯一标识，不含计算细节
    "subject": {
        "profile_id": "UUID",
        "birth_date": "date",
        "gender":     "M|F|other",
    },
    # 这些是 Canonical Signal（已计算并规范化），不是原始计算结果
    "canonical_signals": [CanonicalSignal, ...],
    # Temporal Evidence（已独立Schema定义）
    "temporal_evidence": TemporalSignal | None,
    # Temporal Convergence（独立Schema）
    "temporal_convergence": TemporalConvergence | None,
    # Event Severity（已计算）
    "severity": float,
    # Evidence Chain（完整追溯）
    "evidence_chain": [EvidenceNode, ...],
    # 上一轮 Relational Interpretation 输出（当前态势）
    "current_state_summary": "string",
}
```

**禁止字段（InterpInput 不得包含）**：
```python
# ❌ bazi_pillars       — CalculationContext 原始输出，LLM不得消费
# ❌ heluo_hexagram     — 同上
# ❌ ziwei_ming_gong    — 同上
# ❌ any raw calculation — 任何未经 Canonicalization 的计算中间态
```

**架构原则**: LLM 只能吃已经计算完成并经过 Canonicalization 的结果，不吃计算原料。

### 11.3 输出格式

```python
INTERP_OUTPUT = {
    "state":           "当前整体态势描述",
    "opportunities":   [{"area": "...", "description": "...", "evidence_refs": [...]}],
    "risks":           [{"area": "...", "description": "...", "evidence_refs": [...]}],
    "action_tendency": "建议行动倾向（非强制指令）",
    "remediation":     "可选补救措施",
    "confidence_note": "本解释的置信度说明",
}
```

---

## 十二、Schema 9：Validation Dimensions

### 12.1 9个维度定义

```python
VALIDATION_DIMENSIONS = {
    "CALCULATION": {
        "description": "八字/河洛/紫微计算正确性",
        "check": "与外部参考实现对比",
        "status_source": "PASS if 所有engine结果与参考一致",
    },
    "SIGNAL": {
        "description": "信号生成覆盖度",
        "check": "Golden Dataset中每个实际事件是否有对应信号",
        "metric": "signal_coverage_rate = matched_signals / total_events",
    },
    "ONTOLOGY": {
        "description": "事件本体映射精度",
        "check": "预测类别能否映射到实际类别",
        "metric": "ontology_match_rate = matched_categories / total_events",
    },
    "TEMPORAL": {
        "description": "时间预测精度",
        "check": "预测时间窗口是否覆盖实际事件时间",
        "metric": "temporal_match_rate = events_in_window / total_events",
    },
    "SEVERITY": {
        "description": "严重度评估质量",
        "check": "预测严重度与事件实际影响程度是否一致",
        "metric": "severity_accuracy = correctly_classified / total_events",
    },
    "EVIDENCE": {
        "description": "证据链完整性",
        "check": "每条预测是否有可追溯的证据链",
        "metric": "evidence_completeness_rate = predictions_with_full_chain / total_predictions",
    },
    "INTERPRETATION": {
        "description": "关系解释质量",
        "check": "LLM解释是否有证据支撑，是否违反约束",
        "metric": "interpretation_quality_score（人工评估）",
    },
    "CROSS_ENGINE_AGREE": {
        "description": "多引擎一致性",
        "check": "不同引擎对同一事件的信号是否收敛",
        "metric": "agreement_rate = engines_agreeing / total_engines",
    },
    "DIRECTIONALITY": {
        "description": "方向性正确性",
        "check": "预测方向与实际事件方向是否一致",
        "metric": "direction_accuracy = correct_direction / total_directional_events",
    },
}
```

### 12.2 Validation Status 汇总

由上述9个Dimension的运行结果生成：

```python
VALIDATION_STATUS_REPORT = {
    "frozen_at": "ISO8601",
    "dimension_statuses": {dim: Status for dim in VALIDATION_DIMENSIONS},
    "overall_f1": float | None,
    "overall_precision": float | None,
    "overall_recall": float | None,
    "architecture_acceptance": {
        "contract_compliance": bool,
        "reference_integrity": bool,
        "no_orphan_references": bool,
        "no_illegal_layer_access": bool,
        "no_calculation_regression": bool,
    },
    "validation_targets": {
        "signal_coverage_target": 0.70,
        "temporal_miss_target": 0.40,
        "ontology_miss_target": 0.30,
        "evidence_completeness_target": 0.60,
    },
    "stretch_goal": {
        "f1_target": 0.30,
        "note": "F1≥30%为Stretch Goal，非硬验收门槛",
    },
}
```

---

## 十三、五道铁律（+第六条）

```text
铁律 ①: NOT_IMPLEMENTED / NOT_EVALUABLE / BLOCKED 必须与 FAIL 严格分离
        → 未实现的组件不参与诊断分母，不能伪装成通过

铁律 ②: Golden Dataset 是验证夹具，不是 Ontology 的唯一来源
        → 数据集数量≠本体粒度，不能让10个样本事件定义10类系统本体

铁律 ③: Temporal Orchestrator 不得拥有或重写 Bazi/Heluo/Ziwei 的领域算法
        → 编排层只调度，不实现

铁律 ④: Severity 不能把"系统没实现"误判成"事件严重度为0"
        → Evidence Completeness 与 Event Severity 分离

铁律 ⑤: Yi Engine 是 Interpretation/Evidence 基础设施，不是预测分类器
        → 优先级在 Signal/Ontology/Temporal/Severity 之后

铁律 ⑥: Evidence 不得直接等同于 Prediction
        → 经典原文必须经过 Claim → Mapping → Signal 三层才能进入预测
        → 禁止 LLM 自由解读原文直接输出预测结果

铁律 ⑦: Validation Layer 必须是只读观察层
        → Validation 不得修改：Calculation Result、Canonical Signal、Event Ontology
        → Validation 不得修改：Temporal Engine Output、Evidence Chain、Prediction
        → Validation 不得允许 Golden Dataset 反向污染 Ontology
        → 任何发现都必须以 FAILURE_ANALYSIS 报告形式输出，由人工审核后决定是否触发修正流程
```

---

## 十四、Phase 执行计划（修订版）

### Phase 0 — 审计修正 ✓ 已完成

修正V1.1原报告的7项核心判断错误。

---

### Phase 1 — V-Validation 契约冻结 ⏳ 进行中

**目标**: 生成并冻结 `V_VALIDATION_SPEC_V1.2.md`

**产出**: 本文件 + 各Schema的Python实现骨架（类型定义，无业务逻辑）

**冻结原则**: 本文件经人工审查通过后，进入正式冻结状态。之后任何修改必须走变更流程。

---

### Phase 2 — Evidence / Knowledge Foundation

**目标**: 建立完整的经典证据基础

**关键约束**:
- 《周易》原文注册：纸质书扫描/权威数据库 → 人工核验 → 入库
- **禁止LLM生成经典原文**
- 每条 PASSAGE 必须包含：source / edition / chapter / passage / evidence_level
- CLAIM 由 Rule Engine 从 PASSAGE 推导，禁止 LLM 生成 CLAIM

**产出**:
- `zhoubi/` 知识库表结构 + 数据
- `claim_registry.py` — Rule Engine驱动的Claim推导
- Evidence Registry（支持source_tracing / level_classification / cross_verification）

---

### Phase 3 — Canonical Signal + Event Ontology

**目标**: 打通五大引擎信号 + 建立三层事件本体

**产出**:
- `tongshu/reasoning/canonical_signal_engine.py`（仅提取，不聚合）
- `tongshu/spec/event_ontology_v1.py`（Domain/Type/Direction/Granularity）
- Directionality 检查模块

---

### Phase 4 — Temporal Engine

**目标**: 实现时间编排层

**产出**:
- `tongshu/engines/temporal_orchestrator.py`（接口定义+调度，无领域算法）
- BaziTimeEngine / HeluoTimeEngine / ZiweiTimeEngine 的封装适配层
- Temporal Convergence 计算

---

### Phase 5 — Severity + Cross-Engine Agreement

**目标**: 实现严重度评估 + 多引擎聚合

**产出**:
- `tongshu/reasoning/severity_engine.py`
- `tongshu/reasoning/agreement_engine.py`
- Signal Aggregation（证据保留式，非权重投票式）

---

### Phase 6 — Yi Engine + Relational Interpretation

**目标**: 实现六十四卦结构分析 + LLM关系解释

**产出**:
- `tongshu/reasoning/yi_engine.py`（四层：HexagramSymbol/LineSymbol/ClassicalText/ImageExpansion）
- LLM Prompt（含约束）
- Evidence Chain 完整验证

---

### Phase 7 — V-Validation V2 重新运行

**目标**: 验证修复效果

**验收标准**:
- Architecture Acceptance: 全部硬约束通过
- Validation Target: 预期趋势改善
- F1 ≥ 30%: Stretch Goal（非硬门槛）

---

## 十五、文档索引

```text
docs/
├── V_VALIDATION_SPEC_V1.2.md              ← 本文件（9套Schema + 7铁律 + Golden三层 + 四链）
├── V_VALIDATION_ARCHITECTURE_AUDIT_V1.2.md             ← V1.2原审计（参考）
├── V_VALIDATION_ARCHITECTURE_AUDIT_V1.2_CORRECTED.md   ← V1.2修正版（参考）
├── VALIDATION_FAILURE_ANALYSIS_V1.1.md        ← V1.1诊断报告（参考）
├── V1.1_FAILURE_ANALYSIS_PLAN.md              ← V1.1诊断方案（参考）
├── VALIDATION_REPORT_V1.md                    ← V1.0验证报告（参考）
└── VALIDATION_FAILURE_ANALYSIS_V1.md          ← V1.0失败分析（参考）
```

---

## 十六、Golden Dataset 三阶分层

Golden Dataset 中的每个案例必须明确区分以下三层，禁止直接将标注标签作为本体事实。

```text
OBSERVED FACT（观测事实）
  ↓ 人工标注（不进入系统计算）
ANNOTATION（标注层）
  ↓ 映射规则
CANONICAL EVENT（规范事件）
```

### 16.1 Observed Fact

```python
OBSERVED_FACT = {
    "fact_id":          "UUID",
    "case_id":          "FK → case",
    "fact_text":        "原始事实描述（自然语言）",
    "fact_date":        "ISO8601",
    "fact_source":      "verified_record | newspaper | biography | etc.",
    "fact_reliability": "HIGH | MEDIUM | LOW",
    # 不含任何 Ontology 标签
}
```

### 16.2 Annotation（人工标注）

```python
ANNOTATION = {
    "annotation_id":  "UUID",
    "fact_id":        "FK → observed_fact",
    "event_type":     "PROMOTION | JOB_CHANGE | ...",  # 审核者标注
    "direction":      "POSITIVE | NEGATIVE | CHANGE | NEUTRAL",
    "annotator":      "human_id",
    "annotated_at":   "ISO8601",
    "confidence":     0.0-1.0,  # 标注者自身置信度
    "mapping_policy_version": "V1.2",  # 标注时使用的映射规则版本，用于审计可重复性
}
```

### 16.3 Canonical Event（系统使用的规范事件）

```python
CANONICAL_EVENT = {
    "event_id":           "UUID",
    "case_id":            "FK → case",
    "observed_fact_id":   "FK → observed_fact",
    "annotation_id":      "FK → annotation",
    "event_type":         "USO类型事件",
    "direction":          "POSITIVE|NEGATIVE|CHANGE|NEUTRAL|UNKNOWN",
    "temporal_window":    {"start": "...", "end": "..."},
    "severity_class":     "LOW|MODERATE|HIGH|CRITICAL",
    "evidence_refs":      ["evidence_id_1"],
    "verified":           bool,
    # 以下字段来自人工核验，不作为系统预测结果：
    "actual_severity_class": "LOW|MODERATE|HIGH|CRITICAL|UNKNOWN",
    "canonicalization_version": "V1.2",  # 映射规则版本，用于审计可重复性
}
```

**关键区分**:
- `severity_class`: 由系统 Severity Engine 根据 Schema 6 计算得出（预测值）
- `actual_severity_class`: 由人工根据 Observed Fact 内容核验得出（Ground Truth）
- 两者必须分离存储，禁止混用

**禁止**: 将 `CANONICAL_EVENT.event_type` 反向定义或修改 `EVENT_TYPES`（Schema 3）的本体定义。

---

## 十八、契约层级定义（L0-L4）

### 18.1 层级结构

```text
L0 — DATA CONTRACT
     SOURCE / PASSAGE / CLAIM / EVENT 等数据结构

L1 — DOMAIN ENGINE CONTRACT
     Bazi / Heluo / Ziwei / Huangli / Knowledge

L2 — REASONING POLICY
     Signal / Ontology / Temporal / Severity / Agreement

L3 — INTERPRETATION CONTRACT
     Yi Engine / Relational Interpretation

L4 — VALIDATION CONTRACT
     Validation Dimensions / Golden / Failure Analysis
```

### 18.2 权限边界

```text
L4 不得修改 L0-L3
```

**具体禁止**:
- Validation 不得修改：Calculation Result (L1)
- Validation 不得修改：Canonical Signal (L2)
- Validation 不得修改：Event Ontology (L2)
- Validation 不得修改：Temporal Engine Output (L2)
- Validation 不得修改：Evidence Chain (L0)
- Validation 不得修改：Prediction (L2)
- Validation 不得允许 Golden Dataset 反向污染 Ontology (L2)

### 18.3 第七条铁律（结构性权限边界）

```text
铁律 ⑦: Validation Layer 必须是只读观察层
        → Validation 不得修改：Calculation Result、Canonical Signal、Event Ontology
        → Validation 不得修改：Temporal Engine Output、Evidence Chain、Prediction
        → Validation 不得允许 Golden Dataset 反向污染 Ontology
        → 任何发现都必须以 FAILURE_ANALYSIS 报告形式输出，由人工审核后决定是否触发修正流程
```

**架构意义**:
- 第七条铁律不再是"一句文档规定"，而是结构性的权限边界
- L4 → L0-L3 的数据流只能是单向读取
- 任何修正必须走显式变更流程：FAILURE_ANALYSIS → 人工审核 → V1.2.x 变更记录

### 18.4 完整数据流图

```text
                 ┌──────────────────────────┐
                 │      CALCULATION CHAIN    │
                 │ Profile → Engines → Calc  │
                 └────────────┬─────────────┘
                              ↓
                       Canonicalization
                              ↓
                 ┌──────────────────────────┐
                 │       REASONING CHAIN    │
                 │ Signal → Ontology → Time │
                 │ → Agreement → Severity   │
                 │ → Yi → Interpretation    │
                 └────────────┬─────────────┘
                              │
                              │ Evidence refs
                              ↓
                 ┌──────────────────────────┐
                 │       EVIDENCE CHAIN     │
                 │ Source → Passage → Claim │
                 │ → Evidence → Signal      │
                 └──────────────────────────┘

Observed Fact
      ↓
Annotation
      ↓
Canonical Event
      ↓
Prediction
      ↓
Matching Policy
      ↓
┌──────────────────────────┐
│    VALIDATION CHAIN      │
│ Dimensions → Status      │
│ → Failure Analysis      │
└──────────────────────────┘

Validation Chain
       │
       │ READ ONLY
       ↓
Calculation / Reasoning / Evidence
```

```text
① Calculation Chain（计算链）
User Profile → Bazi/Heluo/Ziwei → Calculation Result
不可被 LLM 修改

② Evidence Chain（证据链）
Source → Passage → Claim → Evidence → Signal
每一级都有 provenance

③ Reasoning Chain（推理链）
Canonical Signal → Ontology → Temporal Evidence →
Cross-Engine Agreement → Severity → Yi Structure →
Relational Interpretation
LLM只在最后的 Interpretation 边界介入

④ Validation Chain（验证链）
Observed Fact → Annotation → Canonical Event →
Prediction → Event Matching Policy →
Validation Dimensions → Validation Status → Failure Analysis
```

---

*V_VALIDATION_SPEC_V1.2 — 生成于 2026-08-22*  
*基于18条裁决 + 冻结前8项修正 + 6项契约细节修正（契约层级/L0-L4）*  
*当前状态: CONTRACT-FROZEN（正式冻结）*  
*冻结日期: 2026-08-22*  
*变更政策: 任何修改必须走 V1.2.x 变更记录或 V1.3 契约修订*  
*修正清单:*
*- ①F1公式改标准F1（Micro-Averaging）*
*- ②Evidence Chain五节点完整Schema*
*- ③《周易折中》归入Level 3*
*- ④Level 5禁止进入Canonical*
*- ⑤Severity Ground Truth分离*
*- ⑥Temporal Window严格区分预测与评估*
*- ⑦Interpretation Quality公式修正+Phase 6门槛*
*- ⑧Event Type数量17*
*- ⑨Overall F1定义（Micro-F1）*
*- ⑩Agreement Evidence vs CROSS_ENGINE_AGREE边界*
*- ⑪Ontology Specificity Policy V1*
*- ⑫Evidence Quality Policy V1*
*- ⑬Single-Parent Domain约束*
*- ⑭Golden Dataset版本化*
*- 新增: 第七条铁律（Validation只读层）*
*- 新增: 契约层级定义 L0-L4
