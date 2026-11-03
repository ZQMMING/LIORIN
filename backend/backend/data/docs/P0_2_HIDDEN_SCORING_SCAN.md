# P0-2 全仓隐性评分扫描 — 初步报告

> **审计时间**：2026-08-29
> **审计范围**：src 目录全部 262 个 Python 文件
> **审计原则**：只扫描，不重构。目标是发现所有未经授权的 score/weight/threshold/strength/balance 路径。
> **基于 commit**：`4483b8f`
> **原始数据**：`docs/P0_2_hidden_scoring_scan_raw.json`

---

## 一、扫描结果总览

| 指标 | 数值 |
|------|------|
| 扫描 Python 文件总数 | 262 |
| 有潜在问题的文件数 | 104 |
| 潜在问题总数 | **1325** |

### 按问题类别统计

| 类别 | 数量 | 说明 |
|------|------|------|
| **score** | 494 | 评分、得分、打分 |
| **strength** | 329 | 强弱、身强身弱、strength |
| **threshold** | 149 | 阈值、临界值、>= / <= |
| **weight** | 140 | 权重、加权、weighted |
| **strong_weak** | 112 | STRONG/WEAK 常量、身强身弱 |
| **balance** | 101 | 五行平衡、imbalance |

---

## 二、高优先级文件（核心子平计算与判断层）

### 🔴 最高优先级（直接影响 Canonical State）

| 文件 | 问题数 | 主要问题 | 状态 |
|------|--------|----------|------|
| `engines/strength_engine.py` | 169 | strength 82, weight 44, score 23, threshold 10 | 🔴 已标记为 Legacy Reference，需隔离 |
| `engines/annual_event_evaluator.py` | 93 | score 70, strength 9, strong_weak 6, threshold 4 | 🔴 流年事件评估器，大量评分 |
| `engines/judgment_engine.py` | 40 | strength 19, strong_weak 16, threshold 5 | 🔴 判断引擎，直接输出强弱 |
| `engines/bazi_engine.py` | 29 | balance 10, strong_weak 8, strength 5, score 4 | 🟡 核心计算引擎，含 five_element_balance |
| `engines/blind_bazi_engine.py` | 32 | strength 22, threshold 7, strong_weak 2 | 🟡 盲派引擎，重复实现 |
| `engines/blind_yingqi.py` | 10 | strength 10 | 🟡 盲派应期 |

### 🟡 中优先级（Signal / Canonical / Reasoning 层）

| 文件 | 问题数 | 主要问题 |
|------|--------|----------|
| `reasoning/event_topic.py` | 56 | score 39, strength 6, strong_weak 6, balance 4 |
| `reasoning/health_signals.py` | 43 | balance 19, strength 12, strong_weak 4, score 6 |
| `reasoning/context_assembler.py` | 12 | strength 7, threshold 1, strong_weak 2, score 2 |
| `reasoning/signal_engine.py` | 15 | threshold 5, balance 8, strength 2 |
| `signal/canonical_signal.py` | 12 | strength 11, threshold 1 |
| `signal/adapters/__init__.py` | 19 | strength 19 |
| `signal/aggregator.py` | 6 | score 2, strength 4 |
| `canonical/composer.py` | 1 | strength 1 |

### 🟢 低优先级（其他命理体系 / Legacy / 验证）

| 类别 | 文件数 | 说明 |
|------|--------|------|
| 河洛（heluo/） | ~10 | metrics_v2 73, interpretation 34, metrics 38 等，河洛自有体系 |
| 紫微（ziwei/） | ~5 | ziwei_engine 34, 主要是 score 30，紫微自有评分 |
| Legacy（legacy/） | ~8 | assertion_v1 旧代码，已标记 Legacy |
| 验证/测试（validation/, v_validation/） | ~15 | 验证评分、测试阈值，不是命理判断 |
| 审计验证（audit_validation/） | ~3 | 验证器阈值，不是命理判断 |
| 其他（admin, db, render, services 等） | ~20 | 管理、数据库、渲染、服务层 |

---

## 三、核心发现

### 发现 1：strength_engine.py 是最大的隐性评分源

`strength_engine.py` 有 169 个问题，包括：
- de_ling / de_di / de_shi（得令/得地/得势）
- support_count / drain_count
- de_ling_weight / de_di_weighted
- wang_score / WANG_SCORE_THRESHOLD
- 调候、从强/从弱

这与 P0 冻结原则直接冲突：
- ❌ 禁止评分 / 阈值 / 权重
- ❌ 禁止五行计数 → 强弱
- ❌ 禁止长生数量 → score

**裁决**：strength_engine.py 应严格隔离为 Legacy Reference，不得作为生产路径输入。旧评分结果只能用于差异审计，不能作为新系统 ground truth。

### 发现 2：bazi_engine.py 仍有隐性评分

`bazi_engine.py` 有 29 个问题，包括：
- `calc_spouse_star_strength`：score → strong/weak/rootless（阈值分类）
- `calc_five_element_balance`：五行计数 + 阈值 → imbalance

这是典型的：
- 数值评分 → 阈值 → 语义状态

**裁决**：这些函数需要标记为 Legacy 或待审计，不能直接进入 Canonical State。

### 发现 3：annual_event_evaluator.py 有大量评分

`annual_event_evaluator.py` 有 93 个问题，其中 score 70 处。

这是流年事件评估器，可能包含大量未经授权的评分逻辑。

**裁决**：需要单独审计，确认哪些是 L1 Fact，哪些是未经授权的 Semantic Judgment。

### 发现 4：judgment_engine.py 直接输出强弱

`judgment_engine.py` 有 40 个问题，其中 strength 19 处，strong_weak 16 处。

这是判断引擎，直接输出身强/身弱判断。

**裁决**：需要确认这些判断是否经过原典授权，还是基于未经授权的评分算法。

### 发现 5：Legacy 目录仍有大量旧代码

`legacy/assertion_v1/` 目录有多个文件，包含大量 weight、score、threshold。

这些是旧版断言引擎，已经标记为 Legacy，但仍然在代码库中。

**裁决**：Legacy 代码应明确隔离，不得被新系统 import 或调用。

---

## 四、误报说明

本次扫描是关键词匹配，可能包含以下误报：

1. **验证/测试文件中的 threshold**：验证器的阈值不是命理判断阈值
2. **Legacy 代码**：已经标记为 Legacy 的旧代码
3. **其他命理体系**：河洛、紫微自有评分体系，不属于子平 Canonical State
4. **注释/文档中的关键词**：注释中提到的 score/strength 不一定是实际计算
5. **数据结构定义中的字段名**：如 `strength` 字段可能只是数据结构，不是计算逻辑

**后续动作**：需要逐项人工审核，区分真正的隐性评分与误报。

---

## 五、下一步建议

### P0-2.1 核心引擎深度审计（高优先级）
- [ ] strength_engine.py：确认 Legacy 隔离状态，检查是否有新系统 import
- [ ] bazi_engine.py：审计 calc_spouse_star_strength、calc_five_element_balance
- [ ] judgment_engine.py：审计强弱判断逻辑是否经过原典授权
- [ ] annual_event_evaluator.py：审计 70 处 score 的来源和授权状态

### P0-2.2 Signal/Canonical 层审计（中优先级）
- [ ] signal/canonical_signal.py：11 处 strength
- [ ] signal/adapters/__init__.py：19 处 strength
- [ ] reasoning/signal_engine.py：8 处 balance
- [ ] canonical/composer.py：1 处 strength

### P0-2.3 分类与隔离（低优先级）
- [ ] Legacy 代码明确隔离，禁止新系统 import
- [ ] 河洛、紫微体系标记为独立体系，不进入子平 Canonical State
- [ ] 验证/测试文件排除出命理判断审计范围

### P0-3 Boundary Cases（待 P0-2 完成后）
- [ ] 子初前/子初后
- [ ] 节气前/节气后
- [ ] 立春前/立春后
- [ ] 真太阳时跨时辰
- [ ] 时区跨日
- [ ] 农历闰月
- [ ] 年柱/月柱/日柱切换
- [ ] 大运交界

---

## 六、审计脚本与数据

- 扫描脚本：`scripts/p0_2_hidden_scoring_scan.py`（可重复运行）
- 原始扫描结果：`docs/P0_2_hidden_scoring_scan_raw.json`（104 个文件，1325 处潜在问题）

---

*本报告是 P0-2 全仓隐性评分扫描的初步成果。扫描发现全仓有超过 1300 处潜在隐性评分路径，其中核心子平计算与判断层（strength_engine、bazi_engine、judgment_engine、annual_event_evaluator）是最高优先级。需要逐项人工审核，区分真正的隐性评分与误报，并对未经授权的评分路径进行隔离或移除。*
