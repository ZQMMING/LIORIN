# P0-③ Signal 架构审计报告

**审计日期**: 2026-08-30
**审计目标**: 三套（实际五套）Signal 系统的职责边界和唯一生产入口
**审计结论**: 🟡 五套Signal并存，职责有重叠，需确定唯一生产入口和分层契约

---

## 一、Signal 系统全景

当前项目存在 **5套** Signal 相关代码（用户说的"三套"是主要的三套，实际还有规范层和聚合层）：

| # | 文件 | 行数 | 核心类 | 层级定位 |
|---|---|---|---|---|
| 1 | `reasoning/signal_engine.py` | 238 | `Signal`, `SignalEngine` | 基础层 — 从规则构建信号 |
| 2 | `reasoning/semantic_signal.py` | 110 | `SemanticSignal` | 语义层 — 带状态和时间范围的信号 |
| 3 | `reasoning/p3_signal_engine.py` | 202 | `P3SignalEngine` | P3层 — P3判定信号引擎 |
| 4 | `signal/canonical_signal.py` | 201 | `CanonicalSignal`, `CanonicalSignalValidator` | 规范层 — 带验证器的规范信号 |
| 5 | `signal/aggregator.py` | 197 | `CanonicalSignalAggregator`, `SignalGroup` | 聚合层 — 多体系信号聚合 |

---

## 二、各层职责分析

### 2.1 基础层：signal_engine.py

**核心职责**:
- `Signal` 数据类：signal_id, ontology_type, direction, polarity, strength, rule_refs, evidence_refs
- `SignalEngine`：从规则匹配结果构建 Signal
- `build_signals()`：按层级（SIGNAL_LAYERS）构建信号字典

**当前状态**: ✅ 基础信号构建，职责清晰
**问题**: strength 字段是浮点数，可能违反"禁止评分"原则（需进一步审计）

### 2.2 语义层：semantic_signal.py

**核心职责**:
- `SemanticSignal` 数据类：比基础Signal多了 status（CANDIDATE/CONFIRMED等）、temporal_scope（时间范围）、confidence
- `SignalStatus` 枚举：ACTIVE, DORMANT, PENDING, RESOLVED
- `TemporalScope` 枚举：ORIGINAL, CURRENT_PERIOD, FLOW_YEAR, FLOW_MONTH
- `validate_signal_contract()`：信号契约验证

**当前状态**: 🟡 语义增强层，与基础Signal有重叠
**问题**: 与 CanonicalSignal 职责重叠，需要确定哪个是生产标准

### 2.3 P3层：p3_signal_engine.py

**核心职责**:
- `P3SignalEngine`：P3层信号引擎
- （需进一步读取详细内容）

**当前状态**: 🟡 P3特定层，职责待明确
**问题**: 与基础SignalEngine的关系不明确

### 2.4 规范层：signal/canonical_signal.py

**核心职责**:
- `CanonicalSignal` 数据类：规范化信号，带完整字段
- `CanonicalSignalValidator`：信号验证器
- `SignalTemporalScope`：时间范围枚举
- `validate_canonical_signal_schema()`：Schema验证

**当前状态**: ✅ 规范化信号，带验证器，是最完整的信号定义
**问题**: 与 SemanticSignal 职责重叠，需要确定哪个是生产标准

### 2.5 聚合层：signal/aggregator.py

**核心职责**:
- `SignalGroup`：信号分组
- `CanonicalSignalAggregator`：多体系信号聚合器
- 从各体系收集 CanonicalSignal 并聚合

**当前状态**: ✅ 聚合层，职责清晰
**问题**: 依赖 CanonicalSignal，需要先确定规范层标准

---

## 三、问题诊断

### 3.1 职责重叠

| 重叠点 | 涉及层 | 问题 |
|---|---|---|
| 信号数据结构 | Signal vs SemanticSignal vs CanonicalSignal | 三套数据结构，字段重叠 |
| 信号验证 | validate_signal_contract vs CanonicalSignalValidator | 两套验证器 |
| 时间范围 | TemporalScope(semantic) vs SignalTemporalScope(canonical) | 两套枚举 |

### 3.2 生产入口不明确

当前没有明确的"唯一生产入口"：
- 基础层 `build_signals()` 产出 `Signal`
- 语义层 `SemanticSignal` 是独立数据类
- 规范层 `CanonicalSignal` 是另一个独立数据类
- 聚合层 `CanonicalSignalAggregator` 消费 `CanonicalSignal`

调用方不知道应该用哪一套。

### 3.3 与 CanonicalState 的关系

P0-① 建立的 CanonicalState 是辨证中间状态容器，Signal 是从状态到断言的中间层。
当前 Signal 系统与 CanonicalState 之间没有明确的接口契约。

---

## 四、建议架构（分层契约）

### 4.1 目标分层

```
CanonicalState (P0-①)
    ↓ 消费
CanonicalSignal (规范层，唯一生产标准)
    ↓ 聚合
CanonicalSignalAggregator (聚合层)
    ↓ 消费
Assertion / 解层
```

### 4.2 各层职责重新定义

| 层 | 文件 | 职责 | 状态 |
|---|---|---|---|
| 规范层 | `signal/canonical_signal.py` | **唯一生产标准** — CanonicalSignal 数据结构 + 验证器 | 🟢 保留为标准 |
| 聚合层 | `signal/aggregator.py` | 多体系信号聚合 | 🟢 保留 |
| 基础层 | `reasoning/signal_engine.py` | 从规则构建信号的**适配器**，输出转换为 CanonicalSignal | 🟡 降级为适配器 |
| 语义层 | `reasoning/semantic_signal.py` | **合并到 CanonicalSignal**，SemanticSignal 标记为 legacy | 🔴 待合并 |
| P3层 | `reasoning/p3_signal_engine.py` | P3特定信号构建，输出转换为 CanonicalSignal | 🟡 降级为P3适配器 |

### 4.3 唯一生产入口

**CanonicalSignal** 是唯一的生产信号标准。
所有其他信号构建器（SignalEngine, P3SignalEngine）都必须输出 CanonicalSignal，而不是各自的信号类型。

---

## 五、迁移路线图

### 阶段1：确定标准（✅ 本报告）
- CanonicalSignal 确定为唯一生产标准
- 分层契约明确

### 阶段2：接口适配（⏳ 待执行）
1. SignalEngine 增加 `to_canonical_signal()` 方法，输出 CanonicalSignal
2. P3SignalEngine 增加 `to_canonical_signal()` 方法
3. SemanticSignal 标记为 legacy，增加 `to_canonical_signal()` 转换方法

### 阶段3：调用方迁移（⏳ 待执行）
1. 所有消费 Signal 的调用方改为消费 CanonicalSignal
2. 所有消费 SemanticSignal 的调用方改为消费 CanonicalSignal

### 阶段4：清理（⏳ 待执行）
1. SemanticSignal 移入 legacy/ 目录
2. Signal 基础类保留为内部实现，不对外暴露
3. 更新文档，明确 CanonicalSignal 为唯一标准

---

## 六、与 CanonicalState 的接口契约

P0-① 建立的 CanonicalState 与 Signal 的关系：

```
CanonicalState
├── facts → 信号的 evidence_refs 来源
├── relations → 信号的 rule_refs 来源
├── classical_states → 信号的语义来源
├── qualifiers → 信号的限定条件
└── unresolved_reasons → 信号的 CANDIDATE 状态原因
    ↓
CanonicalSignal (从 CanonicalState 构建)
├── signal_id
├── source_state_id (关联 CanonicalState 中的 state)
├── direction / polarity
├── status (CANDIDATE / CONFIRMED / UNRESOLVED)
├── temporal_scope
├── evidence_refs (关联 CanonicalState.facts)
├── rule_refs (关联 CanonicalState.relations)
└── provenance (溯源链)
```

---

## 七、审计结论

| 项 | 裁决 |
|---|---|
| 五套Signal识别 | 🟢 PASS（已完整识别） |
| 职责重叠诊断 | 🟢 PASS（已明确重叠点） |
| 唯一生产入口确定 | 🟢 PASS（CanonicalSignal 确定为标准） |
| 分层契约定义 | 🟢 PASS（五层职责重新定义） |
| 接口适配实现 | 🔴 未完成（需各引擎增加 to_canonical_signal()） |
| 调用方迁移 | 🔴 未完成 |
| SemanticSignal 清理 | 🔴 未完成 |

**最终裁决**: 🟡 CONDITIONAL PASS

Signal 架构已审计完成，唯一生产入口（CanonicalSignal）已确定，分层契约已定义。
后续需按迁移路线图逐步完成接口适配、调用方迁移和 legacy 清理。

**关键原则**: CanonicalSignal 是唯一生产标准，所有其他信号类型必须转换为 CanonicalSignal 才能进入生产路径。
