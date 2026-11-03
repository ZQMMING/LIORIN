# P1.2 Signal Contract Unification — Audit Report

> 审计时间：2026-09-01
> 审计方式：三重取证（调用图 + 生产入口链 + 测试对象核对）
> 状态：**已审计，待裁决**

---

## 一、生产路径 Signal 类型真相

### 当前实际运行的类型

```
pipeline.py:154 run()
  → ComputeStage.run() (compute_stage.py:94)
    → SignalEngine.build() (compute_stage.py:138)
      → 产出 dict[str, list[Signal]]
               ↑
         reasoning/signal_engine.py:110
```

**生产 Contract 是 `reasoning/signal_engine.py:110` 的 `Signal`**，不是任何 CanonicalSignal。

### Signal 字段结构（生产路径）

```python
@dataclass(frozen=True)
class Signal:
    signal_id: str
    ontology_type: str
    direction: str            # "STABLE"/"INCREASE"/"DECREASE"/"neutral"
    polarity: str             # 来自规则模板
    strength: str = "moderate" # 硬编码字符串，无数值意义
    layer: str
    rule_refs: list[str]
    evidence_refs: list[str]
```

---

## 二、非生产 Signal 类型（零调用）

| 类型 | 文件:行号 | 生产调用? | 备注 |
|---|---|---|---|
| `CanonicalSignal` (signal层) | `signal/canonical_signal.py:116` | ❌ 否 | 仅 legacy_adapter / blind_bazi_engine 构造 |
| `CanonicalSignal` (spec层) | `spec/canonical_signal.py:62` | ❌ 否 | yi/adapter import 但实际未传 |
| `ConvergenceArbiter` | `signal/convergence.py:80` | ❌ 否 | 仅 docstring 示例引用 |
| `CanonicalSignalAggregator` | `signal/aggregator.py:59` | ❌ 否 | 仅模块 __init__ 导出 |
| `TemporalSignal` | `temporal/schema.py:128` | ❌ 否 | 未接入 pipeline |

---

## 三、违规点确认

### 违规 1：direction 在生产路径中产生并使用

**证据链：**

```
_rule_to_signal() (signal_engine.py:299-313)
  → direction=template["direction"]   # line 306，从规则 JSON 模板读取
  
CrossAnalyzer.analyze() (cross_analysis.py:48-133)
  → sb.direction == sz.direction      # line 83
  → _is_opposite(sb.direction, sz.direction)  # line 92, 114
    → return status="CONFLICTED"     # line 94 ← V13 §四明确禁止
  
compute_stage._build_atomic_claims() (compute_stage.py:275-300)
  → sig.direction                       # line 288, 296，写入 atomic_claims
```

**违反 V13 §四：**
> "EngineEvidence 不能有 polarity/direction — 只保留事实/数值/结构/位置/时间，方向在Assertion之后才产生"

---

### 违规 2：CrossAnalyzer 在生产路径产出 CONFLICTED

**证据：**

```
pipeline_stages/compute_stage.py:148
  cross_result = self.cross_analyzer.analyze(bazi_signals, ziwei_signals)
  
cross_analysis.py:92-100
  if _is_opposite(sb.direction, sz.direction):
      return CrossResult(
          status="CONFLICTED",           # ← 直接违反 V13
          reason_code="OPPOSITE_DIRECTION"
      )
```

**违反 V13 §四："反方向 = 算法/语义问题，不产生 CONFLICTED"**

---

### 违规 3：spec 与 signal 的 CanonicalSignal 字段不一致

| 字段 | `spec/canonical_signal.py` | `signal/canonical_signal.py` |
|---|---|---|
| event 类型 | `event_types: List[str]` | `event_type: str` |
| 置信度 | `confidence: float` | `strength: float` |
| direction | `str`（任意字符串） | `EventDirection` 枚举 |
| domain | 无 | `Domain` 枚举 |

两者同名但结构不同，后续若有人尝试统一将产生隐式转换风险。

---

## 四、strength / confidence 现状

| 字段 | 类型 | 生产路径使用? | 备注 |
|---|---|---|---|
| `Signal.strength` | `str` = "moderate" | ✅ 生产路径有 | 硬编码，从不解析为数值 |
| `CanonicalSignal.strength` | `float` 0.0-1.0 | ❌ 零调用 | 仅 legacy_adapter 构造 |
| `CanonicalSignal.confidence` | `float` 0.0-1.0 | ❌ 零调用 | 仅 convergence.py:189 平均计算 |
| `_STRENGTH_MAP` | dict | ❌ 零引用 | legacy_adapter.py 内部，全仓库无 import |

**结论：strength/confidence 在 production 里无数值意义。**

---

## 五、EngineEvidence 现状

| 项目 | 结果 |
|---|---|
| `src/tongshu/assertion/engine_evidence.py` | **文件不存在** |
| `EngineEvidence` 类定义 | **未找到** |
| `canonical/producer.py` | 使用 `CanonicalState`/`Fact`/`Relation`，不消费 EngineEvidence |
| `temporal_context_contract.py:83` | 仅注释 `# 原始EngineEvidence引用`，无实际 import |

**V13 §三定义的 `EngineEvidence` schema 尚未实现为 Python 类。**

---

## 六、最终对照表

```
组件                              | 生产调用? | direction? | strength/conf? | 状态
─────────────────────────────────|----------|-----------|---------------|------
reasoning/signal_engine.py Signal | ✅ 是     | ✅ 是      | 是(str)        | 🔴 生产违规
reasoning/cross_analysis.py       | ✅ 是     | ✅ 是      | 否            | 🔴 产出 CONFLICTED
signal/canonical_signal.py        | ❌ 否     | —         | —             | 🟡 未接入
spec/canonical_signal.py          | ❌ 否     | —         | —             | 🟡 字段不一致
signal/convergence.py             | ❌ 否     | —         | —             | 🟢 零调用
signal/aggregator.py              | ❌ 否     | —         | —             | 🟢 零调用
signal/legacy_adapter.py          | ❌ 否     | —         | —             | 🟢 已标记 NON_PRODUCTION
temporal/schema.py TemporalSignal | ❌ 否     | —         | —             | 🟢 未接入
assertion/engine_evidence.py      | N/A     | N/A      | N/A           | 🔴 文件不存在
```

---

## 七、待裁决事项

### R1：生产 Signal 的最终形态

当前生产 Contract 是 `reasoning/signal_engine.py:110` 的 `Signal`，携带 `direction`。

选项：
- **A**：将 `reasoning/signal_engine.py` 的 `Signal` 重构为 V13 定义的 `EngineEvidence`（无 direction），在 Assertion 层才引入 direction
- **B**：将 `signal/canonical_signal.py` 的 `CanonicalSignal` 真正接入 pipeline，替换现有 `Signal`

### R2：CrossAnalyzer 的 CONFLICTED 处理

`cross_analysis.py:92-100` 在生产路径中产出 `CONFLICTED`，违反 V13。

选项：
- **A**：移除 `_is_opposite()` 判定，改为互补语义（同主题不同方向 = PARTIAL，不判定 CONFLICTED）
- **B**：完全移除 CrossAnalyzer，改为简单的信号聚合（evidence_count）

### R3：spec/canonical_signal.py vs signal/canonical_signal.py

两者字段不一致，需决定以哪个为权威版本，另一个删除或合并。

---

## 八、下一步建议顺序

```
P1.2 Signal Contract Audit      ✅ 完成
    ↓
P1.4 Cross-System Semantics     ← 最小阻断点：移除 CONFLICTED
    ↓
P1.2 Signal Migration           ← 将 Production Signal 迁移到 EngineEvidence
    ↓
P1.6 Contract Consolidation     ← 统一 spec/signal 双 CanonicalSignal
    ↓
P1.7 Runtime Convergence Audit  ← 最终验证
```

---

*本报告为独立审计结果，不构成代码变更。需 User 裁决后启动实施。*
