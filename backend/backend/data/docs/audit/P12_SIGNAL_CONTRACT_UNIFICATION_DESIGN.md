# P1.2 Signal Contract Unification Design

**状态**: DESIGN (pending 裁决)  
**依据**: c6e3755 P1.1 审计裁决  
**目标**: 统一 Signal / CanonicalSignal / Evidence / Temporal / EngineOutput 五者关系，不改生产代码

---

## 1. 问题陈述

P1.1 审计发现以下 Contract 层面不一致：

| # | 问题 | 位置 #1 | 位置 #2 | 风险 |
|---|------|---------|---------|------|
| 1 | CanonicalSignal 双 Schema | `spec/canonical_signal.py` (Phase1, 纯数据) | `signal/canonical_signal.py` (Phase3, 含G3 validator) | drift + 两套字段不兼容 |
| 2 | TemporalConvergence 双定义 | `spec/temporal_evidence.py` | `temporal/schema.py` | 维护双份，漂移不可避免 |
| 3 | Legacy Signal 仍在生产主链 | `reasoning/signal_engine.py` → pipeline.py:86 | `pipeline_stages/compute_stage.py:148` → CrossAnalyzer | 新体系 CanonicalSignal 无法进入生产 |
| 4 | ConvergenceArbiter 与架构原则冲突 | `signal/convergence.py` | 5-way ALIGNED/CONFLICTED/PARTIAL/INSUFFICIENT/UNDEFINED | 违反"互补不比较"原则 |
| 5 | CrossAnalyzer 行为待审计 | `reasoning/cross_analysis.py` | 操作 Legacy Signal，CROSS_STATES 决策树 | 需确认是否含投票冲突逻辑 |

---

## 2. 决策矩阵（P1.1 裁决汇总）

### DEC-001: CanonicalSignal 单一权威源
- **裁决**: 保留 `spec/canonical_signal.py` 为唯一 Schema/Contract
- **action**: `signal/canonical_signal.py` 中的 Phase3 G3 validator 移至 spec 版或废弃
- **不变更**: spec/canonical_signal.py 现有字段结构（CanonicalSignal / SourceEngine / SignalLayer / SignalTemporalScope）

### DEC-002: TemporalConvergence 统一
- **裁决**: 合并至单一位置，删除重复定义
- **候选方案 A**: 保留 `spec/temporal_evidence.py`，删除 `temporal/schema.py` 中 TemporalConvergence 部分
- **候选方案 B**: 保留 `temporal/schema.py`（含 PredictionWindow / EvaluationToleranceWindow），删除 `spec/temporal_evidence.py` 中 TemporalConvergence 部分
- **待裁决**: 需比较两套定义的字段完整性，选优保留

### DEC-003: ConvergenceArbiter 废止
- **裁决**: 倾向废止（违反"互补不比较"）
- **理由**: ConvergenceArbiter 实现 ALIGNED/CONFLICTED/PARTIAL 5-way 裁定，本质是投票/冲突解决机制
- **架构原则**: 子平/盲派/紫微/河洛/易经 是互补证据源，非竞争性投票源
- **action**: 不删除代码（保留为 Research），但不在生产管线中使用

### DEC-004: CrossAnalyzer 审计范围
- **裁决**: P1.2 必审
- **当前行为**: `cross_analysis.py` 操作 Legacy `Signal`（direction/polarity/strength），对 Bazi vs Ziwei 做确定性分析
- **需确认**:
  - [ ] 是否输出"冲突"状态（CONFLICTED）？若是，则违反互补原则
  - [ ] 是否只做互补关系提取（同向/反向/中性）？若是，则符合架构
  - [ ] 产出 CrossResult 的 ontology_relationship 字段是否被消费？
- **action**: 审计后给出明确结论，P1.4 处理迁移

### DEC-005: signal_engine.py 迁移路径
- **裁决**: 不立即删除，REFACTOR/REPLACE
- **当前职责**: 生产管线主链，产出 Legacy Signal
- **目标状态**: 重构为 Canonical Signal Producer，直接产出 CanonicalSignal
- **约束**: 生产管线 pipeline.py 不能断，需渐进迁移

### DEC-006: Blind Bazi / Yi 接入 Contract
- **裁决**: 先定 Contract，禁止 Engine → Guidance 直连
- **Blind Bazi 现状**: `blind_bazi_engine.py` 已 import CanonicalSignal，但未走完整生产 Contract
- **Yi 现状**: `yi/adapter.py` 输出 PipelineResult.yi_structure，未被消费
- **action**: 定义 EngineOutput 契约（产出 CanonicalSignal 而非 raw structure）

---

## 3. 五者关系设计

```
┌─────────────────────────────────────────────────────────────────┐
│                     EngineOutput 契约                            │
│  每个 Engine (Bazi/Ziwei/Huangli/Blind/Yi/Heluo) 必须产出:      │
│    → list[CanonicalSignal] (通过 spec/canonical_signal.py)       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CanonicalSignal (唯一 Schema)                  │
│  spec/canonical_signal.py:                                      │
│    - signal_id (FK)                                             │
│    - source_engine (SourceEngine enum)                          │
│    - layer (SignalLayer: BASELINE/CYCLE/DAILY)                   │
│    - event_type (str)                                           │
│    - domain (Domain enum)                                       │
│    - direction (EventDirection)                                 │
│    - confidence (float 0-1)                                     │
│    - temporal_scope (SignalTemporalScope)                       │
│    - evidence_refs (list[str])                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Evidence (元数据层)                           │
│  - signal_id → evidence_refs 引用                               │
│  - 原典/规则引用（可追溯）                                       │
│  - 存储在 spec/evidence_registry（如有）                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TemporalConvergence (时间聚合)                  │
│  temporal/schema.py (统一后):                                   │
│    - convergence_id                                             │
│    - target_year/month                                          │
│    - signal_ids_by_engine: Dict[engine, list[sid]]              │
│    - overlap_ratio (0-1)                                        │
│    - convergence_score (0-1)                                    │
│  注意: 不做 ALIGNED/CONFLICTED 裁定，只记录多引擎时间重叠         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Signal (Legacy, 逐步废弃)                   │
│  reasoning/signal_engine.py:                                    │
│    - direction/polarity/strength                                │
│    - 仍在生产管线中（DEC-005 约束）                               │
│    - P1.3 开始迁移至 CanonicalSignal                             │
└─────────────────────────────────────────────────────────────────┘
```

**关键设计原则**:
1. **CanonicalSignal 是唯一生产 Contract** — 所有 Engine 必须产出此格式
2. **Evidence 是元数据** — 每个 CanonicalSignal 通过 evidence_refs 追溯原典
3. **TemporalConvergence 是观察性聚合** — 记录多引擎时间重叠，不做冲突裁定
4. **CrossAnalyzer 只做互补关系提取** — 不输出 CONFLICTED 状态
5. **Legacy Signal 是过渡态** — P1.3 开始替换，P1.7 后彻底废弃

---

## 4. 待裁决事项（提交用户）

| ID | 事项 | 推荐方案 | 备选方案 |
|----|------|---------|---------|
| Q-001 | TemporalConvergence 统一位置 | 保留 `temporal/schema.py`（含 PredictionWindow），删除 `spec/temporal_evidence.py` 中的重复定义 | 反之 |
| Q-002 | ConvergenceArbiter 处置 | 标记为 DEPRECATED，生产管线不使用 | 完全删除 |
| Q-003 | CrossAnalyzer 是否保留 | 保留但改写：仅做互补关系提取，移除 CONFLICTED 状态 | 废弃，由新 CrossAnalysis V2 替代 |
| Q-004 | signal_engine.py 重构方式 | 渐进式：先产出双格式（Legacy + Canonical），再逐步切换管线 | 一次性替换 |
| Q-005 | Blind Bazi 接入方式 | 通过 EngineOutput Contract 统一产出 CanonicalSignal | 维持现状（暂不接入主生产链） |

---

## 5. P1.3 迁移预规划（待 P1.2 批准后）

```
P1.3 Production Signal Migration:
  1. signal_engine.py 添加 CanonicalSignal 产出路径（双轨）
  2. pipeline.py 增加 canonical_signals 字段（不破坏现有 Legacy 路径）
  3. compute_stage.py 同时产出 Legacy Signal + CanonicalSignal
  4. 测试: 新旧双轨输出一致性验证
```

---

**文档状态**: DESIGN DRAFT — 等待用户裁决 DEC-001 至 DEC-006 及 Q-001 至 Q-005
