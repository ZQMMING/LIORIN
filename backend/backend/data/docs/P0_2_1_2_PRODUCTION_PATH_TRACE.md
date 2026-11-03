# P0-2.1.2 生产路径确认 — annual_event_evaluator.py 完整调用链追踪

> **审计时间**：2026-08-29
> **审计目标**：追踪 annual_event_evaluator.py 的完整调用链，确认它是否进入生产路径
> **基于 commit**：`10c0a26`
> **原始数据**：`docs/P0_2_1_2_production_path_trace.json`

---

## 一、核心结论

### 🟢 最终裁决：annual_event_evaluator.py 是完全孤立的实验/验证模块，不是生产污染源

**关键证据**：
1. 只有 1 个文件 import 了它：`legacy/assertion_v1/flow_year.py`（Legacy 目录）
2. `legacy/assertion_v1/` 整个目录都没有被生产代码 import
3. `evaluate_case` 只在 annual_event_evaluator.py 自己内部调用
4. `combine_signals` 只在 annual_event_evaluator.py 自己内部调用
5. **Canonical 层 import: 0 个**
6. **Signal 层 import: 0 个**
7. **API 层 import: 0 个**
8. **Canonical 层调用: 0 个**
9. **Signal 层调用: 0 个**
10. **API 层调用: 0 个**

**裁决**：
- ✅ 不是生产污染源
- ✅ 不会污染 Canonical State / Signal / API
- ⚠️ 内部设计确实有问题（五体系加权融合），但只影响自身
- 📌 可以标记为 Legacy / Experimental，不需要立即删除

---

## 二、annual_event_evaluator.py 内部结构

### 10 个类

| 类名 | 行号 | 职责 |
|------|------|------|
| `SystemSignal` | 62 | 系统信号数据结构 |
| `AnnualPrediction` | 71 | 年度预测数据结构 |
| `EventResult` | 81 | 事件结果数据结构 |
| `BaziScorer` | 94 | 子平评分器 |
| `HeluoScorer` | 214 | 河洛评分器 |
| `YiScorer` | 273 | 易经评分器 |
| `BlindScorer` | 343 | 盲派评分器 |
| `ZiweiScorer` | 403 | 紫微评分器 |
| `CrossValidationLayer` | 483 | 交叉验证层（五体系加权融合） |
| `AnnualEventEvaluator` | 527 | 年度事件评估器（主入口） |

### 12 个目标方法定义

| 方法 | 行号 | 所属类 | 体系 |
|------|------|--------|------|
| `score_disaster` | 159 | BaziScorer | 子平 |
| `score_wealth` | 180 | BaziScorer | 子平 |
| `score_disaster` | 221 | HeluoScorer | 河洛 |
| `score_wealth` | 231 | HeluoScorer | 河洛 |
| `score_disaster` | 287 | YiScorer | 易经 |
| `score_wealth` | 297 | YiScorer | 易经 |
| `score_disaster` | 358 | BlindScorer | 盲派 |
| `score_wealth` | 371 | BlindScorer | 盲派 |
| `score_disaster` | 444 | ZiweiScorer | 紫微 |
| `score_wealth` | 456 | ZiweiScorer | 紫微 |
| `combine_signals` | 505 | CrossValidationLayer | 五体系融合 |
| `evaluate_case` | 575 | AnnualEventEvaluator | 主评估 |

---

## 三、完整调用链追踪

### 第一步：谁 import 了 annual_event_evaluator？

**只有 1 个文件**：

| 文件 | 类型 | import 内容 |
|------|------|-------------|
| `tongshu/legacy/assertion_v1/flow_year.py` | LEGACY | `HeluoScorer, YiScorer` |

**关键发现**：唯一的 import 方在 Legacy 目录中。

### 第二步：legacy/assertion_v1/ 是否被生产代码 import？

**0 个文件** import 了 `legacy/assertion_v1/`。

**结论**：整个 `legacy/assertion_v1/` 目录是完全孤立的 Legacy 代码，没有被生产路径引用。

### 第三步：谁调用了 evaluate_case？

**只有 annual_event_evaluator.py 自己内部调用**（行 670，2 处）。

```python
result = self.evaluate_case(case, prediction_type)
```

### 第四步：谁调用了 combine_signals？

**只有 annual_event_evaluator.py 自己内部调用**（行 627，2 处）。

```python
d_score, w_score = self.cv.combine_signals(
    bazi_d, blind_d, ziwei_d, heluo_d, yi_d,
    bazi_w, blind_w, ziwei_w, heluo_w, yi_w,
)
```

### 第五步：score_disaster / score_wealth 定义在哪里？

| 文件 | 类型 | 方法数 |
|------|------|--------|
| `annual_event_evaluator.py` | ENGINE | 10 个（5 体系各 2 个）+ combine_signals + evaluate_case |
| `heluo/metrics_v2.py` | ENGINE | 1 个 evaluate_case |

---

## 四、是否进入 Canonical / Signal / API？

| 层级 | import 数 | 调用数 | 结论 |
|------|-----------|--------|------|
| **Canonical 层** | 0 | 0 | ✅ 未进入 |
| **Signal 层** | 0 | 0 | ✅ 未进入 |
| **API 层** | 0 | 0 | ✅ 未进入 |
| **Engine 层** | 1（自身） | 2（自身） | 内部调用 |
| **Legacy 层** | 1 | 0 | 仅 import，未调用核心方法 |

**最终结论**：annual_event_evaluator.py **完全没有进入生产路径**。

---

## 五、重新评估之前的担忧

### 之前的担忧（10c0a26 报告）

> "annual_event_evaluator.py 是最危险的文件，整合五个命理体系评分，通过 combine_signals 加权融合，最终选择分数最高的年份。这是典型的'算→辨→解三层揉成一层'。"

### 重新评估

| 担忧点 | 实际情况 | 重新裁决 |
|--------|----------|----------|
| 五体系加权融合 | 确实存在（combine_signals） | ⚠️ 内部设计问题，但只影响自身 |
| 算→辨→解揉成一层 | 确实存在（结构事实→评分→事件判断） | ⚠️ 内部设计问题，但只影响自身 |
| 进入生产路径 | **完全没有进入** | ✅ 不是生产污染源 |
| 污染 Canonical State | **0 个 import，0 个调用** | ✅ 不会污染 |
| 污染 Signal | **0 个 import，0 个调用** | ✅ 不会污染 |
| 污染 API | **0 个 import，0 个调用** | ✅ 不会污染 |

### 最终裁决

**annual_event_evaluator.py 不是生产污染源，而是一个完全孤立的实验/验证模块。**

它的内部设计确实有问题（五体系加权融合、算→辨→解揉成一层），但这些问题只影响它自身，不会传播到生产路径。

**处理建议**：
1. ✅ 标记为 Legacy / Experimental
2. ✅ 不需要立即删除（删除可能破坏 Legacy 代码的引用）
3. ✅ 不需要立即重构（它不在生产路径中）
4. ⚠️ 未来如果要启用它，必须先重构，遵循"五体系互补，不比较；没有综合评分投票"的总架构原则
5. ⚠️ 未来新代码不得 import 或调用它

---

## 六、对 P0-2 整体方向的影响

### 之前的优先级（10c0a26）

1. 🔴 strength_engine.py（最大隐性评分源）
2. 🔴 annual_event_evaluator.py（最危险，五体系加权融合）
3. 🟡 judgment_engine.py（需数据流审计）
4. 🟡 bazi_engine.py（两个隐性评分函数）

### 重新调整后的优先级

1. 🔴 **strength_engine.py**（最大隐性评分源，需确认是否被生产代码 import）
2. 🟡 **judgment_engine.py**（需数据流审计，确认是否进入生产路径）
3. 🟡 **bazi_engine.py**（两个隐性评分函数，需确认是否进入生产路径）
4. 🟢 **annual_event_evaluator.py**（已确认是孤立实验模块，降级为低优先级）

### 下一步建议

**P0-2.1.3：strength_engine.py 生产路径确认**

用同样的方法追踪 strength_engine.py 的完整调用链：
- 谁 import 了 strength_engine？
- 谁调用了它的核心方法（calc_strength、wang_score 等）？
- 结果进入哪里？
- 有没有进入 Canonical？
- 有没有进入 Signal？
- 有没有进入 API？

这是当前最高优先级，因为 strength_engine.py 是最大的隐性评分源，如果它进入了生产路径，那才是真正的生产污染源。

---

## 七、审计脚本与数据

- 调用链追踪脚本：`scripts/p0_2_1_2_production_path_trace.py`（可重复运行）
- 原始追踪结果：`docs/P0_2_1_2_production_path_trace.json`

---

*本报告是 P0-2.1.2 生产路径确认的成果。通过完整调用链追踪，确认 annual_event_evaluator.py 是完全孤立的实验/验证模块，不是生产污染源。它只被 Legacy 代码引用，完全没有进入 Canonical、Signal、API 层。这一发现重新调整了 P0-2 的优先级：strength_engine.py 成为当前最高优先级，需要确认它是否进入生产路径。*
