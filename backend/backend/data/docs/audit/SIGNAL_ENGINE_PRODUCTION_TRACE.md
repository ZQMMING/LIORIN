# S1-S5: Signal Engine Production Path Trace

**Date**: 2026-09-01
**Scope**: `src/tongshu/reasoning/signal_engine.py` — 仅追踪生产调用链，不修改代码

---

## S1: SignalEngine.build() 的所有 production callers

### 直接调用方

| 文件 | 行号 | 代码 | 类型 |
|------|------|------|------|
| `pipeline.py` | 86 | `self.signal_engine = SignalEngine(self.rule_matcher)` | 构造注入 |
| `pipeline.py` | 102 | `signal_engine=self.signal_engine` → ComputeStage | 传递 |
| **`compute_stage.py`** | **138** | **`signals = self.signal_engine.build(bazi_chart, ziwei_chart, huangli_day, gender=gender, heluo_result=heluo_result)`** | **直接调用** |

### 间接引用方（仅 import Signal 类型，不调用 build）

| 文件 | 行号 | 用途 |
|------|------|------|
| `canonical/composer.py` | 18 | `from ..reasoning.signal_engine import Signal` — 类型注解 |
| `cross_analysis.py` | 12 | `from .signal_engine import Signal` — 类型注解 |
| `ziwei_engine.py` | 164 | `from ..reasoning.signal_engine import Signal` — 同结构工厂 |
| `types.py` | 54 | `from .reasoning.signal_engine import Signal` — 类型别名 |
| `reasoning/__init__.py` | 2,10 | 公开 API 导出 |
| `signal/legacy_adapter.py` | 169 | 引用做转换（无生产调用） |

### 结论

> **唯一生产调用**：`compute_stage.py:138`
> 其余均为类型注解或工具层引用。

---

## S2: Signal 最终交给谁

`compute_stage.py:138` 之后 Signal 进入三条路径：

```
signals = self.signal_engine.build(...)   # dict[str, list[Signal]]
  │
  ├─→ [1] Cross Analysis                 # compute_stage.py:143-147
  │     bazi_signals = signals["BASELINE"] + signals["CYCLE_CONTEXT"] + signals["DAILY_ACTIVATION"]
  │     ziwei_signals = [zw_signal]
  │     cross_result = self.cross_analyzer.analyze(bazi_signals, ziwei_signals)
  │
  ├─→ [2] Atomic Claims                  # compute_stage.py:156
  │     atomic_claims = self._build_atomic_claims(theme, signals)
  │
  └─→ [3] Canonical Composer             # compute_stage.py:178-182
        canonical = self.composer.compose(
            signals=signals,              # ← 原始 Signal dict 传入
            cross_result=cross_result,
            atomic_claims=atomic_claims,
            ...
        )
```

**`CanonicalStateProducer` 不在此链中**：零生产调用，属于独立研究工具。

---

## S3: Signal 字段下游消费明细

### `direction` 消费链

| 位置 | 代码 | 作用 |
|------|------|------|
| `cross_analysis.py:83` | `if sb.direction == sz.direction:` | 同向判定（ALIGNED） |
| `cross_analysis.py:92` | `if _is_opposite(sb.direction, sz.direction):` | 反向判定（CONFLICTED） |
| `cross_analysis.py:114` | `if _is_opposite(sb.direction, sz.direction):` | PARTIAL 排除 |
| `compute_stage.py:288` | `direction=sig.direction` → `theme_engine.reframe_claim()` | 主题重构 |
| `compute_stage.py:296` | `"direction": sig.direction` → atomic_claims | 写入输出 |
| `composer.py:149` | `"direction": s.direction` → SIR dict | 序列化进 SIR |
| `app.py:308` | `"atomic_claims": canon.atomic_claims` | API 响应 |

### `polarity` 消费链

| 位置 | 代码 | 作用 |
|------|------|------|
| `compute_stage.py:289` | `polarity=sig.polarity` → `theme_engine.reframe_claim()` | 主题重构 |
| `compute_stage.py:290` | `f"...信号{sig.polarity}。"` | fallback 文本 |
| `composer.py:150` | `"polarity": s.polarity` → SIR dict | 序列化进 SIR |

### `strength` 消费链

| 位置 | 代码 | 作用 |
|------|------|------|
| `composer.py:151` | `"strength": s.strength` → SIR dict | **仅序列化，不参与任何逻辑判断** |

### `theme_engine.reframe_claim()` 的中文映射

```python
# theme_engine.py:50-60
dir_word = {"INCREASE": "增强", "STABLE": "平稳", "DECREASE": "减弱"}.get(direction, "平稳")
pol_word = {"active": "活化", "neutral": "中性", "restricted": "受限"}.get(polarity, "中性")
```

**关键发现**：`direction`/`polarity` 的中文翻译是**硬编码在 theme_engine 里**的，与 `signal_engine._ATOM_DIRECTION_MAP` 的值域完全一致（STABLE/INCREASE/DECREASE × active/neutral/restricted）。两条映射链互相验证。

---

## S4: produces_semantic_atoms → direction/polarity 有多少进入最终输出

### 数据流追踪

```python
# signal_engine.py:288-294
atoms = conclusion.get("produces_semantic_atoms")
if atoms is not None and len(atoms) > 0:
    first_atom = atoms[0]                    # ← 只取第一个 atom
    direction = _ATOM_DIRECTION_MAP.get(first_atom, "STABLE")
    polarity  = _ATOM_POLARITY_MAP.get(first_atom, "neutral")
```

**只取第一个 atom**，且硬编码默认值 `"STABLE"/"neutral"`。

### 进入最终输出的比例

无法从静态分析给出精确数字（取决于 `data/rules/*.json` 中规则的实际分布）。但路径确认：
- 所有通过 `_rule_to_signal()` 产出的 Signal 都会携带 `direction`/`polarity`
- 这些 Signal 全部进入 `_build_atomic_claims()` → `atomic_claims` → SIR → API 响应

**结论**：所有 `produces_semantic_atoms` 规则产出的 Signal，其方向都来自 `first_atom` 的硬编码映射。这是用户指出的"危险的压缩"。

---

## S5: 删除 `_derive_direction_polarity()` 会断掉什么

### 直接断裂点（3处）

| 位置 | 代码 | 后果 |
|------|------|------|
| `signal_engine.py:300` | `direction, polarity = _derive_direction_polarity(rule)` | Signal 无法构造（方向/polarity 为 None） |
| `cross_analysis.py:83,92,114` | `sb.direction == sz.direction` | Cross Analysis 比较逻辑失效 |
| `compute_stage.py:288-290` | `direction=sig.direction, polarity=sig.polarity` | theme_engine.reframe_claim 收到 None |

### 间接影响（如果保留 Signal 字段但设为 None/default）

| 组件 | 当前行为 | 断链后行为 |
|------|----------|------------|
| Cross Analysis | direction 比较决定 ALIGNED/CONFLICTED/PARTIAL | 需改用其他字段或默认返回 EVIDENCE_MISSING |
| theme_engine.reframe_claim | direction→中文词映射 | 收到 None → fallback 到 `"平稳"/"中性"` |
| atomic_claims | 携带 direction | 需改为从 spec 推导或省略 |
| composer._format_signals | 序列化 direction/polarity | 需改为从 spec/ontology 推导 |

### 真正的替代路径

```
当前（旧）:  produces_semantic_atoms → first_atom → ATOM_MAP → direction/polarity → Signal
替代（新）:  ontology_type → EVENT_TYPE_BY_ID → EventDirection → CanonicalSignal.direction
```

`EventDirection` 在 `spec/event_ontology_v1.py` 中已定义（POSITIVE/NEGATIVE/CHANGE/NEUTRAL），每个 EventDefinition 都有预定义的 direction。

---

## 完整生产路径图

```
┌─────────────────────────────────────────────────────────────┐
│ BaziEngine / ZiweiEngine / HuangliEngine                   │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
          build_rule_context()      [signal_engine.py:128]
                        ↓
              RuleMatcher           [matcher.py:298]
              match_all(ctx, layer)
                        ↓
             resolve_conflicts()    [matcher.py]
                        ↓
              resolved rules        │
                        │           │
            ┌───────────┴───────────┘
            ↓                           ↓
  produces_layer_output_template    produces_semantic_atoms
  → template["direction/polarity"]  → first_atom
                                    → ATOM_DIRECTION_MAP
                                    → ATOM_POLARITY_MAP
            └───────────┬───────────┘
                        ↓
              _rule_to_signal()     [signal_engine.py:299]
              Signal(
                direction="STABLE"/"INCREASE"/"DECREASE"
                polarity="active"/"neutral"/"restricted"
                strength="moderate"
              )
                        ↓
              build_signals()       [signal_engine.py:333]
              → dict[BASELINE, CYCLE_CONTEXT, DAILY_ACTIVATION]
                        ↓
            ═══════════════════════════════════════
            │  ComputeStage.run()  [compute_stage.py:138]          │
            ═══════════════════════════════════════
                        │
         ┌──────────────┼──────────────┐
         ↓              ↓              ↓
    [1] Cross      [2] Atomic     [3] Canonical
        Analysis       Claims        Composer
         ↓              ↓              ↓
    cross_result    atomic_claims   CanonicalContent
    (ALIGNED/      (list[dict])     (SIR 结构)
     CONFLICTED/
     PARTIAL)
         └──────────────┬──────────────┘
                        ↓
              RenderStage → API Response
              app.py:308  "atomic_claims": ...
              app.py:270  "cross_status": ...
```

---

## 结论

1. **`SignalEngine.build()` 有明确的单一生产入口**（`compute_stage.py:138`），不是死代码。

2. **`direction`/`polarity` 是实际被消费的生产字段**，影响 Cross Analysis 判断和 atomic_claims 文本生成。

3. **`_derive_direction_polarity()` 是旧架构的核心操作**：将 Semantic Atom（事实）硬编码压缩为 direction/polarity（价值标签），且只取第一个 atom。

4. **替代路径已存在**：`EventDirection` 在 `spec/event_ontology_v1.py` 中定义，每个 EventDefinition 有预定义的 direction，可通过 `ontology_type` 查表获得，无需在 engine 层硬编码映射。

5. **修复方向**：在 `CanonicalComposer` 层用 `EVENT_TYPE_BY_ID[ontology_type].direction` 替换 `_ATOM_DIRECTION_MAP[atom]`，使方向推导从"规则引擎层"上移到"规范层"，恢复语义透明度。
