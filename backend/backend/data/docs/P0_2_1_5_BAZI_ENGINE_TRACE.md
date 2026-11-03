# P0-2.1.5 生产路径确认 — bazi_engine.py 完整调用链与 Calculation Facts 数据血缘审计

> **审计时间**：2026-08-29
> **审计目标**：追踪 bazi_engine.py 的完整调用链，确认它是否进入生产路径，以及它的 Calculation Facts 如何进入 Canonical State
> **基于 commit**：`af7bf21`
> **原始数据**：`docs/P0_2_1_5_bazi_engine_trace.json`

---

## 一、核心结论

### 🔴 最终裁决：bazi_engine.py 确实进入了生产路径，并且可能把 SEMANTIC_STATE / MIXED 字段混入了 Canonical State

**关键证据**：
1. **24 个文件 import 了 bazi_engine**，包括：
   - Canonical 层：1 个（canonical/composer.py）
   - Signal 层：2 个（health_signals.py, signal_engine.py）
   - API 层：1 个（api/app.py）
   - Pipeline 层：2 个（pipeline.py, compute_stage.py）
2. **BaziChart 被 canonical/composer.py import**，这意味着 BaziChart 的字段可能进入 Canonical State
3. **attach_p2_fields 方法把 16 个字段附加到 BaziChart**，其中包括：
   - `spouse_star_strength`（SEMANTIC_STATE，基于 score → strong/weak/rootless 阈值分类）
   - `five_element_balance` / `five_element_imbalance`（MIXED，五行计数 + 阈值 → imbalance）
   - `kong_wang`（MIXED）
4. **calc_five_element_balance 被 health_signals.py（Signal 层）直接调用**

**初步裁决**：
- 🔴 bazi_engine.py 是唯一进入生产路径的核心计算引擎
- 🔴 attach_p2_fields 可能把未经授权的 SEMANTIC_STATE / MIXED 字段混入了 Canonical State
- ⚠️ 需要进一步审计 canonical/composer.py，确认它是否消费了这些有问题的字段
- ⚠️ 需要进一步审计 health_signals.py，确认它如何使用 calc_five_element_balance 的结果
- ⚠️ 需要确认这些字段是否真正进入了 Canonical State 对象

---

## 二、bazi_engine.py 内部结构

### 3 个类

| 类名 | 行号 | 说明 |
|------|------|------|
| `Pillar` | 146 | 柱数据结构 |
| `BaziChart` | 204 | 八字命局数据结构（frozen=True） |
| `BaziEngine` | 670 | 八字计算引擎 |

### 35 个方法（按输出分类）

| 分类 | 数量 | 说明 |
|------|------|------|
| **CALCULATION_FACT** | 19 | 纯事实计算（四柱、藏干、十神、合冲刑害破、十二长生、大运等） |
| **MIXED** | 2 | 混合了 Calculation Fact 和 Semantic State |
| **SEMANTIC_STATE** | 1 | 明确的 Semantic State / 辨 |
| **UNKNOWN** | 13 | 无法自动分类，需要人工审计 |

### 有问题的方法

| 方法 | 行号 | 分类 | 问题 |
|------|------|------|------|
| `calc_spouse_star_strength` | 446 | SEMANTIC_STATE | score → strong/weak/rootless 阈值分类，未经原典授权 |
| `calc_kong_wang` | 562 | MIXED | 空亡计算是 Fact，但"力量减半"是 Semantic（已移除注释） |
| `calc_five_element_balance` | 576 | MIXED | 五行计数是 Fact，但 imbalance 判断基于阈值，是 Semantic |

---

## 三、完整调用链追踪

### 第一步：谁 import 了 bazi_engine？（24 个文件）

| 层级 | 文件数 | 关键文件 |
|------|--------|----------|
| **API** | 1 | `api/app.py` |
| **CANONICAL** | 1 | `canonical/composer.py` ⚠️ |
| **ENGINE** | 9 | annual_event_evaluator, bazi_adapter, blind_bazi_engine, blind_yingqi, judgment_engine, strength_engine, ziwei_engine, __init__, legacy/engine_adapters |
| **JUDGMENT_ARCH** | 1 | judgment_index_foundation.py |
| **LEGACY** | 3 | environmental_fit, flow_year, systems |
| **OTHER** | 1 | types.py |
| **PIPELINE** | 2 | `pipeline.py`, `compute_stage.py` ⚠️ |
| **REASONING** | 3 | bazi_ten_gods, context_assembler, event_topic |
| **SIGNAL** | 2 | `health_signals.py` ⚠️, signal_engine.py |
| **VALIDATION** | 1 | end_to_end.py |

**关键发现**：bazi_engine.py 确实进入了生产路径！它被 Canonical、Signal、API、Pipeline 层都 import 了。

### 第二步：calc_spouse_star_strength 调用链

| 文件 | 层级 | 调用位置 |
|------|------|----------|
| `bazi_engine.py` | ENGINE | 行 604：在 `attach_p2_fields` 中调用 |

**关键发现**：calc_spouse_star_strength 只在 bazi_engine.py 自己的 attach_p2_fields 中被调用，结果被附加到 BaziChart 对象上。

### 第三步：calc_five_element_balance 调用链

| 文件 | 层级 | 调用位置 |
|------|------|----------|
| `bazi_engine.py` | ENGINE | 行 615：在 `attach_p2_fields` 中调用 |
| `health_signals.py` | SIGNAL | 行 100：直接调用 ⚠️ |

**关键发现**：calc_five_element_balance 被 health_signals.py（Signal 层）直接调用！这意味着这个 MIXED 方法的结果直接进入了 Signal 层。

### 第四步：attach_p2_fields 方法分析

`attach_p2_fields` 方法（行 589-635）计算并附加了 16 个字段到 BaziChart：

| 字段 | 分类 | 说明 |
|------|------|------|
| spouse_star | UNKNOWN | 配偶星 |
| spouse_star_attack | UNKNOWN | 配偶星攻击 |
| officer_mixed | UNKNOWN | 官杀混杂 |
| day_branch_clash | CALCULATION_FACT | 日支冲 |
| day_branch_harm | CALCULATION_FACT | 日支害 |
| **spouse_star_strength** | **SEMANTIC_STATE** | **配偶星强度（score → strong/weak/rootless）** ⚠️ |
| peach_blossom | UNKNOWN | 桃花 |
| branch_clash_map | CALCULATION_FACT | 六冲表 |
| branch_harm_map | CALCULATION_FACT | 六害表 |
| branch_he_map | CALCULATION_FACT | 六合表 |
| branch_sanhe_map | CALCULATION_FACT | 三合表 |
| branch_sanxing_map | CALCULATION_FACT | 三刑表 |
| **kong_wang** | **MIXED** | **空亡** ⚠️ |
| **five_element_balance** | **MIXED** | **五行平衡** ⚠️ |
| **five_element_imbalance** | **MIXED** | **五行失衡（基于阈值）** ⚠️ |
| day_branch_main_ten_god | CALCULATION_FACT | 日支主气十神 |

**关键发现**：
- 3 个有问题的字段（spouse_star_strength, kong_wang, five_element_balance/imbalance）被附加到 BaziChart 对象上
- BaziChart 被 canonical/composer.py（Canonical 层）import
- 这意味着这些 SEMANTIC_STATE / MIXED 字段可能进入了 Canonical State！

---

## 四、需要进一步审计的问题

### 🔴 问题 1：canonical/composer.py 是否消费了有问题的字段？

需要确认：
- canonical/composer.py 如何使用 BaziChart？
- 它是否消费了 spouse_star_strength、five_element_balance、five_element_imbalance、kong_wang 等字段？
- 这些字段是否进入了 Canonical State 对象？

**这是当前最高优先级的待确认问题。**

### 🟡 问题 2：health_signals.py 如何使用 calc_five_element_balance 的结果？

需要确认：
- health_signals.py 如何使用 calc_five_element_balance 的返回值？
- 它是否把 imbalance 标志直接作为 Signal 输出？
- health_signals.py 本身是否在生产路径中？（之前确认它只被 Legacy 引用，但需要再次确认）

### 🟡 问题 3：BaziChart 的哪些字段真正进入了 Canonical State？

需要确认：
- Canonical State 对象的完整字段列表
- 哪些字段来自 BaziChart 的 attach_p2_fields
- 哪些字段是纯 Calculation Fact
- 哪些字段是 SEMANTIC_STATE / MIXED

### 🟡 问题 4：13 个 UNKNOWN 方法的人工审计

需要人工审计 13 个无法自动分类的方法，确认它们的输出属于 Calculation Fact 还是 Semantic State。

---

## 五、P0-2 核心引擎审计最终总结

### 四个核心文件的最终裁决

| 文件 | 内部设计问题 | 是否进入生产路径 | 最终裁决 |
|------|-------------|-----------------|----------|
| `annual_event_evaluator.py` | 🔴 五体系加权融合 | ❌ 完全孤立 | ✅ Legacy / Experimental，不是污染源 |
| `strength_engine.py` | 🔴 完整加权评分制 | ❌ 只被 Legacy/孤立模块引用 | ✅ Legacy / Experimental，不是污染源 |
| `judgment_engine.py` | 🟡 消费 D1StrengthResult | ❌ 0 import，完全孤立 | ✅ Legacy / Experimental，不是污染源 |
| `bazi_engine.py` | 🟡 1 个 SEMANTIC_STATE + 2 个 MIXED | 🔴 **确实进入生产路径** | 🔴 **需要进一步审计，可能把 Semantic 混入 Canonical** |

### 重要发现

1. **三个最大的"隐性评分源"都没有进入生产路径**
   - annual_event_evaluator.py：完全孤立实验模块
   - strength_engine.py：只被 Legacy/孤立模块引用
   - judgment_engine.py：0 import，完全孤立

2. **bazi_engine.py 是唯一进入生产路径的核心计算引擎**
   - 它被 Canonical、Signal、API、Pipeline 层都 import 了
   - 它的 attach_p2_fields 方法可能把未经授权的 Semantic State 混入了 Canonical State

3. **生产路径中的 Calculation 可能基本干净，但需要确认边界**
   - bazi_engine.py 的 19 个 CALCULATION_FACT 方法是干净的
   - 但 1 个 SEMANTIC_STATE + 2 个 MIXED 方法可能越界
   - 需要确认这些有问题的字段是否真正进入了 Canonical State

---

## 六、下一步建议

### P0-2.1.6：canonical/composer.py 与 Canonical State 边界审计（最高优先级）

目标：确认 Canonical State 的完整字段列表，以及哪些字段来自 BaziChart 的 attach_p2_fields。

需要回答：
1. Canonical State 对象有哪些字段？
2. 哪些字段来自 BaziChart？
3. spouse_star_strength、five_element_balance、five_element_imbalance、kong_wang 是否进入了 Canonical State？
4. 如果进入了，它们是作为 Fact 还是作为 Semantic State？
5. Canonical State 是否有明确的 Fact vs Semantic 边界？

### P0-2.1.7：health_signals.py 与 Signal 层边界审计

目标：确认 health_signals.py 如何使用 calc_five_element_balance 的结果，以及 Signal 层是否消费了未经授权的 Semantic State。

### P0-2.2：Signal/Canonical 层完整审计

确认生产路径中的 Signal 和 Canonical 层是否干净：
- canonical/composer.py 是否消费了未经授权的评分？
- signal/canonical_signal.py 是否消费了未经授权的评分？
- signal/aggregator.py 是否消费了未经授权的评分？

### P0-2.3：分类与隔离

对所有 Legacy / Experimental 代码进行明确标记和隔离，并对 bazi_engine.py 中有问题的字段进行边界确认或隔离。

---

## 七、审计脚本与数据

- 调用链与数据血缘审计脚本：`scripts/p0_2_1_5_bazi_engine_trace.py`（可重复运行）
- 原始审计结果：`docs/P0_2_1_5_bazi_engine_trace.json`

---

*本报告是 P0-2.1.5 生产路径确认的成果。通过完整调用链与 Calculation Facts 数据血缘审计，确认 bazi_engine.py 确实进入了生产路径（被 Canonical、Signal、API、Pipeline 层 import），并且它的 attach_p2_fields 方法可能把未经授权的 SEMANTIC_STATE / MIXED 字段（spouse_star_strength, five_element_balance/imbalance, kong_wang）混入了 Canonical State。这是当前最高优先级的待确认问题。下一步需要审计 canonical/composer.py 与 Canonical State 的边界，确认这些有问题的字段是否真正进入了 Canonical State。*
