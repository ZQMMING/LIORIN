# P0-LEGACY-PATH-AUDIT v2 — 完整生产路径追踪 + signal_engine 遗留分析

**Audit Date**: 2026-09-01
**Baseline**: origin/main HEAD `b93b8e7` (P1.2 Signal Contract Unification Design)
**Reference**: commit `9a1479d` (P0-8.6, 2026-08-31)

---

## 执行摘要

| 组件 | 文件 | 生产调用 | 状态 | 优先级 |
|------|------|----------|------|--------|
| `strength_engine.py` | ❌ 已删除 | N/A | 🟢 已清理 | — |
| `wang_score >= 2.0` 判定 | N/A | 0 | 🟢 已清理 | — |
| `SemanticSignal` 类 | ❌ 已删除 | 0 | 🟢 已清理 | — |
| `SignalEngine` | ✅ EXISTS | pipeline.py:86 | **ACTIVE_PRODUCTION** | 🔴 P0 |
| `Signal.direction` | ✅ EXISTS | composer.py:149 | **ACTIVE_PRODUCTION** | 🔴 P0 |
| `Signal.polarity` | ✅ EXISTS | cross_analysis.py:83 | **ACTIVE_PRODUCTION** | 🔴 P0 |
| `_derive_direction_polarity()` | ✅ EXISTS | signal_engine.py:300 | **ACTIVE_PRODUCTION** | 🔴 P0 |
| `CanonicalStateProducer` | ✅ EXISTS | 0 调用方 | **ISOLATED** | 🟡 P2 |
| `legacy_adapter.py` | ✅ EXISTS | 0 调用方 | **TEST_ONLY** | 🟡 P2 |
| `judgment_production.py` | ❌ 不存在 | 0 | **DELETED** | — |
| `RuleMatcher` + `RuleLoader` | ✅ EXISTS | pipeline.py:85,131 | **ACTIVE_PRODUCTION** | ✅ 新架构基础设施 |
| `atomic_claims` 结构 | ✅ 生产 | app.py:308 | **ACTIVE_PRODUCTION** | ⚠️ 见下文 |

---

## 一、`strength_engine.py` 的事实核查

### 用户观察 vs 当前状态

| 项目 | 用户观察 | 当前 main (`b93b8e7`) |
|------|----------|----------------------|
| 文件存在 | "仍在" | ❌ 已删除 (commit `966db50`) |
| 评分阈值 | "wang_score >= 2.0 仍存在" | ❌ 已移除 (commit `fad200e`) |
| D1 标签 | "D1 旺衰 Deterministic Engine" | N/A（文件已删） |

**结论**：用户观察基于旧快照（可能是本地未同步分支或浏览器缓存）。当前 main 上：
- `strength_engine.py` 已在 P0 purge 中删除
- `canonical/state.py:437` 保留了防御性 guard（`forbidden_keys` 检查），防止未来回归
- `CanonicalStateProducer`（`producer.py`）是新的特征计算替代方案，但零生产调用

---

## 二、`signal_engine.py` — 🔴 唯一 ACTIVE_PRODUCTION 遗留问题

### 2.1 生产路径完整追踪

```
TONGSHUPipeline.run()
  → ComputeStage.__init__(signal_engine=SignalEngine(rule_matcher))   [pipeline.py:86]
  → ComputeStage.run()
    → signal_engine.build(bazi, ziwei, huangli, gender, ...)          [compute_stage.py:138]
      → build_signals() → _build_layer_signals()                     [signal_engine.py:333]
        → matcher.match_all(ctx, layer)                                [signal_engine.py:317]
        → resolve_conflicts(matched)
        → for each rule:
            _rule_to_signal(rule, layer, i)                            [signal_engine.py:299]
              ↓
            _derive_direction_polarity(rule)                           [signal_engine.py:274]
              ├── produces_layer_output_template → template["direction/polarity"]
              └── produces_semantic_atoms → _ATOM_DIRECTION_MAP / _ATOM_POLARITY_MAP
              ↓
            Signal(direction=..., polarity=..., ...)                   [signal_engine.py:303-308]
    → cross_analyzer.analyze(bazi_signals, ziwei_signals)              [compute_stage.py:147]
      → sb.direction == sz.direction                                   [cross_analysis.py:83]
      → _is_opposite(sb.direction, sz.direction)                       [cross_analysis.py:92,114]
    → _build_atomic_claims(theme, signals)                             [compute_stage.py:156]
      → sig.direction, sig.polarity                                    [compute_stage.py:288-290]
      → theme_engine.reframe_claim(ontology_type, theme, direction, polarity)
      → {"claim": ..., "direction": sig.direction, ...}                [compute_stage.py:296]
    → CanonicalComposer.compose(signals=signals, atomic_claims=...)    [compute_stage.py:178]
      → _format_signals(signals)                                       [composer.py:138]
        → "direction": s.direction, "polarity": s.polarity             [composer.py:149-150]
    → RenderStage → API Response
      → "atomic_claims": canon.atomic_claims                           [app.py:308]
```

### 2.2 `direction`/`polarity` 的值域问题

**`Signal` dataclass**（生产对象）：
```python
# signal_engine.py:102-107
@dataclass(frozen=True)
class Signal:
    direction: str    # 实际值: "STABLE" | "INCREASE" | "DECREASE"
    polarity: str     # 实际值: "active" | "neutral" | "restricted"
```

**`CanonicalSignal` spec**（理论标准）：
```python
# spec/canonical_signal.py:73
direction: str    # 注释写: POSITIVE|NEGATIVE|CHANGE|NEUTRAL|UNKNOWN
```

**`EventDirection` enum**（event_ontology_v1）：
```python
# spec/event_ontology_v1.py:31-37
class EventDirection(enum.Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    CHANGE = "CHANGE"
    NEUTRAL = "NEUTRAL"
    # 缺少 UNKNOWN（但 spec 注释里写了）
```

**`_DIRECTION_MAP`（legacy_adapter.py）**：
```python
_DIRECTION_MAP = {
    "positive": EventDirection.POSITIVE,
    "beneficial": EventDirection.POSITIVE,
    "negative": EventDirection.NEGATIVE,
    ...
}
# ⚠️ 关键：没有 "STABLE"/"INCREASE"/"DECREASE" 的映射！
# legacy_adapter 无法正确转换生产 Signal 的 direction 值
```

**结论**：`legacy_adapter.py` 的映射表与生产 `Signal.direction` 的值域完全不对齐。即使接入，转换也会全部 fallback 到 `UNKNOWN`。

### 2.3 当前生产输出样本

`atomic_claims` 中的方向字段：
```python
# compute_stage.py:296
"direction": sig.direction,  # "STABLE" | "INCREASE" | "DECREASE"
# 而非 spec 期望的:
# "POSITIVE" | "NEGATIVE" | "CHANGE" | "NEUTRAL"
```

---

## 三、新架构组件状态

### 3.1 `CanonicalStateProducer` — ISOLATED

```python
# canonical/producer.py:35
class CanonicalStateProducer:
    """从 BaziChart 生产 CanonicalState。
    【迁移方向】health_signals / annual_event_evaluator 等消费 CanonicalState
    """
```

**生产调用方**：0（全仓库无 import）
**用途**：仅测试/研究，未接入 `ComputeStage` 或 `TONGSHUPipeline`

### 3.2 `legacy_adapter.py` — TEST_ONLY

```python
# signal/legacy_adapter.py:1
"""P0-③ Legacy Signal Adapter — 基础层 Signal 到 CanonicalSignal 的适配器"""
```

**生产调用方**：0（全仓库无 import，包括 compute_stage/composer/pipeline）
**功能**：`legacy_signal_to_canonical(signal)` → `CanonicalSignal`
**缺陷**：`_DIRECTION_MAP` 不包含 `"STABLE"/"INCREASE"/"DECREASE"` 映射

### 3.3 `judgment_production.py` — DELETED

该文件在当前 main 上不存在。P0-6.x/P0-8.x 提交提到的 `Evidence→Primitive→Judgment→Assertion` 路径在代码层面已无对应实现。

---

## 四、README 与实际代码的架构偏差

### README 描述（`README.md:8-10`）
```
算 (Calculation) → 辨 (State/Signal) → 解 (Assertion/Interpretation)
     ↓                  ↓                      ↓
Canonical State    Semantic Signals      Assertion Assets
```

### 实际生产路径
```
算 → BaziEngine/ZiweiEngine/HuangliEngine
辨 → SignalEngine (RuleMatcher + _derive_direction_polarity)
解 → atomic_claims (无结构化 Judgment/Assertion 类型)
```

### 偏差点

| README 描述 | 实际代码 |
|------------|----------|
| `Canonical State` | `CanonicalStateProducer` 零生产调用 |
| `Semantic Signals` | `SemanticSignal` 类已删除；现为 `Signal(direction/polarity)` |
| `Assertion Assets` | `atomic_claims` 是 raw dict list，无 Assertion 类型定义 |

---

## 五、`signal_engine.py` 遗留路径修复方案

### 问题根因

`_derive_direction_polarity()` 将 `produces_semantic_atoms`（事实）直接压缩为 `direction`/`polarity`（价值判断），发生在规则匹配阶段（即"辨"之前）。这违反了：

> **原典授权 ≠ 条件成立 ≠ 断事结论授权**

原则。`direction`/`polarity` 是跨信号比较所需的语义标签，但不应在 Signal 提取阶段就硬编码。

### 修复方案（两步）

#### Step 1：剥离 `direction`/`polarity` 从 `Signal` 数据类

```python
# signal_engine.py:101-107 修改为：
@dataclass(frozen=True)
class Signal:
    signal_id: str
    ontology_type: str
    # direction: str       ← 移除（改为在 CanonicalSignal 层推导）
    # polarity: str        ← 移除
    strength: str
    layer: str
    rule_refs: list
    evidence_refs: list
    # 新增：保留原始语义原子用于下游推导
    semantic_atoms: list[str] = field(default_factory=list)
```

#### Step 2：在 `CanonicalComposer` 层推导方向

```python
# canonical/composer.py _format_signals() 修改为：
def _format_signals(self, signals: dict[str, list[Signal]]) -> dict:
    from ..spec.event_ontology_v1 import EVENT_TYPE_BY_ID, EventDirection
    
    out: dict[str, list[dict]] = {}
    for layer in SIGNAL_LAYERS:
        out[layer] = []
        for s in signals.get(layer, []):
            # 从 ontology_type 查 EventDirection（事实→方向映射在 spec 层，不在 engine 层）
            event_def = EVENT_TYPE_BY_ID.get(s.ontology_type)
            direction = event_def.direction.value if event_def else EventDirection.NEUTRAL.value
            
            out[layer].append({
                "signal_id": s.signal_id,
                "ontology_type": s.ontology_type,
                "direction": direction,   # 从 spec 推导，不从 engine 硬编码
                "strength": s.strength,
                "rule_refs": list(s.rule_refs),
                "evidence_refs": list(s.evidence_refs),
            })
    return out
```

#### Step 3：CrossAnalysis 改用 `EventDirection`

```python
# cross_analysis.py 修改：
from ..spec.event_ontology_v1 import EventDirection, _is_opposite_direction

# 比较逻辑保持不变，但使用 EventDirection 枚举
if sb.direction == sz.direction:  # 改为 EventDirection 比较
    ...
```

### 修复后的架构

```
Rule → Signal(ontology_type, strength, evidence_refs)     ← 无 direction/polarity
  ↓
CanonicalComposer                                          ← 方向从 spec 推导
  ↓
CanonicalSignal(direction=EventDirection)                  ← 规范层
  ↓
CrossAnalysis(EventDirection)                              ← 跨引擎比较
  ↓
atomic_claims                                              ← 最终输出
```

---

## 六、验证矩阵

### 修复前（当前状态）

| 检查项 | 结果 |
|--------|------|
| `strength_engine.py` 生产调用 | ❌ 已删除 |
| `wang_score >= 2.0` 生产判定 | ❌ 已删除 |
| `Signal.direction` 生产流 | 🔴 活跃（`STABLE/INCREASE/DECREASE`） |
| `Signal.polarity` 生产流 | 🔴 活跃（`active/neutral/restricted`） |
| `legacy_adapter` 生产调用 | ❌ 0 |
| `CanonicalStateProducer` 生产调用 | ❌ 0 |
| README 与代码一致性 | ❌ 偏差 |

### 修复后（预期）

| 检查项 | 预期结果 |
|--------|----------|
| `Signal.direction` | 🟢 移除或改为 Optional，不进入生产 |
| `Signal.polarity` | 🟢 移除或改为 Optional |
| `_derive_direction_polarity()` | 🟢 标记 LEGACY_COMPAT，不再调用 |
| `CrossAnalysis` | 🟢 改用 `EventDirection` 枚举比较 |
| `CanonicalComposer._format_signals()` | 🟢 从 spec 推导方向 |
| README | 🟢 与实际路径对齐 |

---

## 七、后续行动

### P0 阻塞项

1. **移除 `Signal.direction` / `Signal.polarity`**（或改为 optional）
   - 影响文件：`signal_engine.py`, `composer.py`, `compute_stage.py`, `cross_analysis.py`
   - 破坏性变更：需同步更新测试

2. **删除 `_derive_direction_polarity()` 或标注 LEGACY_COMPAT**
   - 文件：`signal_engine.py:274-294`
   - 策略：保留函数但不从 `build_signals()` 调用

3. **对齐 README 与实际路径**
   - 文件：`README.md`
   - 更新架构描述为实际运行的路径

### P2 技术债

4. **接入 `legacy_adapter.py`** 或删除（如果不再需要转换）
5. **补充 `EventDirection.UNKNOWN` 到 spec**（当前 spec 注释有但 enum 无）
6. **补充 `_DIRECTION_MAP` 覆盖 `STABLE/INCREASE/DECREASE`**（如需保留 adapter）

### 暂缓

- `CanonicalStateProducer` 接入主链路（需重新设计 ComputeStage）
- `judgment_production.py` 重建（文件已删除，需评估是否需要）
