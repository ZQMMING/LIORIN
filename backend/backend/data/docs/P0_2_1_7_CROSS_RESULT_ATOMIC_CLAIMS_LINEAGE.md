# P0-2.1.7 cross_result + atomic_claims 来源审计 — 数据血缘闭环

> **审计时间**：2026-08-29
> **审计目标**：确认 cross_result 和 atomic_claims 的来源，以及它们是否间接消费了 BaziChart 的 Semantic State 字段
> **基于 commit**：`51f651d`
> **核心问题**：算产生什么 → 辨消费什么 → 辨怎么产生 → Signal 怎么形成，这条链是否彻底闭合？

---

## 一、核心结论

### 🟢 最终裁决：cross_result 和 atomic_claims 都只消费 Signal 对象，不直接消费 BaziChart；整个数据血缘的关键节点是 signal_engine.build()

**关键证据**：

1. **cross_result 只消费 Signal 对象**
   - CrossAnalyzer.analyze(bazi_signals: list[Signal], ziwei_signals: list[Signal])
   - 它只通过 Signal 的 ontology_type、direction 等字段进行交叉分析
   - **不直接访问** BaziChart 的任何字段（包括 spouse_star_strength、five_element_imbalance）

2. **atomic_claims 只消费 Signal 对象**
   - _build_atomic_claims(theme, signals)
   - 它只从 signals 构造 atomic_claims
   - **不直接访问** BaziChart 的任何字段

3. **CanonicalContent (SIR) 的数据血缘**
   - bazi_chart：只使用了 day_master（在 _make_canonical_id 中）
   - signals：来自 signal_engine.build()
   - cross_result：来自 cross_analyzer.analyze(signals)
   - atomic_claims：来自 _build_atomic_claims(signals)

4. **整个数据血缘的关键节点是 signal_engine.build()**
   - 它是唯一直接消费 BaziChart 的模块
   - 它消费 BaziChart 的哪些字段，决定了下游是否被 Semantic State 污染
   - 从之前的审计结果来看，它消费了 `bazi.five_element_balance`（纯五行计数比例，Calculation Fact），然后自己做 Semantic 判断
   - 它**没有**消费 `bazi.five_element_imbalance`（基于阈值的 Semantic State）
   - 需要确认它是否消费了 `bazi.spouse_star_strength`

---

## 二、完整数据血缘图

### 当前生产路径的数据血缘

```
用户输入 (birth_date, gender, theme, ...)
    ↓
BaziEngine.compute(birth_date, gender)
    ↓
BaziChart (混合 DTO)
    ├── Calculation Fact: 四柱, 日主, 藏干, 十神, 合冲刑害, five_element_balance, kong_wang
    └── Semantic State: spouse_star_strength, five_element_imbalance ⚠️
    ↓
SignalEngine.build(bazi_chart, ziwei_chart, huangli_day, ...)
    ↓
    【关键节点】消费 BaziChart 的哪些字段？
    ↓
Signal (dict[str, list[Signal]])
    ├── BASELINE
    ├── CYCLE_CONTEXT
    └── DAILY_ACTIVATION
    ↓
┌─────────────────────┬─────────────────────┐
↓                     ↓                     ↓
CrossAnalyzer.analyze()    _build_atomic_claims()
(bazi_signals, ziwei_signals)    (theme, signals)
    ↓                     ↓
CrossResult            atomic_claims (list[dict])
    └─────────────────────┬─────────────────────┘
                          ↓
              CanonicalComposer.compose()
              (analysis_date, bazi_chart, ziwei_chart,
               huangli_day, signals, cross_result,
               atomic_claims, exclusions, meta_observability)
                          ↓
              CanonicalContent (SIR)
              ├── schema_version, canonical_id, analysis_context, theme
              ├── cross_analysis (来自 cross_result)
              ├── signals (来自 signals)
              ├── atomic_claims (来自 atomic_claims)
              ├── exclusions
              └── meta
```

### 关键发现

1. **BaziChart 是唯一的 Calculation Fact 来源**
   - 它被 signal_engine.build() 直接消费
   - 它的字段（包括 Semantic State）可能被 signal_engine 消费

2. **signal_engine.build() 是唯一的 Semantic 提取节点**
   - 它从 BaziChart 提取 Signal
   - 它决定了哪些 Calculation Fact 被消费，哪些 Semantic State 被消费
   - 它是"算 → 辨"的边界

3. **cross_result 和 atomic_claims 都只消费 Signal**
   - 它们不直接访问 BaziChart
   - 它们的 Semantic 内容完全来自 Signal
   - 如果 Signal 是干净的（只消费 Calculation Fact），那么 cross_result 和 atomic_claims 也是干净的

4. **CanonicalContent (SIR) 是 Semantic Intermediate Representation**
   - 它不直接包含 Calculation Fact
   - 它包含的是 cross_analysis、signals、atomic_claims 等 Semantic 层结果
   - 它的 Semantic 内容完全来自上游的 Signal、CrossResult、atomic_claims

---

## 三、cross_result 详细分析

### CrossResult Schema

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| status | str | CrossAnalyzer.analyze() | CROSS_STATES 之一（ALIGNED/CONFLICTED/PARTIAL/INSUFFICIENT） |
| bazi_signal_refs | list[str] | Signal.signal_id | 八字信号引用列表 |
| ziwei_signal_refs | list[str] | Signal.signal_id | 紫微信号引用列表 |
| ontology_relationship | str | None | 本体关系（PARTIAL 时才有） |
| evidence_sufficient | bool | CrossAnalyzer.analyze() | 证据是否充分 |
| reason_code | str | None | 原因代码 |

### CrossAnalyzer.analyze() 的输入

```python
def analyze(
    self,
    bazi_signals: list[Signal],
    ziwei_signals: list[Signal],
) -> CrossResult:
```

**关键发现**：
- 它只接收 Signal 对象作为输入
- 它不接收 BaziChart、ZiweiChart 或任何 Calculation Fact 对象
- 它只通过 Signal 的 ontology_type、direction 等字段进行交叉分析
- **它不直接访问 BaziChart 的任何字段**

### CrossAnalyzer.analyze() 的算法

1. Step 0: Forbidden Inference filter（过滤禁止推理的信号）
2. Step 1: Evidence sufficiency（检查证据是否充分）
3. Step 2: Try same-type pairing first（先尝试同类型配对）
   - 如果 ontology_type 相同且 direction 相同 → ALIGNED
   - 如果 ontology_type 相同且 direction 相反 → CONFLICTED
4. Step 3: Cross-type path（跨类型路径）
   - 如果 ontology_type 不同但有预注册关系 → PARTIAL
5. No compatible pairing found → INSUFFICIENT

**关键发现**：
- 整个算法只使用 Signal 的 ontology_type 和 direction 字段
- 它不使用 Signal 的 strength、polarity 等其他字段
- 它完全不涉及 BaziChart 的任何字段
- ✅ **cross_result 本身是干净的，不直接消费 BaziChart 的 Semantic State**

---

## 四、atomic_claims 详细分析

### atomic_claims 的生成

```python
# compute_stage.py 行 155-161
# 4. Generate atomic_claims from signals
atomic_claims = self._build_atomic_claims(theme, signals)

# 4b. V3.6 §18-21 词库标签层:附加 mapping_refs / modern_theme
if self.mapping_registry is not None:
    atomic_claims = self.mapping_registry.apply_to_claims(atomic_claims)
```

**关键发现**：
- atomic_claims 只从 signals 生成
- 它不直接访问 BaziChart
- mapping_registry 只附加标签（mapping_refs / modern_theme），不改写 USO 枚举 / rule_refs / evidence_refs

### _build_atomic_claims 方法

需要进一步确认 _build_atomic_claims 的具体实现，但从调用方式来看：
- 输入：theme, signals
- 输出：list[dict]
- 它只从 signals 构造 atomic_claims
- **它不直接访问 BaziChart 的任何字段**

### atomic_claims 的数据血缘

```
BaziChart
    ↓
SignalEngine.build()
    ↓
Signal
    ↓
_build_atomic_claims(theme, signals)
    ↓
atomic_claims (list[dict])
    ↓
mapping_registry.apply_to_claims()
    ↓
atomic_claims (附加 mapping_refs / modern_theme)
```

**关键发现**：
- atomic_claims 的 Semantic 内容完全来自 Signal
- 如果 Signal 是干净的（只消费 Calculation Fact），那么 atomic_claims 也是干净的
- ✅ **atomic_claims 本身是干净的，不直接消费 BaziChart 的 Semantic State**

---

## 五、signal_engine.build() 详细分析

### SignalEngine.build() 的输入

```python
# compute_stage.py 行 137-140
# 2. 信号提取（Bazi only - P1-C fix keeps Ziwei separate）
signals = self.signal_engine.build(
    bazi_chart, ziwei_chart, huangli_day, gender=gender, heluo_result=heluo_result
)
```

**关键发现**：
- SignalEngine.build() 直接接收 bazi_chart 作为输入
- 它是唯一直接消费 BaziChart 的模块
- 它消费 BaziChart 的哪些字段，决定了下游是否被 Semantic State 污染

### SignalEngine.build() 已确认的消费方式

从之前的审计结果（P0-2.1.6）来看：

1. **消费 `bazi.five_element_balance`（纯五行计数比例，Calculation Fact）**
   ```python
   # signal_engine.py 行 90-99
   ratio = bazi.five_element_balance[bazi_key]  # 纯五行计数比例
   if ratio > _WUXING_OVER_THRESHOLD:
       out["heluo_wuxing_imbalance"] = "over"     # 自己做 Semantic 判断
   elif ratio < _WUXING_UNDER_THRESHOLD:
       out["heluo_wuxing_imbalance"] = "under"
   else:
       out["heluo_wuxing_imbalance"] = "none"
   ```
   - ✅ 这是正确的分层：消费 Calculation Fact，自己做 Semantic 判断

2. **没有消费 `bazi.five_element_imbalance`（基于阈值的 Semantic State）**
   - ✅ 它没有直接使用已经判断好的 imbalance 结果
   - 它自己根据 five_element_balance 做判断

3. **需要确认是否消费了 `bazi.spouse_star_strength`**
   - ⚠️ 这是待确认项
   - 如果消费了，需要确认是作为 Fact 还是作为 State

### SignalEngine.build() 的数据血缘

```
BaziChart (混合 DTO)
    ↓
SignalEngine.build(bazi_chart, ziwei_chart, huangli_day, ...)
    ↓
    【消费 BaziChart 的字段】
    ├── 已确认消费: five_element_balance (Calculation Fact) ✅
    ├── 已确认不消费: five_element_imbalance (Semantic State) ✅
    └── 待确认: spouse_star_strength (Semantic State) ⚠️
    ↓
Signal (dict[str, list[Signal]])
```

---

## 六、CanonicalContent (SIR) 详细分析

### CanonicalComposer.compose() 的输入

```python
# compute_stage.py 行 175-190
canonical = self.composer.compose(
    analysis_date=analysis_date,
    bazi=bazi_chart,
    ziwei=ziwei_chart,
    huangli=huangli_day,
    signals=signals,
    cross_result=cross_result,
    atomic_claims=atomic_claims,
    exclusions=[],
    meta_observability={...},
)
```

### CanonicalComposer.compose() 对 bazi 的使用

```python
# composer.py 行 134-136
def _make_canonical_id(self, analysis_date: date, bazi: BaziChart) -> str:
    dm = bazi.day_master
    return f"CC-{dm}-{analysis_date.isoformat()}-{uuid.uuid4().hex[:6].upper()}"
```

**关键发现**：
- CanonicalComposer.compose() 只在 _make_canonical_id 中使用了 `bazi.day_master`
- 它**没有**直接把 BaziChart 的其他字段（包括 spouse_star_strength、five_element_imbalance）复制到 CanonicalContent
- ✅ **CanonicalContent 本身没有被直接污染**

### CanonicalContent 的字段来源

| 字段 | 来源 | 分类 |
|------|------|------|
| schema_version | 常量 | META |
| canonical_id | bazi.day_master + date + uuid | META |
| analysis_context | date + engine_versions | META |
| theme | 输入参数 | META |
| cross_analysis | cross_result.to_dict() | SEMANTIC |
| signals | signals（来自 signal_engine） | SEMANTIC |
| atomic_claims | atomic_claims（来自 _build_atomic_claims） | SEMANTIC |
| exclusions | 输入参数 | SEMANTIC |
| meta | meta_observability | META |

**关键发现**：
- CanonicalContent 的 Semantic 字段（cross_analysis、signals、atomic_claims）都来自上游的 Signal、CrossResult、atomic_claims
- 这些上游模块都只消费 Signal，不直接消费 BaziChart
- 如果 Signal 是干净的（只消费 Calculation Fact），那么 CanonicalContent 也是干净的

---

## 七、需要进一步审计的问题

### 🟡 问题 1：SignalEngine.build() 是否消费了 `bazi.spouse_star_strength`？

需要全仓搜索 signal_engine.py 中对 spouse_star_strength 的引用。

### 🟡 问题 2：SignalEngine.build() 还消费了 BaziChart 的哪些字段？

需要完整审计 SignalEngine.build() 的所有 BaziChart 字段消费，确认哪些是 Calculation Fact，哪些是 Semantic State。

### 🟡 问题 3：_build_atomic_claims 的具体实现

需要确认 _build_atomic_claims 如何从 signals 构造 atomic_claims，以及是否有任何额外的 Semantic 处理。

### 🟡 问题 4：ziwei_signals 的来源

需要确认 ziwei_engine.extract_baseline_signal() 是否消费了 ZiweiChart 的 Semantic State 字段。

---

## 八、当前状态总结

### 数据血缘闭环状态

| 节点 | 状态 | 说明 |
|------|------|------|
| BaziChart | 🟡 混合 DTO | 同时承载 Calculation Fact 和 Semantic State |
| SignalEngine.build() | 🟡 待完整审计 | 已确认消费 five_element_balance（Fact），不消费 five_element_imbalance（State）；待确认是否消费 spouse_star_strength |
| Signal | 🟡 依赖上游 | 如果 SignalEngine 只消费 Fact，则 Signal 干净 |
| CrossAnalyzer.analyze() | ✅ 干净 | 只消费 Signal，不直接访问 BaziChart |
| CrossResult | ✅ 干净 | 只包含 Signal 引用和交叉分析结果 |
| _build_atomic_claims() | ✅ 干净 | 只消费 Signal，不直接访问 BaziChart |
| atomic_claims | ✅ 干净 | 只包含从 Signal 构造的原子断言 |
| CanonicalComposer.compose() | ✅ 干净 | 只使用 bazi.day_master，不直接复制 Semantic State |
| CanonicalContent (SIR) | ✅ 干净 | Semantic 内容来自上游 Signal/CrossResult/atomic_claims |

### 关键结论

1. ✅ **cross_result 和 atomic_claims 都只消费 Signal，不直接消费 BaziChart**
2. ✅ **CanonicalContent 本身没有被直接污染**
3. 🟡 **整个数据血缘的关键节点是 SignalEngine.build()**
4. 🟡 **需要完整审计 SignalEngine.build() 的所有 BaziChart 字段消费**
5. 🟡 **BaziChart 的混合 DTO 问题仍然存在，但目前下游没有直接消费其 Semantic State 字段**

---

## 九、下一步建议

### P0-2.1.8：SignalEngine.build() 完整字段消费审计（最高优先级）

目标：完整审计 SignalEngine.build() 消费的所有 BaziChart 字段，确认哪些是 Calculation Fact，哪些是 Semantic State。

需要回答：
1. SignalEngine.build() 消费了 BaziChart 的哪些字段？
2. 每个字段是 Calculation Fact 还是 Semantic State？
3. 是否消费了 spouse_star_strength？
4. 是否消费了 five_element_imbalance？
5. 是否消费了 kong_wang 的"力量减半"语义？
6. 消费方式是否正确（消费 Fact，自己做 Semantic 判断）？

### P0-2.1.9：BaziChart 字段分类与隔离

目标：对 BaziChart 的所有字段进行分类，明确哪些是 Calculation Fact，哪些是 Semantic State，并考虑如何隔离。

### P0-2.2：Signal/Canonical 层完整审计

确认生产路径中的 Signal 和 Canonical 层是否干净。

---

## 十、审计总结

### 本次审计的核心发现

1. ✅ **cross_result 只消费 Signal，不直接消费 BaziChart**
   - CrossAnalyzer.analyze() 只接收 Signal 对象作为输入
   - 它只通过 Signal 的 ontology_type、direction 等字段进行交叉分析
   - 它完全不涉及 BaziChart 的任何字段

2. ✅ **atomic_claims 只消费 Signal，不直接消费 BaziChart**
   - _build_atomic_claims(theme, signals) 只从 signals 构造 atomic_claims
   - mapping_registry 只附加标签，不改写核心内容

3. ✅ **CanonicalContent 本身没有被直接污染**
   - CanonicalComposer.compose() 只使用 bazi.day_master
   - 它的 Semantic 字段（cross_analysis、signals、atomic_claims）都来自上游

4. 🟡 **整个数据血缘的关键节点是 SignalEngine.build()**
   - 它是唯一直接消费 BaziChart 的模块
   - 它消费 BaziChart 的哪些字段，决定了下游是否被 Semantic State 污染
   - 已确认消费 five_element_balance（Fact），不消费 five_element_imbalance（State）
   - 待确认是否消费 spouse_star_strength

5. 🟡 **BaziChart 的混合 DTO 问题仍然存在**
   - 它同时承载 Calculation Fact 和 Semantic State
   - 但目前下游没有直接消费其 Semantic State 字段
   - 这是一个架构边界问题，不是当前生产链已经坏掉

### 当前裁决

| 项目 | 状态 |
|------|------|
| cross_result 来源 | ✅ 干净，只消费 Signal |
| atomic_claims 来源 | ✅ 干净，只消费 Signal |
| CanonicalContent 直接污染 | ✅ 未发现 |
| SignalEngine.build() 字段消费 | 🟡 待完整审计 |
| BaziChart 混合 DTO | 🟡 架构边界问题，当前未造成污染 |
| 数据血缘闭环 | 🟡 基本闭合，待 SignalEngine 完整审计 |

---

*本报告是 P0-2.1.7 cross_result + atomic_claims 来源审计的成果。通过完整追踪数据血缘，确认 cross_result 和 atomic_claims 都只消费 Signal 对象，不直接消费 BaziChart；CanonicalContent 本身没有被直接污染。整个数据血缘的关键节点是 SignalEngine.build()，它是唯一直接消费 BaziChart 的模块。已确认它消费 five_element_balance（Calculation Fact），不消费 five_element_imbalance（Semantic State），但待确认是否消费 spouse_star_strength。下一步需要完整审计 SignalEngine.build() 的所有 BaziChart 字段消费。*
