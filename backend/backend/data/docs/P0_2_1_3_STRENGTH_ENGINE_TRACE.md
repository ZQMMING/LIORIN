# P0-2.1.3 生产路径确认 — strength_engine.py 完整调用链追踪

> **审计时间**：2026-08-29
> **审计目标**：追踪 strength_engine.py 的完整调用链，确认它是否进入生产路径
> **基于 commit**：`5bb76c6`
> **原始数据**：`docs/P0_2_1_3_strength_engine_trace.json`

---

## 一、核心结论

### 🟡 最终裁决：strength_engine.py 部分进入 Signal 层，但实际生产路径仍需进一步确认

**关键证据**：
1. 7 个文件 import 了 strength_engine
2. 其中 3 个是 Legacy 代码（engine_adapters.py, environmental_fit.py, systems.py）
3. 1 个是已确认的孤立实验模块（annual_event_evaluator.py）
4. 2 个是只被 Legacy 引用的模块（health_signals.py, event_topic.py）
5. 1 个是 judgment_engine.py（import D1StrengthResult，需进一步确认）
6. **Canonical 层 import: 0 个**
7. **Signal 层 import: 1 个（health_signals.py）**
8. **API 层 import: 0 个**
9. **Canonical 层调用: 0 处**
10. **Signal 层调用: 2 处（support_count, drain_count，均在 health_signals.py）**
11. **API 层调用: 0 处**

**初步裁决**：
- ⚠️ strength_engine.py 确实被 health_signals.py import，并且 health_signals.py 调用了 support_count 和 drain_count
- ⚠️ 但 health_signals.py 本身只被 Legacy 代码（flow_year.py）引用，没有进入生产路径
- ⚠️ event_topic.py 也只被 Legacy 代码引用，没有进入生产路径
- ⚠️ judgment_engine.py import D1StrengthResult，需要进一步确认它是否在生产路径中，以及如何使用 D1StrengthResult
- 🟡 初步判断：strength_engine.py 可能没有进入生产路径，但需要进一步审计 judgment_engine.py 确认

---

## 二、strength_engine.py 内部结构

### 1 个类

| 类名 | 行号 | 说明 |
|------|------|------|
| `D1StrengthResult` | 115 | D1 强弱结果数据结构 |

### 1 个核心方法

| 方法 | 行号 | 说明 |
|------|------|------|
| `evaluate_strength` | 217 | 评估日主强弱（包含完整加权评分制） |

**注意**：strength_engine.py 内部包含完整的加权评分制：
- de_ling / de_di / de_shi（得令/得地/得势）
- support_count / drain_count
- de_ling_weight / de_di_weighted
- wang_score / WANG_SCORE_THRESHOLD
- 调候、从强/从弱

这与 P0 冻结原则直接冲突：禁止评分 / 阈值 / 权重，禁止五行计数 → 强弱。

---

## 三、完整调用链追踪

### 第一步：谁 import 了 strength_engine？（7 个文件）

| 文件 | 类型 | import 内容 | 生产路径？ |
|------|------|-------------|------------|
| `engines/annual_event_evaluator.py` | ENGINE | `evaluate_strength` | ❌ 已确认是孤立实验模块 |
| `engines/judgment_engine.py` | ENGINE | `D1StrengthResult` | ⚠️ 需进一步确认 |
| `legacy/assertion_v1/engine_adapters.py` | LEGACY | `evaluate_strength`, `_SUPPORT_ELEMENTS`, `_DRAIN_ELEMENTS` | ❌ Legacy |
| `legacy/assertion_v1/environmental_fit.py` | LEGACY | `evaluate_strength` | ❌ Legacy |
| `legacy/assertion_v1/systems.py` | LEGACY | 多个 | ❌ Legacy |
| `reasoning/event_topic.py` | OTHER | `evaluate_strength`, `_hidden_stems` | ❌ 只被 Legacy 引用 |
| `reasoning/health_signals.py` | SIGNAL | `D1StrengthResult`, `evaluate_strength`, `_hidden_stems` | ❌ 只被 Legacy 引用 |

### 第二步：health_signals.py 和 event_topic.py 是否被生产代码引用？

**搜索结果**：
- `health_signals`：只被 `legacy/assertion_v1/flow_year.py` 引用
- `event_topic`：只被 `legacy/assertion_v1/flow_year.py` 引用，以及在 `matcher.py` 的注释中提到

**结论**：health_signals.py 和 event_topic.py 都只被 Legacy 代码引用，没有进入生产路径。

### 第三步：谁调用了核心方法？

| 方法 | 调用文件数 | 调用文件 | 生产路径？ |
|------|-----------|----------|------------|
| `support_count` | 1 | `reasoning/health_signals.py` | ❌ 只被 Legacy 引用 |
| `drain_count` | 1 | `reasoning/health_signals.py` | ❌ 只被 Legacy 引用 |
| `evaluate_strength` | 0（直接调用） | - | - |

**注意**：`evaluate_strength` 方法没有被直接调用，可能是因为：
1. 它只被 import 但没有被实际调用
2. 或者通过其他方式间接调用（需要进一步确认）

### 第四步：是否进入 Canonical / Signal / API？

| 层级 | import 数 | 调用数 | 结论 |
|------|-----------|--------|------|
| **Canonical 层** | 0 | 0 | ✅ 未进入 |
| **Signal 层** | 1（health_signals.py） | 2（support_count, drain_count） | ⚠️ 部分进入，但 health_signals.py 本身只被 Legacy 引用 |
| **API 层** | 0 | 0 | ✅ 未进入 |
| **Service 层** | 0 | - | ✅ 未进入 |
| **Pipeline 层** | 0 | - | ✅ 未进入 |

---

## 四、需要进一步确认的问题

### 🔴 问题 1：judgment_engine.py 如何使用 D1StrengthResult？

judgment_engine.py import 了 D1StrengthResult，但需要确认：
1. 它是否在生产路径中？
2. 它如何使用 D1StrengthResult？
3. 它是否调用了 evaluate_strength？
4. 它的输出是否进入了 Canonical State / Signal / API？

**这是当前最高优先级的待确认问题。**

### 🟡 问题 2：evaluate_strength 是否被间接调用？

搜索结果显示 evaluate_strength 没有被直接调用，但可能：
1. 通过 D1StrengthResult 的构造函数间接调用
2. 通过其他方式间接调用
3. 或者确实没有被调用

需要进一步确认。

### 🟡 问题 3：health_signals.py 的 support_count / drain_count 如何使用？

health_signals.py 调用了 D1StrengthResult 的 support_count 和 drain_count 属性，需要确认：
1. 这些属性是如何计算的？
2. health_signals.py 如何使用这些属性？
3. 这些属性是否进入了 Signal 输出？

但由于 health_signals.py 本身只被 Legacy 引用，这个问题的优先级较低。

---

## 五、重新评估之前的担忧

### 之前的担忧（10c0a26 报告）

> "strength_engine.py 是最大的隐性评分源，包含完整的加权评分制，与 P0 冻结原则直接冲突。"

### 重新评估

| 担忧点 | 实际情况 | 重新裁决 |
|--------|----------|----------|
| 完整加权评分制 | 确实存在（de_ling, de_di, wang_score 等） | ⚠️ 内部设计问题 |
| 与 P0 冻结原则冲突 | 确实冲突 | ⚠️ 内部设计问题 |
| 进入生产路径 | 可能没有进入（需确认 judgment_engine.py） | 🟡 待确认 |
| 污染 Canonical State | 0 import / 0 调用 | ✅ 未污染 |
| 污染 Signal | 1 import（health_signals.py），但 health_signals.py 只被 Legacy 引用 | 🟡 间接关联，但未进入生产 |
| 污染 API | 0 import / 0 调用 | ✅ 未污染 |

### 初步裁决

**strength_engine.py 可能没有进入生产路径，但需要进一步审计 judgment_engine.py 确认。**

它的内部设计确实有问题（完整加权评分制，与 P0 冻结原则冲突），但如果它没有进入生产路径，那它就不是生产污染源。

**处理建议**：
1. ⚠️ 先审计 judgment_engine.py，确认它是否在生产路径中，以及如何使用 D1StrengthResult
2. ⚠️ 如果 judgment_engine.py 在生产路径中，并且使用了 strength_engine 的计算结果，那 strength_engine.py 就是生产污染源，需要隔离或重构
3. ✅ 如果 judgment_engine.py 不在生产路径中，或者只是 import 了 D1StrengthResult 但没有实际使用，那 strength_engine.py 就不是生产污染源，可以标记为 Legacy / Experimental
4. ✅ 不需要立即删除（删除可能破坏 Legacy 代码的引用）
5. ✅ 不需要立即重构（如果它不在生产路径中）

---

## 六、对 P0-2 整体方向的影响

### 当前优先级

| 优先级 | 文件 | 状态 |
|--------|------|------|
| 🔴 1 | **judgment_engine.py** | 需确认是否在生产路径中，以及如何使用 D1StrengthResult |
| 🟡 2 | **strength_engine.py** | 可能没有进入生产路径，待 judgment_engine.py 确认后裁决 |
| 🟡 3 | **bazi_engine.py** | 两个隐性评分函数，需确认是否进入生产路径 |
| 🟢 4 | ~~annual_event_evaluator.py~~ | ✅ 已确认是孤立实验模块 |

### 下一步建议

**P0-2.1.4：judgment_engine.py 生产路径确认**

用同样的方法追踪 judgment_engine.py 的完整调用链：
- 谁 import 了 judgment_engine？
- 谁调用了它的核心方法？
- 它如何使用 D1StrengthResult？
- 结果进入哪里？
- 有没有进入 Canonical？
- 有没有进入 Signal？
- 有没有进入 API？

这是当前最高优先级，因为 judgment_engine.py 是唯一可能把 strength_engine 的计算结果带入生产路径的文件。

---

## 七、审计脚本与数据

- 调用链追踪脚本：`scripts/p0_2_1_3_strength_engine_trace.py`（可重复运行）
- 原始追踪结果：`docs/P0_2_1_3_strength_engine_trace.json`

---

*本报告是 P0-2.1.3 生产路径确认的成果。通过完整调用链追踪，发现 strength_engine.py 被 7 个文件 import，但其中 3 个是 Legacy 代码，1 个是孤立实验模块，2 个只被 Legacy 引用，1 个是 judgment_engine.py（需进一步确认）。strength_engine.py 没有进入 Canonical 层和 API 层，部分进入 Signal 层（通过 health_signals.py），但 health_signals.py 本身只被 Legacy 引用。初步判断 strength_engine.py 可能没有进入生产路径，但需要进一步审计 judgment_engine.py 确认。*
