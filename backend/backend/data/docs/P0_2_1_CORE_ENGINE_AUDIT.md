# P0-2.1 核心引擎深度审计 — 初步报告

> **审计时间**：2026-08-29
> **审计范围**：四个核心引擎文件
> **审计原则**：不是消灭 score，而是证明生产 Calculation Path 中不存在未经授权的"评分 → 阈值 → 语义状态"链。
> **基于 commit**：`76a7578`
> **原始数据**：`docs/P0_2_1_core_engine_audit_raw.json`

---

## 一、审计范围与结果总览

### 四个核心文件

| 文件 | 问题数 | 主要问题 |
|------|--------|----------|
| `strength_engine.py` | 105 | weight 50, score 23, threshold 21, strength 11 |
| `annual_event_evaluator.py` | 87 | score 68, strength 10, threshold 5, weight 4 |
| `judgment_engine.py` | 33 | strength 18, threshold 15 |
| `bazi_engine.py` | 23 | balance 9, strength 6, threshold 6, score 2 |
| **总计** | **248** | |

### 按初步分类统计（自动初判，需人工复核）

| 分类 | 数量 | 说明 |
|------|------|------|
| **NEEDS_MANUAL_REVIEW** | **130** | 需要人工逐项归因 |
| LIKELY_COMMENT | 75 | 可能是注释/文档 |
| LIKELY_LEGACY | 27 | 可能是 Legacy 代码 |
| LIKELY_FIELD_DEFINITION | 11 | 可能是字段定义/数据结构 |
| LIKELY_SORTING | 5 | 可能是排序/优先级 |

---

## 二、逐文件深度分析

### 🔴 文件 1：strength_engine.py（105 处）

**核心问题**：完整的加权评分制，直接与 P0 冻结原则冲突。

**关键结构**：
- `de_ling` / `de_di` / `de_shi`（得令/得地/得势）
- `support_count` / `drain_count`
- `de_ling_weight` / `de_di_weighted`
- `wang_score` / `WANG_SCORE_THRESHOLD`
- 调候、从强/从弱

**计算链**：
```
五行计数
  ↓
加权（de_ling_weight / de_di_weighted）
  ↓
wang_score
  ↓
WANG_SCORE_THRESHOLD（>= 2.0）
  ↓
身强 / 身弱
```

**裁决**：
- ✅ 已标记为 Legacy Reference
- ❌ 不得作为生产路径输入
- ❌ 旧评分结果只能用于差异审计，不能作为新系统 ground truth
- ⚠️ 需要确认是否有新系统 import 此文件

**初步分类**：
- LIKELY_LEGACY: 27 处（文件整体已标记 Legacy）
- LIKELY_COMMENT: 22 处（注释中提到评分）
- NEEDS_MANUAL_REVIEW: 56 处（实际计算逻辑）

---

### 🔴 文件 2：annual_event_evaluator.py（87 处，最危险）

**核心问题**：整合五个命理体系评分，通过加权融合输出事件判断。这是"算→辨→解三层揉成一层"的典型。

**关键结构**：
- `score_disaster`（灾劫评分）
- `score_wealth`（财运评分）
- 五个体系各自的评分函数：
  - 子平：`bazi.score_disaster` / `bazi.score_wealth`
  - 盲派：`blind.score_disaster` / `blind.score_wealth`
  - 紫微：`ziwei.score_disaster` / `ziwei.score_wealth`
  - 河洛：`heluo.score_disaster` / `heluo.score_wealth`
  - 易经：`yi.score_disaster` / `yi.score_wealth`
- `combine_signals`（五体系加权融合）
- `evaluate_case`（选择分数最高的年份作为预测结果）

**计算链**：
```
结构事实（四柱、流年）
  ↓
五体系各自评分（score_disaster / score_wealth）
  ↓
combine_signals（加权融合）
  ↓
排序（max(scores)）
  ↓
事件判断（预测年份）
```

**关键发现**：
- 第 605 行注释："子平评分 (V2.5: 传入旺衰verdict, 十神吉凶动态判断)"
- 第 626 行注释："交叉验证 (V4: 五体系加权)"
- 第 642 行：`predicted = max(scores, key=scores.get)` — 直接用分数最高的年份作为预测

**需要人工审核的关键问题**：
1. 这个文件是生产路径还是测试/验证文件？
   - 从 `evaluate_case` 函数看，它有 `actual` 答案和 `correct` 判断，看起来是测试/验证
   - 但它直接调用了 `cv.bazi.score_disaster`，这些函数可能在生产路径中
2. `combine_signals` 的加权规则是什么？是否经过原典授权？
3. 五个体系的评分规则是否经过原典授权？
4. 这个文件的输出是否进入了 Canonical State / Signal？

**初步分类**：
- LIKELY_COMMENT: 24 处（注释中提到评分）
- LIKELY_SORTING: 4 处（max 排序）
- LIKELY_FIELD_DEFINITION: 3 处（字段定义）
- NEEDS_MANUAL_REVIEW: 56 处（实际评分计算逻辑）

---

### 🟡 文件 3：judgment_engine.py（33 处）

**核心问题**：判断引擎直接输出强弱判断，需要做数据流审计。

**关键问题**：
- 它的判断规则有没有经过授权？
- 输入是不是 Canonical Fact？
- 有没有偷偷依赖旧 strength score？

**需要人工审核的关键问题**：
1. `strength` 相关的 18 处：是字段定义还是计算逻辑？
2. `threshold` 相关的 15 处：是判断阈值还是测试阈值？
3. 这个引擎的输入来源是什么？是否直接调用了 strength_engine.py？
4. 输出是否进入了 Canonical State / Signal？

**初步分类**：
- LIKELY_COMMENT: 9 处
- LIKELY_FIELD_DEFINITION: 1 处
- NEEDS_MANUAL_REVIEW: 23 处

---

### 🟡 文件 4：bazi_engine.py（23 处）

**核心问题**：核心计算引擎仍有隐性评分函数。

**关键函数**：
1. `calc_spouse_star_strength`：
   - score → strong / weak / rootless
   - 典型的"数值评分 → 阈值 → 语义状态"
   - 阈值：>= 1.0 → strong, >= 0.3 → weak, else → rootless

2. `calc_five_element_balance`：
   - 五行计数 + 阈值 → imbalance
   - 阈值：max > 0.40 或 min < 0.05 → imbalance

**裁决**：
- 这些函数需要标记为 Legacy 或待审计
- 不能直接进入 Canonical State
- `calc_five_element_balance` 的五行计数本身是 L1 Fact，但 `imbalance` 判断是未经授权的 Semantic Judgment

**初步分类**：
- LIKELY_SORTING: 1 处
- LIKELY_COMMENT: 1 处
- NEEDS_MANUAL_REVIEW: 21 处

---

## 三、核心发现

### 发现 1：annual_event_evaluator.py 是最危险的文件

它整合了五个命理体系的评分，通过加权融合输出事件判断。这是"算→辨→解三层揉成一层"的典型。

**关键问题**：
- 五体系加权规则（combine_signals）是否经过原典授权？
- 五个体系的评分规则是否经过原典授权？
- 这个文件是生产路径还是测试/验证文件？
- 输出是否进入了 Canonical State / Signal？

### 发现 2：strength_engine.py 是最大的隐性评分源

完整的加权评分制，直接与 P0 冻结原则冲突。已标记为 Legacy Reference，但需要确认是否有新系统 import。

### 发现 3：bazi_engine.py 仍有两个隐性评分函数

- `calc_spouse_star_strength`：score → strong/weak/rootless
- `calc_five_element_balance`：五行计数 + 阈值 → imbalance

需要标记为 Legacy 或待审计，不能直接进入 Canonical State。

### 发现 4：judgment_engine.py 需要数据流审计

判断引擎直接输出强弱判断，需要确认：
- 判断规则有没有经过授权？
- 输入是不是 Canonical Fact？
- 有没有偷偷依赖旧 strength score？

---

## 四、误报说明

本次深度审计仍有自动初判，可能包含以下误报：

1. **LIKELY_COMMENT（75 处）**：注释/文档中提到的 score/strength，不一定是实际计算
2. **LIKELY_LEGACY（27 处）**：已标记为 Legacy 的代码，不一定在生产路径中
3. **LIKELY_FIELD_DEFINITION（11 处）**：字段叫 strength ≠ 存在非法评分，可能只是 Schema 字段
4. **LIKELY_SORTING（5 处）**：排序/优先级用的 score，不一定是命理判断
5. **测试/验证代码**：annual_event_evaluator.py 可能是测试/验证文件，不一定在生产路径中

**后续动作**：需要逐项人工审核，区分真正的未经授权评分路径与误报。

---

## 五、下一步建议

### P0-2.1.1 人工逐项归因（高优先级）
- [ ] strength_engine.py：确认是否有新系统 import，确认 Legacy 隔离状态
- [ ] annual_event_evaluator.py：确认是生产路径还是测试/验证文件，审计 combine_signals 加权规则
- [ ] judgment_engine.py：数据流审计，确认输入来源和判断规则授权状态
- [ ] bazi_engine.py：审计 calc_spouse_star_strength、calc_five_element_balance，标记 Legacy 或待审计

### P0-2.1.2 生产路径确认（高优先级）
- [ ] 确认哪些文件在生产路径中被调用
- [ ] 确认 Canonical State / Signal 的数据来源
- [ ] 确认是否有未经授权的评分进入 Canonical State / Signal

### P0-2.2 Signal/Canonical 层审计（中优先级）
- [ ] signal/canonical_signal.py：11 处 strength
- [ ] signal/adapters/__init__.py：19 处 strength
- [ ] reasoning/signal_engine.py：8 处 balance
- [ ] canonical/composer.py：1 处 strength

### P0-2.3 分类与隔离（低优先级）
- [ ] Legacy 代码明确隔离，禁止新系统 import
- [ ] 河洛、紫微体系标记为独立体系，不进入子平 Canonical State
- [ ] 验证/测试文件排除出命理判断审计范围

---

## 六、审计脚本与数据

- 深度审计脚本：`scripts/p0_2_1_core_engine_audit.py`（可重复运行）
- 原始审计结果：`docs/P0_2_1_core_engine_audit_raw.json`（4 个文件，248 处，含上下文）

---

*本报告是 P0-2.1 核心引擎深度审计的初步成果。对四个核心文件进行了深度扫描，发现 248 处潜在问题，其中 130 处需要人工逐项归因。最危险的文件是 annual_event_evaluator.py（整合五体系评分加权融合），最大的隐性评分源是 strength_engine.py（已标记 Legacy）。需要进一步人工审核，区分真正的未经授权评分路径与误报，并确认生产路径中是否存在未经授权的"评分→阈值→语义状态"链。*
