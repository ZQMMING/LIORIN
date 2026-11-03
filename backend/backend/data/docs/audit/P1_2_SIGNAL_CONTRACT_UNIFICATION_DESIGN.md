# P1.2 Signal Contract Unification — Design Document

**Author**: Codex  
**Date**: 2026-08-31  
**Status**: DRAFT — Awaiting user裁决  
**Parent**: P1.1 Audit c6e3755 → P1.2 Signal Contract Unification  

---

## 1. Purpose

P1.2 是 P1 信号迁移路线的第二个阶段，目标是**定义** Signal / CanonicalSignal / Evidence / Temporal / EngineOutput 五者的最终关系，**不改动生产代码**。产出物为设计文档，待用户裁决后进入 P1.3 实施阶段。

---

## 2. Current State Summary

### 2.1 Dual CanonicalSignal Schema

| 位置 | Phase | 性质 | 字段差异 |
|------|-------|------|---------|
| `spec/canonical_signal.py` | Schema 4, Phase 1 | 纯数据 schema，无 validation | `ontology_type` + `direction` + `confidence`；`event_types`(列表) |
| `signal/canonical_signal.py` | Phase 3 | 含 G3 验证器 | `event_type`(单值)；`domain` + `strength`；extends spec 版 |

**问题**：两处 dataclass 字段不一致（`ontology_type` vs `domain+strength`、`event_types` vs `event_type`），Phase 3 版 extends Phase 1 版但引入了额外约束，造成契约漂移风险。

### 2.2 Dual TemporalConvergence Definition

| 位置 | 内容 |
|------|------|
| `spec/temporal_evidence.py` | 定义 `TemporalSignal` + `TemporalConvergence` |
| `temporal/schema.py` | 定义 `TemporalConvergence` + `PredictionWindow` + `EvaluationToleranceWindow` |

**问题**：两份定义并存，字段漂移，维护时易不同步。

### 2.3 Legacy Signal 仍在生产主链

```
pipeline.py:87  →  SignalEngine  →  legacy Signal (direction/polarity/strength)
                                   →  CrossAnalyzer.analyze(bazi_signals, ziwei_signals)
                                   →  CanonicalComposer (still imports legacy Signal)
                                   →  ComputeResult.signals (dict[str, list[Signal]])
```

唯一直接输出 `CanonicalSignal` 的引擎：`blind_bazi_engine.py`，但其产出未经完整 Contract 链路处理。

### 2.4 CrossAnalyzer 设计审查

**现状**：`CrossAnalyzer.analyze()` 接收 `list[Signal]` (legacy)，输出 `CrossResult`（CROSS_STATES：ALIGNED / CONFLICTED / PARTIAL / INSUFFICIENT）。

**审查结论**：
- 子平/盲派/紫微/河洛/易经是**互补系统**（架构原则"互补不比较"），非同一事件的多源投票
- `CONFLICTED` 状态语义上隐含"冲突裁决"，与互补原则冲突
- `CROSS_STATES` 决策树需审计：是否存在"多数引擎压倒少数引擎"的投票逻辑
- **P1.2 行动**：定义 CrossAnalyzer 的新职责——互补关系提取（如 Bazi 说"水旺"、Ziwei 说"火弱"→ 关系为"水克火"而非"谁赢"）

### 2.5 ConvergenceArbiter 设计审查

**现状**：`signal/convergence.py` 实现 5-way 裁定：ALIGNED / CONFLICTED / PARTIAL / INSUFFICIENT / UNDEFINED。

**审查结论**：
- Arbiter 语义是"仲裁冲突"，本质是投票/裁决机制
- 与架构原则"互补不比较"直接冲突
- **P1.2 建议**：**废止** ConvergenceArbiter，将多引擎信号聚合改为关系提取（Relation Extraction），非裁决

### 2.6 Yi Engine 输出边界

**现状**：`yi/adapter.py` 输出 `PipelineResult.yi_structure`，但：
- 未消费（无下游 processor）
- 结构未定义（"结构事实 / Signal / Assertion / Interpretation 四选一"）

**P1.2 建议**：定义 Yi 输出作为 **Evidence**（结构事实层），非 Signal 直出；消费路径须经 CrossAnalyzer 关系提取后再进入 Composer。

### 2.7 Blind Bazi 接入

**现状**：`blind_bazi_engine.py` 直接 import `CanonicalSignal` 并产出，但：
- 未经 `CanonicalSignalValidator` 校验
- 未经 Aggregator 收集
- 未经 TemporalConvergence 评估

**P1.2 建议**：定义 Blind Bazi → CanonicalSignal Producer 的完整 Contract，包含：
- 产出 Schema（引用 `spec/canonical_signal.py`）
- 校验路径（G3 validation）
- 聚合路径（CanonicalSignalAggregator）
- Temporal 路径（TemporalConvergence）

---

## 3. Design Decisions

### 3.1 CanonicalSignal 单一权威源

**决策**：以 `spec/canonical_signal.py` 为**唯一权威 Schema/Contract**。

理由：
- `spec/` 目录语义为"规格定义"，`signal/` 目录语义为"运行时实现"
- Phase 1 Schema 先于 Phase 3 扩展，符合演进顺序
- `signal/canonical_signal.py` 中的 Phase 3 扩展（G3 validator、`event_type` 单值）为**运行时实现细节**，不应覆盖 spec 版 Contract

**执行路径（P1.3 实施）**：
1. 将 `signal/canonical_signal.py` 中 G3 验证逻辑合并到 `spec/canonical_signal.py`（作为 `validate_canonical_signal(signal)` 函数）
2. 删除 `signal/canonical_signal.py` 中的 dataclass 定义，改为 `from ..spec.canonical_signal import CanonicalSignal` 别名导入
3. 统一 `event_types` (列表) 为唯一字段，废弃 `event_type` (单值)
4. 统一 `ontology_type + direction + confidence` 为唯一组合，废弃 `domain + strength`

### 3.2 TemporalConvergence 单一权威源

**决策**：以 `temporal/schema.py` 为**唯一权威源**，合并 `spec/temporal_evidence.py` 的 `TemporalSignal` 定义。

理由：
- `temporal/schema.py` 包含完整的 `PredictionWindow` / `EvaluationToleranceWindow` 相关类型，功能更完整
- `spec/temporal_evidence.py` 的 TemporalConvergence 为 Phase 1 简版，字段缺失

**执行路径（P1.3 实施）**：
1. 将 `spec/temporal_evidence.py` 中的 `TemporalSignal` dataclass 迁移到 `temporal/schema.py`
2. 删除 `spec/temporal_evidence.py` 中的 `TemporalConvergence` 定义
3. 更新所有 import 指向 `temporal.schema.TemporalConvergence`

### 3.3 ConvergenceArbiter 废止

**决策**：**废止** `signal/convergence.py` 中的 `ConvergenceArbiter`。

理由：
- Arbiter 语义是"裁决冲突"，与"互补不比较"原则直接冲突
- 5-way 裁定（ALIGNED / CONFLICTED / PARTIAL / INSUFFICIENT / UNDEFINED）隐含投票逻辑
- 多引擎信号应通过**关系提取**（Relation Extraction）而非**冲突裁决**（Conflict Resolution）处理

**替代方案**：
- CrossAnalyzer 扩展为多引擎关系提取器（Bazi 说 X、Ziwei 说 Y → 输出"X 与 Y 的关系是 Z"）
- 关系提取结果作为 Evidence 进入 CanonicalComposer.signals 字段
- 不再产出"ALIGNED/CONFLICTED"等裁定状态，改为"RELATION: 水克火 · 证据：Bazi(水旺) + Ziwei(火弱)"

### 3.4 CrossAnalyzer 审计范围

**P1.2 审计清单**：
1. 检查 `cross_analysis.py` 中 `CROSS_STATES` 决策树：是否存在"多数压倒少数"的投票逻辑
2. 检查 `analyze()` 方法签名：是否硬编码 Bazi + Ziwei 二元关系（应扩展为 N 元互补关系）
3. 检查 `forbidden_inferences` 过滤：是否包含"跨系统直接比较"类规则
4. 输出：审计报告 `docs/audit/P1_2_CROSS_ANALYZER_AUDIT.md`

### 3.5 signal_engine.py 重构路径

**决策**：**不立即删除**，制定迁移计划：

| 阶段 | 动作 | 文件 |
|------|------|------|
| P1.2 | 定义 Legacy Signal → CanonicalSignal 映射表 | `docs/design/signal_migration_mapping.md` |
| P1.3 | 新增 `CanonicalSignalProducer` 包装类（保留 Legacy API） | `reasoning/canonical_producer.py` |
| P1.4 | Pipeline 切换至 CanonicalSignalProducer | `pipeline.py` |
| P1.5 | 废弃 `signal_engine.py` 中 legacy 部分 | `reasoning/signal_engine.py`（标记 deprecated） |
| P1.6 | 完全移除 `signal_engine.py` | 删除文件 |

### 3.6 Yi Engine 输出边界定义

**决策**：Yi Engine 输出定义为 **Evidence（结构事实层）**，消费路径：

```
Yi Engine → yi.adapter.YiStructure
           → YiEvidenceConverter (新)
           → list[Evidence] (structured facts)
           → CrossAnalyzer (relation extraction, multi-engine)
           → CanonicalComposer.signals
```

**Yi 输出不可直出 Signal**：Yi 的输出为"卦辞/爻辞/象义"，属解释层，需经 Evidenece 转换后方可进入信号链路。

### 3.7 五者最终关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Engine Layer                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Bazi     │ │ BlindBazi│ │ Ziwei    │ │ Heluo    │  Yi      │
│  │ Engine   │ │ Engine   │ │ Engine   │ │ Engine   │ Adapter  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘    │       │
│       │            │            │            │          │       │
│       ▼            ▼            ▼            ▼          ▼       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 CanonicalSignal (spec/)                   │  │
│  │         ← 五引擎统一产出 Schema (唯一权威) →               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              CrossAnalyzer (Extension)                    │  │
│  │         ← 互补关系提取 (非冲突裁决) →                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            CanonicalSignalAggregator                      │  │
│  │         ← 收集 + 校验 + 分组 (无 score/weight) →           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            TemporalConvergence (temporal/schema.py)       │  │
│  │         ← 多引擎时序收敛评估 (唯一权威) →                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │             CanonicalContent (SIR)                        │  │
│  │         ← Canon
