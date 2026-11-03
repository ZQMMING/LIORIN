# P0-2.1.6 Canonical State Boundary Audit — canonical/composer.py + CanonicalContent Schema

> **审计时间**：2026-08-29
> **审计目标**：确认 Canonical State 的完整 schema、每个字段来源，以及是否有 Semantic State 混入 Canonical Facts
> **基于 commit**：`52561da`
> **核心问题**：到底什么东西才有资格进入 Canonical State？

---

## 一、核心结论

### 🟡 最终裁决：Canonical State 本身没有被直接污染，但 BaziChart 存在 Calculation + Interpretation 混合 DTO 的架构边界问题

**关键证据**：

1. **canonical/composer.py 只使用了 `bazi.day_master`**
   - 行 135：`dm = bazi.day_master`（在 _make_canonical_id 中）
   - **没有**直接把 spouse_star_strength、five_element_balance、five_element_imbalance、kong_wang 等字段复制到 CanonicalContent
   - ✅ Canonical State 本身没有被直接污染

2. **signal_engine.py 消费了 `bazi.five_element_balance`，但是正确的分层**
   - 行 90-99：使用 `bazi.five_element_balance[bazi_key]`（纯五行计数比例，Calculation Fact）
   - 然后自己根据 ratio 和阈值判断 `heluo_wuxing_imbalance`（Semantic State）
   - ✅ 这是正确的分层！Calculation Fact → Semantic 判断

3. **但是 BaziChart 存在架构边界问题**
   - BaziChart 既承载 Calculation Fact（四柱、十神、藏干、合冲刑害）
   - 又承载 Semantic State（spouse_star_strength、five_element_imbalance）
   - 🔴 这是一个 Calculation + Interpretation 混合 DTO

4. **calc_five_element_balance 返回两个值，需要拆层**
   - `balance`：五行分布的归一化比例（纯 Calculation Fact）✅
   - `imbalance`：失衡标记（基于阈值 max > 0.40 或 min < 0.05 的 Semantic State）⚠️
   - 这两个值被同时附加到 BaziChart，造成 Fact / Semantic 混合

---

## 二、CanonicalContent Schema 完整分析

### CanonicalContent 字段列表

| 字段 | 类型 | 来源 | 分类 | 说明 |
|------|------|------|------|------|
| schema_version | str | 常量 | META | SIR 版本 |
| canonical_id | str | bazi.day_master + date + uuid | META | 唯一标识 |
| analysis_context | dict | date + engine_versions | META | 分析上下文 |
| theme | str | 输入参数 | META | 主题 |
| cross_analysis | dict | cross_result.to_dict() | SEMANTIC | 交叉分析结果 |
| signals | dict | signals（来自 signal_engine） | SEMANTIC | 语义信号 |
| atomic_claims | list[dict] | 输入参数 | SEMANTIC | 原子断言 |
| exclusions | list[dict] | 输入参数 | SEMANTIC | 排除项 |
| meta | dict | meta_observability | META | 可观测性元数据 |

### 关键发现

1. **CanonicalContent 本身不直接包含 BaziChart 的 Calculation Facts**
   - 它包含的是 cross_analysis、signals、atomic_claims 等 Semantic 层结果
   - 它不直接包含四柱、十神、藏干、合冲刑害等 Calculation Facts
   - 这意味着 CanonicalContent 更像是一个 Semantic Intermediate Representation，而不是 Canonical Facts 容器

2. **CanonicalContent 的 Semantic 字段来自外部**
   - cross_analysis 来自 cross_result（CrossResult）
   - signals 来自 signal_engine
   - atomic_claims 来自外部输入
   - 这些 Semantic 字段可能间接消费了 BaziChart 的有问题字段

3. **需要进一步审计 cross_result 和 atomic_claims 的来源**
   - cross_result 是否消费了 BaziChart 的 Semantic State 字段？
   - atomic_claims 是否消费了 BaziChart 的 Semantic State 字段？

---

## 三、calc_five_element_balance 详细分析

### 函数实现

```python
def calc_five_element_balance(chart: BaziChart) -> tuple[dict, bool]:
    """五行分布(归一化) + 失衡标记 (max > 0.40 或 min < 0.05)."""
    counts = {"WOOD": 0, "FIRE": 0, "EARTH": 0, "METAL": 0, "WATER": 0}
    for s in chart.four_stems():
        counts[STEM_ELEMENT[s]] += 1
    for b in chart.four_branches():
        counts[_branch_element(b)] += 1
    total = sum(counts.values()) or 1
    balance = {k: v / total for k, v in counts.items()}
    imbalance = (max(balance.values()) > 0.40) or (min(balance.values()) < 0.05)
    return balance, imbalance
```

### 返回值分类

| 返回值 | 类型 | 分类 | 说明 |
|--------|------|------|------|
| `balance` | dict[str, float] | **CALCULATION_FACT** ✅ | 五行分布的归一化比例，纯客观统计 |
| `imbalance` | bool | **SEMANTIC_STATE** ⚠️ | 基于阈值（max > 0.40 或 min < 0.05）的失衡判断，未经原典授权 |

### signal_engine.py 的消费方式

```python
# 行 90-99
if benming_wuxing and bazi and getattr(bazi, "five_element_balance", None):
    bazi_key = _HELUO_WUXING_TO_BASI_KEY.get(benming_wuxing)
    if bazi_key and bazi_key in bazi.five_element_balance:
        ratio = bazi.five_element_balance[bazi_key]
        if ratio > _WUXING_OVER_THRESHOLD:
            out["heluo_wuxing_imbalance"] = "over"
        elif ratio < _WUXING_UNDER_THRESHOLD:
            out["heluo_wuxing_imbalance"] = "under"
        else:
            out["heluo_wuxing_imbalance"] = "none"
```

**关键发现**：
- signal_engine.py 消费的是 `bazi.five_element_balance`（即 `balance`，纯五行计数比例）
- 它**没有**消费 `bazi.five_element_imbalance`（即 `imbalance`，Semantic State）
- 它自己根据 ratio 和阈值判断 `heluo_wuxing_imbalance`
- ✅ **这是正确的分层！Calculation Fact → Semantic 判断**

---

## 四、BaziChart 架构边界问题

### BaziChart 字段分类（基于 attach_p2_fields）

| 字段 | 分类 | 说明 |
|------|------|------|
| year_pillar, month_pillar, day_pillar, hour_pillar | CALCULATION_FACT ✅ | 四柱 |
| day_master | CALCULATION_FACT ✅ | 日主 |
| hidden_stems | CALCULATION_FACT ✅ | 藏干 |
| ten_gods | CALCULATION_FACT ✅ | 十神 |
| branch_clash_map, branch_harm_map, branch_he_map | CALCULATION_FACT ✅ | 合冲刑害 |
| branch_sanhe_map, branch_sanxing_map | CALCULATION_FACT ✅ | 三合三刑 |
| kong_wang | MIXED ⚠️ | 空亡计算是 Fact，但"力量减半"是 Semantic |
| five_element_balance | CALCULATION_FACT ✅ | 五行计数比例 |
| **five_element_imbalance** | **SEMANTIC_STATE** 🔴 | 基于阈值的失衡判断 |
| **spouse_star_strength** | **SEMANTIC_STATE** 🔴 | score → strong/weak/rootless 阈值分类 |
| spouse_star, spouse_star_attack, officer_mixed | UNKNOWN ⚠️ | 需要人工审计 |
| peach_blossom, day_branch_clash, day_branch_harm | CALCULATION_FACT ✅ | 神煞/关系 |
| day_branch_main_ten_god | CALCULATION_FACT ✅ | 日支主气十神 |

### 核心问题

**BaziChart 是一个 Calculation + Interpretation 混合 DTO。**

它既承载：
- 四柱、十神、藏干、合冲刑害（Calculation Fact）

又承载：
- spouse_star_strength（Semantic State，score → strong/weak/rootless）
- five_element_imbalance（Semantic State，基于阈值的失衡判断）

这造成了：
1. **Fact / Semantic 边界模糊**：消费方无法明确区分哪些是 Fact，哪些是 Semantic
2. **Semantic State 可能被误当成 Fact**：消费方可能直接使用 five_element_imbalance，而不是自己根据 five_element_balance 判断
3. **架构污染风险**：未经授权的 Semantic State 混入 Calculation Result，可能被下游误消费

---

## 五、需要进一步审计的问题

### 🟡 问题 1：cross_result 是否消费了 BaziChart 的 Semantic State 字段？

需要确认：
- CrossResult 的来源是什么？
- 它是否消费了 spouse_star_strength、five_element_imbalance 等字段？
- 它的 cross_analysis 结果是否包含未经授权的 Semantic 判断？

### 🟡 问题 2：atomic_claims 是否消费了 BaziChart 的 Semantic State 字段？

需要确认：
- atomic_claims 的来源是什么？
- 它是否消费了 spouse_star_strength、five_element_imbalance 等字段？

### 🟡 问题 3：是否有其他模块消费了 `bazi.five_element_imbalance` 或 `bazi.spouse_star_strength`？

需要全仓搜索：
- 谁消费了 `bazi.five_element_imbalance`？
- 谁消费了 `bazi.spouse_star_strength`？
- 这些消费是否是正确的分层，还是越界？

### 🟡 问题 4：13 个 UNKNOWN 方法的人工审计

需要人工审计 13 个无法自动分类的方法，确认它们的输出属于 Calculation Fact 还是 Semantic State。

---

## 六、建议的架构拆分

### 当前架构（有问题）

```
Bazi Input
    ↓
BaziEngine.compute()
    ↓
BaziChart (混合 DTO)
    ├── pillars, ten_gods, hidden_stems (Calculation Fact)
    ├── five_element_balance (Calculation Fact)
    ├── five_element_imbalance (Semantic State) ❌
    ├── spouse_star_strength (Semantic State) ❌
    └── kong_wang (MIXED)
    ↓
CanonicalComposer.compose(bazi, ...)
    ↓
CanonicalContent (SIR)
```

### 建议架构（拆层）

```
Bazi Input
    ↓
BaziCalculation
    ↓
┌──────────────────────┐
│ Canonical Facts      │  ← 纯事实，不包含任何 Semantic 判断
│ - pillars            │
│ - ten_gods           │
│ - hidden_stems       │
│ - relations (合冲刑害)│
│ - five_element_counts│  ← 五行计数（纯客观统计）
│ - kong_wang          │  ← 空亡计算（纯事实）
└──────────────────────┘
    ↓
┌─────────────┬─────────────┐
↓             ↓             ↓
子平辨        盲派辨        紫微辨
(格局/结构)  (应事/人事)   (宫域/星曜)
    ↓             ↓             ↓
Semantic State  Semantic State  Semantic State
- 身强/身弱     - 应事结构     - 宫域状态
- 格局成立      - 人事落点     - 星曜组合
- 调候状态      - 时间状态     - 四化状态
    └─────────────┼─────────────┘
                  ↓
          Multi-Dimensional State
                  ↓
              Signal Engine
                  ↓
              Semantic Signals
                  ↓
          CanonicalContent (SIR)
```

### 关键原则

1. **Canonical Facts 只包含纯客观计算结果**，不包含任何基于阈值/权重/评分的 Semantic 判断
2. **Semantic State 由各体系独立辨识**，不回写到 Canonical Facts
3. **Signal Engine 消费 Canonical Facts，生成 Semantic Signals**
4. **CanonicalContent (SIR) 包含 Semantic 层结果**，不直接包含 Canonical Facts

---

## 七、下一步建议

### P0-2.1.7：cross_result + atomic_claims 来源审计（高优先级）

确认 cross_result 和 atomic_claims 是否消费了 BaziChart 的 Semantic State 字段。

### P0-2.1.8：全仓搜索 five_element_imbalance 和 spouse_star_strength 的消费方（高优先级）

确认是否有其他模块消费了这两个 Semantic State 字段，以及消费方式是否正确。

### P0-2.2：Signal/Canonical 层完整审计

确认生产路径中的 Signal 和 Canonical 层是否干净：
- signal_engine.py 是否只消费 Calculation Fact？
- cross_analysis 是否只消费 Calculation Fact？
- atomic_claims 是否只消费 Calculation Fact？

### P0-2.3：分类与隔离

对 BaziChart 中的 Semantic State 字段进行边界确认或隔离：
- five_element_imbalance：标记为 Semantic State，从 Calculation Contract 中剥离
- spouse_star_strength：标记为 Semantic State / Legacy Candidate，从 Calculation Contract 中剥离
- kong_wang：拆分为 Calculation Fact（空亡计算）和 Semantic Rule（力量变化）

---

## 八、审计总结

### 本次审计的核心发现

1. ✅ **Canonical State (CanonicalContent) 本身没有被直接污染**
   - canonical/composer.py 只使用了 `bazi.day_master`
   - 没有直接把 Semantic State 字段复制到 CanonicalContent

2. ✅ **signal_engine.py 消费 five_element_balance 的方式是正确的分层**
   - 消费纯五行计数比例（Calculation Fact）
   - 自己做 Semantic 判断（heluo_wuxing_imbalance）

3. 🔴 **BaziChart 存在 Calculation + Interpretation 混合 DTO 的架构边界问题**
   - 既承载 Calculation Fact，又承载 Semantic State
   - Fact / Semantic 边界模糊
   - 存在 Semantic State 被误当成 Fact 的风险

4. ⚠️ **calc_five_element_balance 返回两个值，需要拆层**
   - balance：Calculation Fact ✅
   - imbalance：Semantic State ⚠️

### 当前状态

| 项目 | 状态 |
|------|------|
| Canonical State 直接污染 | ✅ 未发现 |
| Signal 层消费方式 | ✅ 正确分层（已确认 five_element_balance） |
| BaziChart 架构边界 | 🔴 存在混合 DTO 问题 |
| five_element_imbalance 消费方 | ⚠️ 待确认 |
| spouse_star_strength 消费方 | ⚠️ 待确认 |
| cross_result 来源 | ⚠️ 待确认 |
| atomic_claims 来源 | ⚠️ 待确认 |

---

*本报告是 P0-2.1.6 Canonical State Boundary Audit 的成果。通过审计 canonical/composer.py 和 CanonicalContent Schema，确认 Canonical State 本身没有被直接污染，signal_engine.py 消费 five_element_balance 的方式是正确的分层。但是发现 BaziChart 存在 Calculation + Interpretation 混合 DTO 的架构边界问题，five_element_imbalance 和 spouse_star_strength 等 Semantic State 字段被混入 Calculation Result。下一步需要审计 cross_result 和 atomic_claims 的来源，以及全仓搜索这两个 Semantic State 字段的消费方。*
