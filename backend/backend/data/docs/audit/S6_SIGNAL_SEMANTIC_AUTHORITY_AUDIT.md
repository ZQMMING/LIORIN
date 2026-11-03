# S6: Signal Semantic Authority Audit — direction/polarity 唯一权威源判定

**Date**: 2026-09-01
**Context**: P0-LEGACY-PATH-AUDIT v2 + S1-S5 trace 结论：SignalEngine 保留，需解决 direction/polarity 权威来源问题

---

## 一、当前三条方向模型的碰撞

### 模型 A：Template 路径（64 条规则）

```
produces_layer_output_template → template["direction"]
```

| 值 | 数量 | 备注 |
|----|------|------|
| `DECLINE` | 38 | **不在** `_ATOM_DIRECTION_MAP` 中 |
| `INCREASE` | 14 | 与 ATOM_MAP 对齐 |
| `STABLE` | 9 | 与 ATOM_MAP 对齐 |
| `VOLATILE` | 3 | **不在** `_ATOM_DIRECTION_MAP` 中 |

### 模型 B：Atom 路径（72 条规则）

```
produces_semantic_atoms → first_atom → _ATOM_DIRECTION_MAP → direction
```

| 值 | 来源 |
|----|------|
| `STABLE` | SUPPORT族（8 atoms） |
| `INCREASE` | ACTION族（6 atoms） |
| `DECREASE` | CONTRACTION族（4 atoms） |

### 模型 C：EventDirection spec（`spec/event_ontology_v1.py`）

```python
class EventDirection(enum.Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    CHANGE = "CHANGE"
    NEUTRAL = "NEUTRAL"
```

**关键事实**：模型 A 和模型 B 的值域与模型 C **完全不相交**。

---

## 二、跨引擎比较逻辑的断裂

`cross_analysis.py:_is_opposite()` 仅识别一对相反关系：

```python
def _is_opposite(d1: str, d2: str) -> bool:
    if d1 == "INCREASE" and d2 == "DECREASE":
        return True
    if d1 == "DECREASE" and d2 == "INCREASE":
        return True
    return False
```

**断裂点**：
- `DECLINE`（38条规则产出）：从不触发 `_is_opposite`，即使它语义上是"下降"
- `VOLATILE`（3条规则产出）：从不触发 `_is_opposite`
- `STABLE` vs `DECREASE`：不触发（但语义上可能应触发）
- 紫微引擎产出 `direction="STABLE"`（硬编码），与八字任何 direction 都"不对立"

**后果**：38条 DECLINE 规则产出的 Signal 在 Cross Analysis 中永远不会被判定为 CONFLICTED，无论紫微是什么方向。这是数据一致性的结构性缺陷。

---

## 三、ontology_type 与 EventDefinition 的映射断层

### 当前规则产出的 ontology_types（11 个）

```
ACTION, CHANGE, CONSTRAINT, OUTPUT, REFLECTION, RELATION, RESOURCE, SUPPORT
HEALTH_RISK, MARRIAGE_OPPORTUNITY, MARRIAGE_RISK   ← 不在 EVENT_TYPE_BY_ID 中
```

### `EVENT_TYPE_BY_ID` 定义的 event types（25 个）

```
EXAM, ADMISSION, GRADUATION, DEGREE, PROMOTION, JOB_CHANGE, RESIGNATION,
DEMOTION, MAJOR_INCOME, MARRIAGE, DIVORCE, CHILD_BIRTH, PARENT_DEATH,
FAMILY_HARMONY, RELOCATION, HEALTH_ISSUE, LEGAL_ISSUE
```

**断层**：
- `HEALTH_RISK` → 无对应 EventDefinition，应映射到 `HEALTH_ISSUE`（EventDirection.NEGATIVE）
- `MARRIAGE_RISK` → 无对应，应映射到 `DIVORCE`（EventDirection.NEGATIVE）或 `PARENT_DEATH`
- `MARRIAGE_OPPORTUNITY` → 无对应，应映射到 `MARRIAGE`（EventDirection.POSITIVE）
- `ACTION`/`OUTPUT`/`CONSTRAINT`/`RESOURCE`/`SUPPORT`/`RELATION`/`REFLECTION`/`CHANGE` → USO 类型，非 Event ID

**更严重的问题**：USO 类型（8 个）与 Event ID（25 个）是**两套命名空间**，目前没有任何代码将 `signal.ontology_type`（USO）映射到 `EventDefinition.id`。

---

## 四、theme_engine 的中文字符串映射缺口

```python
# theme_engine.py:72-74
dir_word = {
    "INCREASE": "增强",
    "STABLE": "平稳",
    "DECREASE": "减弱",
}.get(direction, "平稳")        # ← VOLATILE/DECLINE 全部 fallback 到 "平稳"

pol_word = {
    "active": "活化",
    "neutral": "中性",
    "restricted": "受限",
}.get(polarity, "中性")         # ← template 的 "opportunity"/"caution" 全部 fallback
```

**断裂**：
- 38条 DECLINE 规则的 claim 文本会显示"减弱"（fallback 到 DECREASE 的同义词）或"平稳"（如果走 template 路径且 direction=DECLINE）
- 3条 VOLATILE 规则的 claim 文本固定为"平稳"
- Template 的 polarity="opportunity"/"caution" 全部 fallback 为"中性"

---

## 五、Authority Model 判定

### 用户倾向：Option A

> Signal 保留 direction/polarity，但权威来源从 Semantic Atom 改为 Event Ontology

### 实施前提：需要先解决三重重叠断层

```
当前混乱状态:

Rule
  ├─ produces_layer_output_template  →  direction ∈ {VOLATILE, DECLINE, INCREASE, STABLE}
  │                                      polarity ∈ {opportunity, caution, neutral, ...}
  └─ produces_semantic_atoms         →  first_atom → ATOM_MAP
                                         direction ∈ {STABLE, INCREASE, DECREASE}
                                         polarity ∈ {active, neutral, restricted}
                                              ↓
                                         Signal.direction/polarity
                                              ↓
                              CrossAnalysis._is_opposite()  ← 仅识别 INCREASE↔DECREASE
                                              ↓
                              theme_engine.reframe_claim()   ← 仅映射 INCREASE/STABLE/DECREASE
```

```
目标状态 (Option A):

Rule
  ├─ produces_layer_output_template  →  ontology_type (USO)  ← 不变
  └─ produces_semantic_atoms         →  ontology_type (USO)  ← 不变
                                              ↓
                              ontology_type → USO→EventDirection 映射表（新增）
                                              ↓
                              Signal.direction = EventDirection (POSITIVE/NEGATIVE/CHANGE/NEUTRAL)
                                              ↓
                              CrossAnalysis._is_opposite()  ← 改为 EventDirection 比较
                                              ↓
                              theme_engine.reframe_claim()   ← 改为 EventDirection 中文映射
```

### 新增映射表设计

| USO Type | EventDirection | 依据 |
|----------|---------------|------|
| ACTION | POSITIVE | 行动驱动增长 |
| OUTPUT | POSITIVE | 输出表达创造 |
| RESOURCE | POSITIVE | 资源支撑 |
| SUPPORT | NEUTRAL | 稳定支撑，不增不减 |
| RELATION | NEUTRAL | 关系中性，依赖具体情境 |
| CONSTRAINT | NEGATIVE | 约束限制 |
| REFLECTION | NEUTRAL | 内省观察 |
| CHANGE | CHANGE | 变化本身 |

**注意**：这是从 ontology 语义推导，而非从 atom 推导。一张表替代 36 行的 `_ATOM_DIRECTION_MAP`。

### polarity 的去留决策

polarity（active/neutral/restricted）与 direction 正交：
- direction = 事件本身的语义方向（来自 ontology）
- polarity = 该信号在当前命盘中的状态（来自 rule conclusion 的附加信息）

**建议**：保留 polarity，但同样从 `produces_layer_output_template["polarity"]` 或原子组合推导，而非硬编码在 atom map 中。

---

## 六、S6 结论与阻塞清单

### 核心结论

| 问题 | 当前状态 | 需修复 |
|------|----------|--------|
| direction 权威来源 | Semantic Atom → ATOM_MAP | → EventOntology 映射表 |
| direction 值域对齐 | 三个不相交集合 | → 统一为 EventDirection |
| `_is_opposite()` | 仅识别 INCREASE↔DECREASE | → 改为 EventDirection.NEGATIVE↔POSITIVE |
| ontology_type 映射 | USO 类型无 EventDefinition | → 新增 USO→EventDirection 映射表 |
| theme_engine 映射 | 仅覆盖 INCREASE/STABLE/DECREASE | → 覆盖 EventDirection 四值 |
| TEMPLATE direction | VOLATILE/DECLINE 无对应 | → 纳入映射表或废弃 |

### 不阻塞但需记录

- `HEALTH_RISK/MARRIAGE_OPPORTUNITY/MARRIAGE_RISK` 不在 USO_TYPES：需 DECISION-010 处理
- `legacy_adapter.py` 的 `_DIRECTION_MAP` 不包含 STABLE/INCREASE/DECREASE：adapter 本身有 bug
- `ziwei_engine.extract_baseline_signal()` 硬编码 `direction="STABLE"`：需用映射表替代

### 修复范围（一次性迁移，避免双来源）

| 文件 | 修改内容 |
|------|----------|
| `spec/signal_ontology.py` | 新增 `USO_TO_EVENT_DIRECTION` 映射表 |
| `reasoning/signal_engine.py` | 移除 `_ATOM_DIRECTION_MAP`/`_ATOM_POLARITY_MAP`；`_derive_direction_polarity()` 改为查映射表 |
| `reasoning/cross_analysis.py` | `_is_opposite()` 改为 EventDirection 比较 |
| `reasoning/theme_engine.py` | 中文映射改为 EventDirection |
| `canonical/composer.py` | 序列化改用 EventDirection.value |
| `engines/ziwei_engine.py` | `extract_baseline_signal` 改查映射表 |

---

## 七、风险评估

### 破坏性变更

- `Signal.direction` 值域从 `{STABLE, INCREASE, DECREASE}` 变为 `{POSITIVE, NEGATIVE, CHANGE, NEUTRAL}`
- 所有现有测试中引用 `.direction` 的比较需要更新
- `atomic_claims` 中 `direction` 字段的值会改变

### 缓解策略

1. 先在 `spec/signal_ontology.py` 增加映射表，不改任何运行时逻辑
2. 修改 `_derive_direction_polarity()` 使用新映射表（保持返回值类型不变，内部替换查找表）
3. 逐步替换下游消费者（cross_analysis, theme_engine, composer）
4. 最后再考虑将 `Signal.direction` 类型从 `str` 改为 `EventDirection`

---

## 附录：当前规则产出方向分布统计

```
Template 路径 (64 rules):
  DECLINE     38 rules  → Signal.direction = "DECLINE" (不在 _is_opposite 中)
  INCREASE    14 rules  → Signal.direction = "INCREASE"
  STABLE       9 rules  → Signal.direction = "STABLE")
  VOLATILE     3 rules  → Signal.direction = "VOLATILE" (不在映射中)

Atom 路径 (72 rules):
  SUPPORT     18 rules  → Signal.direction = "STABLE"
  CONSTRAINT  18 rules  → Signal.direction = "DECREASE"
  OUTPUT      16 rules  → Signal.direction = "INCREASE"
  RESOURCE     7 rules  → Signal.direction = "STABLE"
  REFLECTION   6 rules  → Signal.direction = "STABLE"
  RELATION     5 rules  → Signal.direction = "STABLE"
  CHANGE       1 rules  → Signal.direction = "INCREASE"
  ACTION       1 rules  → Signal.direction = "INCREASE"

Cross Analysis 实际生效的相反对:
  INCREASE ↔ DECREASE:  (14+1+16+1) vs (18+18) rules = 32 vs 36 rules
  其他所有组合: 不触发 _is_opposite
```

**38条 DECLINE 规则在 Cross Analysis 中永远无法产生 CONFLICTED 结果**——这是已确认的结构性缺陷。
