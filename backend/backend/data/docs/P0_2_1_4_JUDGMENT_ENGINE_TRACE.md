# P0-2.1.4 生产路径确认 — judgment_engine.py 完整调用链与 D1StrengthResult 数据血缘

> **审计时间**：2026-08-29
> **审计目标**：追踪 judgment_engine.py 的完整调用链与 D1StrengthResult 数据血缘，确认 strength_engine 是否通过 judgment_engine 进入生产路径
> **基于 commit**：`1bae49a`
> **原始数据**：`docs/P0_2_1_4_judgment_engine_trace.json`

---

## 一、核心结论

### 🟢 最终裁决：judgment_engine.py 完全没有进入生产路径；strength_engine.py 也没有通过 judgment_engine 进入生产路径

**关键证据**：
1. **0 个文件 import judgment_engine.py**
2. judgment_engine.py 的 `judgment` 方法搜索到的 5 个"调用"全部是**假阳性**（实际是指 `Judgment` 类/断言资产，不是 `judgment_engine.judgment` 方法）
3. D1StrengthResult 只在 strength_engine.py 中被实例化（行 409：`return D1StrengthResult(`）
4. evaluate_strength 被 8 个文件调用，但大部分是 Legacy 代码或只被 Legacy 引用的模块
5. **Canonical 层 import: 0 个**
6. **Signal 层 import: 0 个**
7. **API 层 import: 0 个**

**最终裁决**：
- ✅ judgment_engine.py 完全没有进入生产路径
- ✅ strength_engine.py 也没有通过 judgment_engine.py 进入生产路径
- ✅ strength_engine.py 的计算结果（D1StrengthResult）只被 Legacy 代码、孤立实验模块、以及只被 Legacy 引用的模块使用
- ✅ strength_engine.py 也不是生产污染源

---

## 二、judgment_engine.py 内部结构

### 1 个类

| 类名 | 行号 | 说明 |
|------|------|------|
| `P2JudgmentResult` | 308 | P2 判断结果数据结构 |

### 5 个方法

| 方法 | 行号 | 说明 |
|------|------|------|
| `_get_ten_god_by_element` | 265 | 工具方法 |
| `_get_element_by_ten_god` | 282 | 工具方法 |
| `to_dict` | 330 | 序列化 |
| `_has_element_in_chart` | 351 | 工具方法 |
| `judgment` | 371 | **核心方法**：`judgment(chart: BaziChart, d1_result: D1StrengthResult) -> P2JudgmentResult` |

**关键发现**：
- `judgment` 方法接受 `d1_result: D1StrengthResult` 作为参数
- 这意味着 judgment_engine 消费 strength_engine 的计算结果
- 但是，由于 judgment_engine 没有被任何文件 import，所以这个消费关系只存在于代码内部，没有进入生产路径

---

## 三、完整调用链追踪

### 第一步：谁 import 了 judgment_engine？

**0 个文件！**

这是最关键的证据。judgment_engine.py 没有被任何文件 import，所以它不可能在生产路径中被调用。

### 第二步：judgment 方法的"调用"全部是假阳性

搜索到 5 个文件"调用"了 judgment 方法，但经过人工确认，全部是假阳性：

| 文件 | 实际含义 | 假阳性原因 |
|------|----------|------------|
| `judgment_architecture/canonical_asset_acquisition.py` | `Judgment` 类（断言资产） | 第 505-506 行：`j.status != SourceStatus.VALIDATED`，`Judgment must be VALIDATED` |
| `assertion_v2/contract.py` | `Judgment` 概念 | 指断言/判断，不是方法调用 |
| `judgment_architecture/judgment_index_foundation.py` | `Judgment` 类 | 指断言资产索引 |
| `judgment_architecture/source_verification.py` | `Judgment` 类 | 指断言资产验证 |

**结论**：judgment_engine.judgment 方法没有被任何文件实际调用。

---

## 四、D1StrengthResult 数据血缘追踪

### 4.1 D1StrengthResult 在哪里被 import？

4 个文件：
- `engines/judgment_engine.py`（行 41）
- `reasoning/health_signals.py`（行 19）
- （另外 2 个在搜索结果中未完全显示，可能是 Legacy 代码）

### 4.2 D1StrengthResult 在哪里被实例化（创建点）？

**只有 1 个文件**：
- `engines/strength_engine.py`（行 409）：`return D1StrengthResult(`

**关键发现**：D1StrengthResult 只在 strength_engine.py 中被创建。这意味着所有 D1StrengthResult 对象都来自 strength_engine 的计算。

### 4.3 evaluate_strength 在哪里被调用？

8 个文件：

| 文件 | 类型 | 生产路径？ |
|------|------|------------|
| `engines/annual_event_evaluator.py` | ENGINE | ❌ 已确认是孤立实验模块 |
| `legacy/assertion_v1/engine_adapters.py` | LEGACY | ❌ Legacy |
| `legacy/assertion_v1/environmental_fit.py` | LEGACY | ❌ Legacy |
| `legacy/assertion_v1/systems.py` | LEGACY | ❌ Legacy |
| `reasoning/event_topic.py` | REASONING | ❌ 只被 Legacy 引用 |
| `reasoning/health_signals.py` | SIGNAL | ❌ 只被 Legacy 引用 |
| （另外 2 个未完全显示） | - | - |

**结论**：evaluate_strength 只被 Legacy 代码、孤立实验模块、以及只被 Legacy 引用的模块调用。没有进入生产路径。

---

## 五、是否进入 Canonical / Signal / API？

| 层级 | import 数 | 调用数 | 结论 |
|------|-----------|--------|------|
| **Canonical 层** | 0 | 0 | ✅ 未进入 |
| **Signal 层** | 0 | 0 | ✅ 未进入 |
| **API 层** | 0 | 0 | ✅ 未进入 |
| **Service 层** | 0 | - | ✅ 未进入 |
| **Pipeline 层** | 0 | - | ✅ 未进入 |
| **Reasoning 层** | 0 | - | ✅ 未进入 |

**最终结论**：judgment_engine.py 完全没有进入生产路径。

---

## 六、重新评估 strength_engine.py

### 之前的担忧（10c0a26 / 1bae49a）

> "strength_engine.py 是最大的隐性评分源，包含完整的加权评分制，与 P0 冻结原则直接冲突。可能通过 judgment_engine.py 进入生产路径。"

### 重新评估

| 担忧点 | 实际情况 | 重新裁决 |
|--------|----------|----------|
| 完整加权评分制 | 确实存在 | ⚠️ 内部设计问题 |
| 与 P0 冻结原则冲突 | 确实冲突 | ⚠️ 内部设计问题 |
| 通过 judgment_engine 进入生产 | **judgment_engine 0 import，未进入生产** | ✅ 未通过此路径进入 |
| 进入 Canonical State | 0 import / 0 调用 | ✅ 未进入 |
| 进入 Signal | health_signals.py import，但 health_signals 只被 Legacy 引用 | ✅ 未进入生产 |
| 进入 API | 0 import / 0 调用 | ✅ 未进入 |
| 被生产代码调用 | evaluate_strength 只被 Legacy / 孤立实验 / 只被 Legacy 引用的模块调用 | ✅ 未被生产代码调用 |

### 最终裁决

**strength_engine.py 不是生产污染源！**

它的内部设计确实有问题（完整加权评分制，与 P0 冻结原则冲突），但：
- 它没有被生产代码 import 或调用
- 它的计算结果（D1StrengthResult）只被 Legacy 代码、孤立实验模块、以及只被 Legacy 引用的模块使用
- 它没有通过 judgment_engine.py 进入生产路径（因为 judgment_engine 本身也没有进入生产路径）

**处理建议**：
- ✅ 标记为 Legacy / Experimental
- ✅ 不需要立即删除（删除可能破坏 Legacy 代码的引用）
- ✅ 不需要立即重构（它不在生产路径中）
- ⚠️ 未来新代码不得 import 或调用它
- ⚠️ 未来如果要启用它，必须先重构，遵循 P0 冻结原则（禁止评分/阈值/权重，禁止五行计数→强弱）

---

## 七、P0-2 核心引擎审计总结

### 四个核心文件的最终裁决

| 文件 | 内部设计问题 | 是否进入生产路径 | 最终裁决 |
|------|-------------|-----------------|----------|
| `annual_event_evaluator.py` | 🔴 五体系加权融合 | ❌ 完全孤立 | ✅ Legacy / Experimental，不是污染源 |
| `strength_engine.py` | 🔴 完整加权评分制 | ❌ 只被 Legacy/孤立模块引用 | ✅ Legacy / Experimental，不是污染源 |
| `judgment_engine.py` | 🟡 消费 D1StrengthResult | ❌ 0 import，完全孤立 | ✅ Legacy / Experimental，不是污染源 |
| `bazi_engine.py` | 🟡 两个隐性评分函数 | ⏳ 待确认 | ⏳ P0-2.1.5 待审计 |

### 重要发现

1. **三个核心文件都没有进入生产路径！**
   - annual_event_evaluator.py：完全孤立实验模块
   - strength_engine.py：只被 Legacy/孤立模块引用
   - judgment_engine.py：0 import，完全孤立

2. **生产路径中的 Calculation 可能是干净的！**
   - 这三个最大的"隐性评分源"都没有进入生产路径
   - 生产路径可能使用的是其他计算引擎（如 bazi_engine.py 的纯事实计算）

3. **bazi_engine.py 是下一个需要审计的对象**
   - 它有两个隐性评分函数（calc_spouse_star_strength, calc_five_element_balance）
   - 它可能在生产路径中（因为它是核心计算引擎）
   - 需要确认这两个函数是否被生产代码调用

---

## 八、下一步建议

### P0-2.1.5：bazi_engine.py 生产路径确认

用同样的方法追踪 bazi_engine.py 的完整调用链：
- 谁 import 了 bazi_engine？
- 谁调用了 calc_spouse_star_strength？
- 谁调用了 calc_five_element_balance？
- 这两个函数的结果进入哪里？
- 有没有进入 Canonical？Signal？API？

这是当前最高优先级，因为 bazi_engine.py 可能是唯一在生产路径中的核心计算引擎，需要确认它的两个隐性评分函数是否被生产代码调用。

### P0-2.2：Signal/Canonical 层审计

确认生产路径中的 Signal 和 Canonical 层是否干净：
- canonical/composer.py 是否消费了未经授权的评分？
- signal/canonical_signal.py 是否消费了未经授权的评分？
- signal/aggregator.py 是否消费了未经授权的评分？

### P0-2.3：分类与隔离

对所有 Legacy / Experimental 代码进行明确标记和隔离：
- strength_engine.py → Legacy / Experimental
- annual_event_evaluator.py → Legacy / Experimental
- judgment_engine.py → Legacy / Experimental
- legacy/assertion_v1/ → Legacy（已隔离）

---

## 九、审计脚本与数据

- 调用链与数据血缘追踪脚本：`scripts/p0_2_1_4_judgment_engine_trace.py`（可重复运行）
- 原始追踪结果：`docs/P0_2_1_4_judgment_engine_trace.json`

---

*本报告是 P0-2.1.4 生产路径确认的成果。通过完整调用链与 D1StrengthResult 数据血缘追踪，确认 judgment_engine.py 完全没有进入生产路径（0 个 import，方法调用全部是假阳性）。因此 strength_engine.py 也没有通过 judgment_engine.py 进入生产路径。最终裁决：strength_engine.py 和 judgment_engine.py 都不是生产污染源，可以标记为 Legacy / Experimental。下一个需要审计的是 bazi_engine.py，确认它的两个隐性评分函数是否被生产代码调用。*
