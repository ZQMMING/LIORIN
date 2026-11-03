# P0-2.5 JUDGMENT MODEL AUDIT — 整个辨识层模型审计

> **审计时间**：2026-08-29
> **审计目标**：把现在整个工程里的辨识全部扫出来，逐项回答 8 个问题，确认哪些 Rule 应该保留、哪些应该拆成 Evidence、哪些应该进入 Judgment Strategy、哪些属于格局引擎、哪些属于调候引擎、哪些属于关系引擎、哪些根本放错层
> **基于 commit**：`b7e1d65`
> **核心问题**：顺天知道每一个辨识是从哪些算出来的事实、经过什么传统推理结构，得到什么状态吗？

---

## 一、核心结论

### 🔴 最终裁决：当前工程的整个辨识层（Judgment Layer）存在系统性架构问题；136 条 Rule 中，131 条（96%）直接宣布结论，62 条（46%）是单一条件型，71 条（52%）是简单 AND 组合，没有真正的"Evidence → Evidence Relation → Judgment"推理过程

**关键证据**：

1. **136 条 Rule 总体统计**
   - 直接宣布结论: 131 条（96%）
   - 单一条件型: 62 条（46%）
   - 多条件组合型(AND): 71 条（52%）
   - 多条件择一型(OR): 2 条（1%）
   - 无条件/永远匹配: 1 条（1%）

2. **按辨识类型统计**（一条 Rule 可能属于多个类型）
   - 旺衰: 52
   - 神煞: 40
   - 气势: 39
   - 格局: 38
   - 健康: 32
   - 刑冲合害: 30
   - 紫微宫星关系: 29
   - 岁运: 27
   - 官运: 26
   - 财运: 26
   - 河洛卦象: 21
   - 体用: 18
   - 盲派结构: 15
   - 制化: 11
   - 婚姻: 10
   - 合化: 9
   - 其他/未分类: 6
   - 紫微四化: 4
   - 学业: 3
   - 调候: 3
   - 易经卦爻: 3
   - 顺逆: 1
   - 用神: 1

3. **按状态统计**
   - active: 75（55%）
   - draft: 51（38%）
   - validated: 10（7%）

---

## 二、8 个问题的逐项回答

### ① 它辨的是什么？

当前工程的辨识覆盖了 24 个类型，包括：
- 子平体系：旺衰、格局、调候、用神、制化、合化、刑冲合害、清浊、体用、顺逆、气势
- 盲派体系：盲派结构
- 紫微体系：紫微宫星关系、紫微四化
- 河洛体系：河洛卦象
- 易经体系：易经卦爻
- 应用领域：健康、婚姻、财运、学业、官运、岁运、神煞

**问题**：辨识类型非常广泛，但绝大多数都是简单的条件匹配，没有真正的推理过程。

### ② 它依赖哪些 Calculation Facts？

从 Rule 的条件字段来看，主要依赖：
- 基础四柱：day_master, day_branch, month_stem, month_branch, year_stem, year_branch, hour_stem, hour_branch
- 十神：month_hidden_main_ten_god, day_branch_main_ten_god, transparent_ten_gods
- 十二长生：day_master_stage_month
- 通根/得地：day_master_road_month, day_master_absolute_month
- 关系：day_branch_clash, day_branch_harm
- 河洛：heluo_benming_guawuxing, heluo_wuxing_imbalance, heluo_dishu_youyu
- 紫微：soul_palace_main_star_key, daily_sihua_roles
- 流年：flow_year_stem, flow_year_branch, flow_year_branch_main_ten_god

**问题**：这些 Fact 都是从 BaziChart 直接提取的，没有经过 Evidence Derivation 层。

### ③ 哪些 Fact 会变成 Evidence？

当前工程中，Fact 直接变成 Rule 的条件，没有明确的 Evidence 层。

例如：
- month_hidden_main_ten_god in [印比劫] → 直接作为"得令"证据
- day_branch_main_ten_god in [比劫] → 直接作为"得地"证据
- day_master_stage_month in [临官, 帝旺] → 直接作为"得势"证据

**问题**：没有明确的 Evidence Derivation 层，Fact 直接被当作 Evidence 使用。

### ④ Evidence 之间是什么关系？

当前工程中，Evidence 之间的关系只有简单的 AND/OR 逻辑：
- 71 条（52%）是多条件组合型(AND)：所有条件都满足才匹配
- 2 条（1%）是多条件择一型(OR)：任一条件满足就匹配
- 62 条（46%）是单一条件型：只有一个条件

**问题**：没有真正的 Evidence Relation 处理，例如：
- 生扶 vs 克泄耗的力量对比
- 制化关系
- 证据之间的优先级
- 证据的权重（但不能是简单的数值评分）
- 证据的组合逻辑（如"得令但受制"、"失令但有强根"）

### ⑤ 是综合型、结构型、条件型、关系型还是状态转换型？

当前工程的 Rule 主要是：
- **条件型**: 133 条（98%）—— 单一条件或简单 AND/OR 组合
- **结构型**: 少数（如四库、三合等结构判断）
- **综合型**: 几乎没有
- **关系型**: 少数（如刑冲合害关系）
- **状态转换型**: 几乎没有

**问题**：绝大多数 Rule 都是简单的条件型，没有真正的综合判断或状态转换。

### ⑥ 最终产生什么 Semantic State？

当前工程的 Rule 产生的 Semantic State 主要是：
- SUPPORT（身强/支持）
- CONSTRAINT（身弱/约束）
- CHANGE（变化）
- HEALTH_RISK（健康风险）
- MARRIAGE_RISK（婚姻风险）
- 各种 ontology_type（如 WEALTH, CAREER, EDUCATION 等）

**问题**：这些 Semantic State 都是直接从 Rule 条件产生的，没有经过 Judgment 层的综合判断。

### ⑦ 哪部经典/哪套体系授权这种推理？

从 Rule 的 source.work 来看：
- 滴天髓: 7 条
- 三命通会: 5 条
- 渊海子平: 5 条
- 子平真诠: 35 条（但很多是工程种子）
- 河洛真数: 38 条
- 工程种子: 15 条
- 其他: 各种来源

**问题**：
- 很多 Rule 的来源声明不准确（如 ZPZ 前缀但 source.work 是"工程种子"）
- 没有一条完成原典级授权
- 没有明确的"经典推理结构"授权

### ⑧ 当前代码是否真的实现了这个推理？

**答案**：没有。

当前代码实现的是：
```
Calculation Facts
    ↓
Rule 条件匹配（简单 AND/OR）
    ↓
直接宣布 Semantic State
    ↓
Signal
```

而不是：
```
Calculation Facts
    ↓
Evidence Derivation（得令、得地、得势、受制）
    ↓
Evidence Relation（生扶 vs 克泄耗、制化、优先级）
    ↓
System-specific Judgment（子平旺衰/格局、盲派结构/象）
    ↓
Semantic State
    ↓
Signal
```

---

## 三、辨识类型详细分析

### 子平体系

| 辨识类型 | Rule 数量 | 主要问题 |
|----------|-----------|----------|
| 旺衰 | 52 | 9 条单一证据 → 直接结论；没有综合判断 |
| 格局 | 38 | 条件匹配为主，没有格局成立/破坏的综合判断 |
| 调候 | 3 | 数量太少，没有完整的调候体系 |
| 用神 | 1 | 只有 1 条，没有完整的用神体系 |
| 制化 | 11 | 条件匹配为主，没有制化关系的综合判断 |
| 合化 | 9 | 条件匹配为主，没有合化条件的综合判断 |
| 刑冲合害 | 30 | 关系判断为主，但没有关系之间的优先级 |
| 清浊 | 0 | 没有相关 Rule |
| 体用 | 18 | 条件匹配为主 |
| 顺逆 | 1 | 只有 1 条 |
| 气势 | 39 | 条件匹配为主，没有气势的综合判断 |

### 其他体系

| 辨识类型 | Rule 数量 | 主要问题 |
|----------|-----------|----------|
| 盲派结构 | 15 | 条件匹配为主，没有盲派特有的结构/象法推理 |
| 紫微宫星关系 | 29 | 条件匹配为主，没有紫微特有的宫星关系推理 |
| 紫微四化 | 4 | 数量太少 |
| 河洛卦象 | 21 | 条件匹配为主，没有河洛特有的卦象推理 |
| 易经卦爻 | 3 | 数量太少 |

### 应用领域

| 辨识类型 | Rule 数量 | 主要问题 |
|----------|-----------|----------|
| 健康 | 32 | 2 条 active 死规则（使用未填充字段） |
| 婚姻 | 10 | 1 条 active 死规则（使用未填充字段） |
| 财运 | 26 | 条件匹配为主 |
| 学业 | 3 | 数量太少 |
| 官运 | 26 | 条件匹配为主 |
| 岁运 | 27 | 条件匹配为主 |
| 神煞 | 40 | 条件匹配为主，没有神煞之间的关系 |

---

## 四、当前辨识层的架构问题

### 问题 1：没有 Evidence Derivation 层

当前工程中，Calculation Fact 直接被当作 Rule 条件使用，没有明确的 Evidence Derivation 层。

例如：
- month_hidden_main_ten_god in [印比劫] → 直接作为"得令"证据
- 但"得令"本身应该是一个 Evidence，需要明确的定义和计算

### 问题 2：没有 Evidence Relation 层

当前工程中，Evidence 之间的关系只有简单的 AND/OR 逻辑，没有真正的 Evidence Relation 处理。

例如：
- "得令" + "受制" → 应该如何判断？
- "失令" + "得地" + "得势" → 应该如何判断？
- 生扶 vs 克泄耗的力量对比 → 应该如何处理？

### 问题 3：没有 System-specific Judgment 层

当前工程中，所有 Rule 都在同一个 Rule Pool 中，没有按体系分开。

例如：
- 子平的旺衰判断应该和盲派的结构判断分开
- 紫微的宫星关系应该和河洛的卦象判断分开
- 不同体系的辨识逻辑不同，不能混在一起

### 问题 4：96% 的 Rule 直接宣布结论

136 条 Rule 中，131 条（96%）直接宣布结论，没有推理过程。

这意味着：
- Rule 的条件匹配后，直接产生 Semantic State
- 没有中间的 Judgment 过程
- 这正是"把 Evidence 当成 Judgment"的问题

### 问题 5：46% 的 Rule 是单一条件型

62 条（46%）是单一条件型，只有一个条件就直接宣布结论。

例如：
- 得令 → 身强
- 失令 → 身弱
- 通根 → 身强
- 临官/帝旺 → 身强

这是最严重的简化问题。

---

## 五、正确的辨识层架构应该是什么

### 目标架构

```
算
↓
Calculation Facts
↓
Evidence Derivation
├── 得令证据
├── 得地证据
├── 得势证据
├── 受制证据
├── 调候证据
├── 格局证据
└── 关系证据（合冲刑害）
↓
Evidence Relation
├── 生扶 vs 克泄耗
├── 制化关系
├── 证据优先级
└── 证据组合逻辑
↓
System-specific Judgment
├── 子平：旺衰/格局/调候/用神
├── 盲派：结构/象法
├── 紫微：宫星关系/四化
├── 河洛：卦象/卦数
└── 易经：卦爻/变化
↓
Semantic State
↓
Signal
↓
Cross-domain
↓
解
```

### 关键原则

1. **Evidence 不是 Judgment**：得令、得地、得势、受制都是 Evidence，不是 Judgment
2. **Evidence Relation 是核心**：多个 Evidence 之间的关系处理是 Judgment 的核心
3. **System-specific Judgment**：不同体系有不同的 Judgment 逻辑，不能混在一起
4. **不能用数值评分**：不能把 Evidence 改成 +10、+20、-10 的评分系统
5. **UNRESOLVED 是合法状态**：无法确定时，应该保持 UNRESOLVED，而不是强行判断

---

## 六、当前状态总结

### 辨识层状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 辨识类型覆盖 | 🟡 广泛但浅 | 24 个类型，但绝大多数是简单条件匹配 |
| Evidence Derivation | 🔴 缺失 | Fact 直接被当作 Evidence |
| Evidence Relation | 🔴 缺失 | 只有简单 AND/OR，没有真正的关系处理 |
| System-specific Judgment | 🔴 缺失 | 所有 Rule 混在一个 Pool 中 |
| 直接宣布结论 | 🔴 96% | 131/136 条直接宣布结论 |
| 单一条件型 | 🔴 46% | 62/136 条是单一条件 |
| 完成原典级授权 | 🔴 0 | 无一条完成 |
| active 死规则 | 🔴 3 | 使用未填充字段，生产中永远不会匹配 |

### "算 → 辨 → 解"边界状态

| 层 | 状态 | 说明 |
|----|------|------|
| 算（Calculation） | 🟡 继续独立证明 | BaziChart 混合 DTO，但下游未消费 Semantic State |
| Fact → RuleContext | ✅ 干净 | build_rule_context() 只消费 Calculation Fact |
| RuleContext → RuleMatcher | ✅ 工程链成立 | |
| **Rule 授权** | 🔴 **严重问题** | 136 条中 0 条完成原典级授权，96% 直接宣布结论 |
| **Judgment Layer** | 🔴 **系统性架构问题** | 没有 Evidence Derivation、Evidence Relation、System-specific Judgment |
| Rule → Signal | ✅ 工程上可运行 | 但语义正确性未证明 |
| "辨准" | 🔴 **未通过** | 辨识层需要重新建模 |

---

## 七、下一步建议

### P0-2.5.1：辨识层架构设计（最高优先级）

目标：设计正确的辨识层架构，包括 Evidence Derivation、Evidence Relation、System-specific Judgment 三层。

这需要：
1. 定义 Evidence 类型（得令、得地、得势、受制、调候、格局、关系等）
2. 定义 Evidence Relation 类型（生扶 vs 克泄耗、制化、优先级、组合逻辑）
3. 定义 System-specific Judgment 接口（子平、盲派、紫微、河洛、易经）
4. 定义 Semantic State 输出
5. 明确 UNRESOLVED 状态的处理

### P0-2.5.2：现有 Rule 分类与迁移规划（高优先级）

目标：将现有 136 条 Rule 按辨识类型分类，规划迁移路径：
- 哪些 Rule 应该保留（作为 Evidence 或简单关系判断）
- 哪些 Rule 应该拆成 Evidence
- 哪些 Rule 应该进入 Judgment Strategy
- 哪些 Rule 属于格局引擎
- 哪些 Rule 属于调候引擎
- 哪些 Rule 属于关系引擎
- 哪些 Rule 根本放错层

### P0-2.5.3：修复 3 条 active 死规则（高优先级）

目标：修复 HLT-106、HLT-305、MAR-105 这 3 条 active Rule，它们使用了 build_rule_context() 未填充的字段。

### P0-2.5.4：修复 2 条条件定义错误的 Rule（高优先级）

目标：修复 DTS-105（条件为空）和 MK-103（条件数为 0）。

### P0-3：Boundary Cases（高优先级）

目标：建立边界测试用例，验证计算引擎在边界情况下的正确性。

### P0-4：Calculation Golden Dataset（高优先级）

目标：建立计算 Golden Dataset，验证 Bazi Calculation 的正确性。

---

## 八、审计总结

### 本次审计的核心发现

1. 🔴 **整个辨识层（Judgment Layer）存在系统性架构问题**
   - 没有 Evidence Derivation 层
   - 没有 Evidence Relation 层
   - 没有 System-specific Judgment 层
   - 所有 Rule 混在一个 Pool 中

2. 🔴 **96% 的 Rule 直接宣布结论**
   - 131/136 条直接宣布结论
   - 没有推理过程
   - 这正是"把 Evidence 当成 Judgment"的问题

3. 🔴 **46% 的 Rule 是单一条件型**
   - 62/136 条是单一条件
   - 只有一个条件就直接宣布结论
   - 这是最严重的简化问题

4. 🟡 **辨识类型广泛但浅**
   - 覆盖 24 个类型
   - 但绝大多数是简单条件匹配
   - 没有真正的推理过程

5. 🔴 **0 条完成原典级授权**

6. 🔴 **3 条 active 死规则**

### 当前裁决

| 项目 | 状态 |
|------|------|
| 算 → Fact | 🟡 继续独立证明 |
| Fact → RuleContext | ✅ 干净 |
| RuleContext → RuleMatcher | ✅ 工程链成立 |
| **Rule 授权** | 🔴 **严重问题** |
| **Judgment Layer 架构** | 🔴 **系统性问题，需要重新建模** |
| Rule → Signal | ✅ 工程上可运行，语义正确性未证明 |
| "辨准" | 🔴 **未通过** |

### 最重要的一句话

这次 JUDGMENT MODEL AUDIT 证明了用户之前的判断是完全正确的：

> 当前代码把 Evidence 当成 Judgment 了。

136 条 Rule 中，96% 直接宣布结论，46% 是单一条件型，没有真正的"Evidence → Evidence Relation → Judgment"推理过程。

这不是简单修几条 Rule 就能解决的问题，而是需要重新设计整个辨识层架构。

等辨识层架构真正建立起来，后面的"格局、调候、用神、盲派结构、紫微、河洛"等才能按同一方法分别建立；这才是真正把"算 → 辨 → 解"严丝合缝地落到代码里。

---

*本报告是 P0-2.5 JUDGMENT MODEL AUDIT 的成果。通过审计整个辨识层的 136 条 Rule，发现当前工程的辨识层存在系统性架构问题：没有 Evidence Derivation、Evidence Relation、System-specific Judgment 三层；96% 的 Rule 直接宣布结论；46% 是单一条件型；0 条完成原典级授权；3 条 active 死规则。这证明了"当前代码把 Evidence 当成 Judgment"的问题。下一步需要重新设计辨识层架构，然后将现有 Rule 分类迁移。*
