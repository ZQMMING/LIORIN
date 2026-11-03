# P0 执行约束 — 先审计，再重构

> **文档性质**：执行层面的硬约束，高于架构裁决结果
> **创建时间**：2026-08-29
> **基于 commit**：`168b2a4`
> **关联文档**：`docs/ARCHITECTURE_DECISION_RESULT.md`

---

## 核心硬约束

> **任何"算"或"辨"没有通过独立验证，都不能因为架构已经裁决，就直接进入实现和生产。**

`docs/ARCHITECTURE_DECISION_RESULT.md` 是当前有效的**架构裁决基线**，但它只回答了"方向是什么"，没有回答"计算事实是否正确"。

**架构裁决通过 ≠ 计算正确性已证明 ≠ 可以开始写 canonical_state_engine.py**

---

## 优先级排序

```
算准  ← 第一优先级
辨准  ← 第二优先级
解准  ← 暂后
```

当前阶段：
- **算准**：第一优先级，必须先完成独立验证
- **辨准**：第二优先级，建立在算准的基础上
- **解准**：暂后，等算和辨都 FREEZE 后再恢复

---

## 正确执行顺序

### P0-1 Calculation Source Reconciliation（当前）
逐项审：
- 四柱、日主、十神
- 十二长生、藏干
- 冲、合、刑、害、三合、三刑、空亡

三套数据源逐项 diff：
- `bazi_l1_facts.py`
- `reasoning/bazi_ten_gods.py`
- `reasoning/bazi_fixed_tables.py`

建立：`SOURCE_DIFF_REPORT`

**产出**：差异分类、原典验证、Canonical Registry 候选

---

### P0-2 Calculation Integrity Audit
全仓扫描隐性评分路径：
- `score` / `weight` / `threshold`
- `strong` / `weak` / `strength`
- `balance` / `imbalance`

逐项判断：
- 这是 L1 Fact？
- Relationship？
- 还是未经授权的 Semantic Judgment？

**已确认问题**（commit `168b2a4`）：
1. `strength_engine.py`：完整加权评分系统
2. `bazi_engine.py::calc_spouse_star_strength`：score → strong/weak/rootless
3. `bazi_engine.py::calc_five_element_balance`：五行计数 + 阈值 → imbalance

**产出**：完整的隐性评分路径清单 + 分类

---

### P0-3 Boundary Cases
建立边界测试案例：
- 子初前 / 子初后
- 节气前 / 节气后
- 立春前 / 立春后
- 真太阳时跨时辰
- 时区跨日
- DST
- 农历闰月
- 年柱切换、月柱切换、日柱切换
- 大运交界

**产出**：Boundary Cases 测试集

---

### P0-4 CALCULATION_GOLDEN_DATASET
扩展 Golden Dataset：
- 1983 案例只能作为一个 reference，不能叫"Calculation Correctness 已证明"
- 至少覆盖：
  - 阴阳日主
  - 四季
  - 四土月
  - 节气边界
  - 子初
  - 真太阳时边界
  - 农历/公历
  - 藏干完整组合
  - 合冲刑害
  - 多种日主
  - 强弱存在争议的案例
  - 应该得到 UNRESOLVED 的案例

**产出**：完整的 CALCULATION_GOLDEN_DATASET

---

### P0-5 State / Signal Integrity Audit
验证：
- Canonical State 是否独立、封闭、可验证
- Signal 是否只从 Canonical State 提取语义，不创造 Canonical State
- Signal Engine 是否重新计算命理事实（禁止）
- 3 套 Signal Engine 的职责边界

**产出**：State / Signal 完整性审计报告

---

### CALCULATION + STATE FREEZE
以上全部通过后：
- 计算层 FREEZE
- 状态层 FREEZE
- 才允许进入下一步

---

### 才允许 Canonical State → Signal → Assertion
CALCULATION + STATE FREEZE 后：
- 才允许创建 `canonical_state_engine.py`
- 才允许接 Signal
- 才允许接 Assertion

---

### 最后才恢复 P6.5-C
断言批量生产必须等算和辨都 FREEZE 后才能恢复。

---

## 禁止事项

### ❌ 禁止直接进入实现
- 不能因为 `ARCHITECTURE_DECISION_RESULT.md` 裁决了方向，就直接去写 `canonical_state_engine.py`
- 不能跳过 Source Reconciliation 直接假设数据源一致
- 不能跳过 Integrity Audit 直接假设计算正确

### ❌ 禁止用旧评分结果当 ground truth
- `strength_engine.py` 的 `wang_score` 不能作为新系统的验证标准
- `calc_spouse_star_strength` 的 strong/weak/rootless 不能作为新系统的 ground truth
- 旧评分结果只能用于差异审计（Differential Audit），不能用于正确性验证

### ❌ 禁止 fallback 到旧算法
- 新 Canonical State 引擎中，无法确定的状态必须标记为 `UNRESOLVED`
- 不能因为 Canonical State 不确定，就调用旧评分引擎得到强/弱
- 这种 fallback 必须禁止

### ❌ 禁止新旧系统并行生产
- Legacy 系统只能用于 Regression / Differential Audit
- Legacy 不能参与授权、投票、融合、fallback
- 不能同时有两套系统产生生产结果

---

## 中医类比

这个顺序符合中医的"先辨证后论治"：

```
辨证（算准 + 辨准）
    ↓
确认病机（CALCULATION + STATE FREEZE）
    ↓
论治（解准）
    ↓
处方（Assertion）
```

不能在辨证还没完成时就开处方。

---

## 易经类比

符合易经所强调的：
> 从结构、关系、变化回到本体

- **结构**：三套数据源的结构是否一致
- **关系**：计算事实之间的关系是否正确
- **变化**：边界案例下计算是否稳定
- **本体**：回到计算事实本身的正确性

不能在本体还没验证时就直接构建上层应用。

---

## 当前状态

| 阶段 | 状态 | commit |
|------|------|--------|
| 架构裁决基线 | ✅ 已保存 | `168b2a4` |
| P0-1 Source Reconciliation | 🔵 当前 | - |
| P0-2 Integrity Audit | ⚠️ 部分完成（3处确认） | `168b2a4` |
| P0-3 Boundary Cases | ⏳ 待执行 | - |
| P0-4 Golden Dataset | ⚠️ Step 1 完成（1983案例） | - |
| P0-5 State/Signal Audit | ⏳ 待执行 | - |
| CALCULATION + STATE FREEZE | ❌ 未完成 | - |
| Canonical State 实现 | ❌ 禁止提前 | - |
| P6.5-C 恢复 | ❌ 禁止提前 | - |

---

## 下一步

**立即执行 P0-1 Calculation Source Reconciliation**：
- 三套数据源逐项 diff
- 建立 SOURCE_DIFF_REPORT
- 不重构、不实现、只审计

---

*本约束是执行层面的硬约束，高于架构裁决结果。任何违反本约束的执行行为都应被拒绝。*
