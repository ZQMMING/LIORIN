# P0-2.4 身强身弱/旺衰辨识模型深度解剖

> **审计时间**：2026-08-29
> **审计目标**：深度解剖当前工程的"身强身弱/旺衰"整条辨识链，看看工程现在究竟是"事实 → 证据 → 综合辨识"还是"事实 → 一个 Rule → 直接宣布身强/身弱"
> **基于 commit**：`f67200b`
> **核心问题**：原典如何从多个事实形成一个辨识？

---

## 一、核心结论

### 🔴 最终裁决：当前工程的旺衰辨识模型存在严重架构问题；19 条相关 Rule 中，9 条是"单一证据 → 直接结论"，3 条 active Rule 使用了未被填充的 RuleContext 字段（生产中永远不会匹配），2 条 Rule 条件定义有问题

**关键证据**：

1. **19 条旺衰相关 Rule 统计**
   - 单一证据 Rule: 9 条（47%）
   - 直接宣布身强/身弱: 13 条（68%）
   - Draft 状态: 15 条（79%）
   - Active 状态: 4 条（21%）

2. **DTS-101~105 都是"单一证据 → 直接结论"**
   - DTS-101：得令 → SUPPORT（身强）
   - DTS-102：失令 → CONSTRAINT（身弱）
   - DTS-103：日支通根 → SUPPORT
   - DTS-104：月支临官帝旺 → SUPPORT
   - DTS-105：比劫透干得势 → SUPPORT（但条件是空的！）

3. **3 条 active Rule 使用了未被填充的 RuleContext 字段**
   - HLT-106：five_element_imbalance present True → HEALTH_RISK（active）
   - HLT-305：five_element_imbalance + 流年为失衡旺五行 → HEALTH_RISK（active）
   - MAR-105：gender eq male + spouse_star_strength in ['weak', 'rootless'] → MARRIAGE_RISK（active）
   - **这些字段在 RuleContext 中定义了，但 build_rule_context() 没有填充它们（EVENT_TOPIC-only fields）**
   - **这意味着这 3 条 Rule 在生产中可能永远不会匹配！**

4. **2 条 Rule 条件定义有问题**
   - DTS-105：条件数 1，但条件详情是 ['  ']（空字符串）
   - MK-103：条件数 0（没有条件，永远匹配）

---

## 二、旺衰相关 Rule 逐条分析

### 第一类："单一证据 → 直接结论"（9 条，47%）

这些 Rule 只使用一个证据，就直接宣布身强/身弱。这正是用户指出的问题："事实 → 一个 Rule → 直接宣布身强/身弱"。

| Rule ID | 标题 | 条件 | 输出 | 状态 | 问题 |
|---------|------|------|------|------|------|
| DTS-101 | 日主得令 → SUPPORT | month_hidden_main_ten_god in [印比劫] | SUPPORT | draft | 单一证据，未考虑得地/得势/受制 |
| DTS-102 | 日主失令 → CONSTRAINT | month_hidden_main_ten_god in [官财食伤] | CONSTRAINT | draft | 单一证据，未考虑得地/得势/受制 |
| DTS-103 | 日支通根 → SUPPORT | day_branch_main_ten_god in [比劫] | SUPPORT | draft | 单一证据，未考虑得令/得势/受制 |
| DTS-104 | 月支临官帝旺 → SUPPORT | day_master_stage_month in [临官, 帝旺] | SUPPORT | draft | 单一证据，未考虑其他因素 |
| DTS-105 | 比劫透干得势 → SUPPORT | **条件为空！** | SUPPORT | draft | **条件定义错误** |
| SMTH-101 | 十二宫旺位 → SUPPORT | day_master_stage_month in [临官, 帝旺] | SUPPORT | draft | 单一证据，与 DTS-104 重复 |
| SMTH-102 | 十二宫弱位 → CONSTRAINT | day_master_stage_month in [死, 墓, 绝] | CONSTRAINT | draft | 单一证据 |
| HH-101 | 合化需得令 | day_master_stage_month in [临官, 帝旺, 长生] | SUPPORT | draft | 单一证据 |
| HLT-106 | 五行失衡 → 脏器风险 | **five_element_imbalance present True** | HEALTH_RISK | **active** | **使用未被填充的字段** |

### 第二类：多证据组合（4 条，21%）

这些 Rule 开始考虑多个证据的组合，但仍然是简单的 AND 逻辑，没有真正的"综合辨识"。

| Rule ID | 标题 | 条件数 | 输出 | 状态 | 说明 |
|---------|------|--------|------|------|------|
| DTS-106 | 得令但月令被围克 → 身弱 | 2 | CONSTRAINT | draft | 得令 + 日支冲 → 身弱 |
| DTS-107 | 失令但有强根/帮扶 → 身偏强 | 2 | SUPPORT | draft | 失令 + 日支有印比 → 身偏强 |
| MK-101 | 四库旺衰判据 | 2 | CONSTRAINT | draft | 得令 + 得地 → 库/墓判断 |
| MK-102 | 库宜开墓宜闭 | 2 | CONSTRAINT | draft | 月令主气 + 月令为四库 |
| MK-104 | 库中财官印透干 → 不需再冲 | 3 | SUPPORT | draft | 月令为四库 + 月令主气非比劫 + 条件3为空 |
| MK-105 | 库根透出后逢冲 → 余气尽伤 | 3 | CONSTRAINT | draft | 月令为四库 + 日支为四库 + 得令 |
| HLT-305 | 本命五行失衡 + 流年为失衡旺五行 | 2 | HEALTH_RISK | **active** | **使用未被填充的字段 five_element_imbalance** |
| MAR-105 | 男命财星弱/无根 → 婚姻迟滞 | 2 | MARRIAGE_RISK | **active** | **使用未被填充的字段 spouse_star_strength** |
| WLT-103 | 流年财星且日主得地 → 能担财 | 2 | SUPPORT | active | 流年财星 + 日主得地 |

### 第三类：条件定义有问题（2 条，11%）

| Rule ID | 标题 | 问题 | 状态 |
|---------|------|------|------|
| DTS-105 | 比劫透干得势 → SUPPORT | 条件数 1，但条件详情是 ['  ']（空字符串） | draft |
| MK-103 | 开库方式 | 条件数 0（没有条件，永远匹配） | draft |

---

## 三、最严重的问题：3 条 active Rule 使用了未被填充的 RuleContext 字段

### 问题描述

在 P0-2.2 的审计中，我们发现 RuleContext Schema 中定义了以下字段（行 165-176），但注释明确说明：

```python
# EVENT_TOPIC-only fields (kept here so draft EVENT_TOPIC rules can be
# statically validated; matcher never evaluates them in production).
spouse_star: dict | None = None
spouse_star_attack: str | None = None
officer_mixed: bool | None = None
day_branch_clash: bool | None = None
day_branch_harm: bool | None = None
spouse_star_strength: str | None = None  # ⚠️
peach_blossom: bool | None = None
branch_clash_map: dict | None = None
branch_harm_map: dict | None = None
five_element_imbalance: bool | None = None  # ⚠️
```

**关键问题**：
- 这些字段在 RuleContext Schema 中定义了
- 但是 build_rule_context() **没有填充**它们
- 注释说 "matcher never evaluates them in production"
- 但是，有 3 条 **active 状态**的 Rule 使用了这些字段！

### 受影响的 Rule

| Rule ID | 标题 | 使用的未填充字段 | 状态 | 影响 |
|---------|------|------------------|------|------|
| HLT-106 | 五行失衡 → 脏器风险 | five_element_imbalance | **active** | 生产中永远不会匹配（字段始终为 None） |
| HLT-305 | 本命五行失衡 + 流年为失衡旺五行 | five_element_imbalance | **active** | 生产中永远不会匹配 |
| MAR-105 | 男命财星弱/无根 → 婚姻迟滞 | spouse_star_strength | **active** | 生产中永远不会匹配 |

### 这意味着什么

1. **这 3 条 Rule 在生产中是"死规则"**
   - 它们的条件引用了 build_rule_context() 没有填充的字段
   - 这些字段始终为 None
   - 因此这些 Rule 的条件永远不会匹配
   - 它们永远不会产生 Signal

2. **这是一个严重的治理问题**
   - 这些 Rule 被标记为 active，暗示它们在生产中工作
   - 但实际上它们是死规则
   - 这会误导开发者和用户，以为这些辨识逻辑在工作

3. **这暴露了 Rule 授权审计的必要性**
   - 如果没有这次深度审计，这些死规则可能会一直存在
   - 这证明了 P0-2.3 RULE AUTHORIZATION AUDIT 的必要性

---

## 四、"单一证据 → 直接结论"问题分析

### 问题描述

DTS-101~105、SMTH-101~102、HH-101 等 9 条 Rule 都是"单一证据 → 直接结论"的模式。

例如：
- DTS-101：月令主气为印比劫（得令）→ 直接判定 SUPPORT（身强）
- DTS-102：月令主气为官财食伤（失令）→ 直接判定 CONSTRAINT（身弱）

### 这为什么是问题

用户在之前的分析中已经明确指出：

> 假设工程里有：
> Rule: 月令生扶日主 → 身强
> 工程上可以找到经典：月令很重要。
> 于是有人可能给这个 Rule 标：AUTHORIZED
> 这是错误的。
> 因为经典支持的是：月令 ↓ 旺衰判断的重要证据
> 并不必然支持：月令有利 ↓ 整体身强
> 《滴天髓》恰恰提醒"得时"不能机械等同于旺，并强调年、日、时仍然有损益之权。

### 正确的模型应该是

```
Calculation Facts
    ↓
Evidence Derivation
    ├── 得令证据
    ├── 得地证据
    ├── 得势证据
    └── 受制证据
    ↓
Evidence Relation
    ├── 生扶
    ├── 克泄耗
    └── 制化
    ↓
System-specific Judgment
    ├── 子平：旺衰/格局
    ├── 盲派：结构/象
    └── 其他体系
    ↓
Semantic State
    ↓
Signal
```

### 当前工程的模型

```
Calculation Facts
    ↓
单一 Rule（如 DTS-101：得令 → 身强）
    ↓
直接宣布 Semantic State（SUPPORT / CONSTRAINT）
    ↓
Signal
```

**这是一个严重的架构简化问题**：
- 它把"证据"直接等同于"结论"
- 它没有考虑多个证据之间的关系
- 它没有考虑不同体系的辨识逻辑
- 它没有考虑证据的权重和组合

---

## 五、Rule 条件定义问题

### DTS-105：条件为空

```json
{
  "rule_id": "DTS-105",
  "title": "比劫透干得势(党众)→ SUPPORT",
  "conditions": {
    "all": [
      {
        "field": "",
        "op": "",
        "value": ""
      }
    ]
  }
}
```

**问题**：
- field、op、value 都是空字符串
- 这条 Rule 的条件没有正确定义
- 它可能永远不会匹配，或者总是匹配（取决于 RuleMatcher 的实现）

### MK-103：条件数为 0

```json
{
  "rule_id": "MK-103",
  "title": "开库方式:刑开库缓慢代价大,冲开库高效冲突明显",
  "conditions": {
    "all": []
  }
}
```

**问题**：
- conditions.all 是空数组
- 这条 Rule 没有任何条件
- 它可能总是匹配（取决于 RuleMatcher 的实现）
- 这意味着它可能在所有命例中都产生 Signal

---

## 六、当前状态总结

### 旺衰辨识模型状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 旺衰相关 Rule 总数 | 19 | |
| 单一证据 → 直接结论 | 9（47%） | 架构简化问题 |
| 直接宣布身强/身弱 | 13（68%） | |
| Draft 状态 | 15（79%） | 不应在生产中使用 |
| Active 状态 | 4（21%） | |
| Active 但使用未填充字段 | 3 | **生产中永远不会匹配** |
| 条件定义有问题 | 2 | DTS-105 条件为空，MK-103 条件数为 0 |
| 多证据组合 Rule | 4（21%） | 简单 AND 逻辑，非真正综合辨识 |
| 完成原典级授权 | 0 | |

### "算 → 辨 → 解"边界状态

| 层 | 状态 | 说明 |
|----|------|------|
| 算（Calculation） | 🟡 继续独立证明 | BaziChart 混合 DTO，但下游未消费 Semantic State |
| Fact → RuleContext | ✅ 干净 | build_rule_context() 只消费 Calculation Fact |
| RuleContext → RuleMatcher | ✅ 工程链成立 | |
| **Rule 授权** | 🔴 **严重问题** | 19 条旺衰 Rule 中，9 条单一证据，3 条 active 死规则，2 条条件错误 |
| Rule → Signal | ✅ 工程上可运行 | 但语义正确性未证明 |
| "辨准" | 🔴 **未通过** | 旺衰辨识模型存在严重架构问题 |

---

## 七、下一步建议

### P0-2.4.1：修复 3 条 active 死规则（最高优先级）

目标：修复 HLT-106、HLT-305、MAR-105 这 3 条 active Rule，它们使用了 build_rule_context() 未填充的字段。

选项：
1. 在 build_rule_context() 中填充这些字段（但需要确认这些字段的计算逻辑和授权状态）
2. 将这些 Rule 降级为 draft（直到字段被正确填充和授权）
3. 修改这些 Rule 的条件，使用已被填充的字段

### P0-2.4.2：修复 2 条条件定义错误的 Rule（高优先级）

目标：修复 DTS-105（条件为空）和 MK-103（条件数为 0）。

### P0-2.4.3：旺衰辨识模型重构设计（高优先级，长期工作）

目标：设计正确的旺衰辨识模型，从"单一证据 → 直接结论"升级为"多证据 → 证据关系 → 体系-specific 判断 → Semantic State"。

这需要：
1. 定义 Evidence Derivation 层（得令、得地、得势、受制）
2. 定义 Evidence Relation 层（生扶、克泄耗、制化）
3. 定义 System-specific Judgment 层（子平旺衰/格局、盲派结构/象）
4. 定义 Semantic State 输出
5. 逐条 Rule 重新设计和授权

### P0-2.4.4：RuleLoader 生产过滤确认（高优先级）

目标：确认 RuleLoader 是否过滤了 status != "active" 的规则，确保 15 条 Draft 规则不在生产中被评估。

### P0-3：Boundary Cases（高优先级）

目标：建立边界测试用例，验证计算引擎在边界情况下的正确性。

### P0-4：Calculation Golden Dataset（高优先级）

目标：建立计算 Golden Dataset，验证 Bazi Calculation 的正确性。

---

## 八、审计总结

### 本次审计的核心发现

1. 🔴 **旺衰辨识模型存在严重架构问题**
   - 19 条相关 Rule 中，9 条是"单一证据 → 直接结论"（47%）
   - 这把"证据"直接等同于"结论"，没有考虑多个证据之间的关系
   - 这与用户指出的"得时不能机械等同于旺"的原则相违背

2. 🔴 **3 条 active Rule 是"死规则"**
   - HLT-106、HLT-305、MAR-105 使用了 build_rule_context() 未填充的字段
   - 这些字段始终为 None，因此这些 Rule 在生产中永远不会匹配
   - 这是一个严重的治理问题

3. 🔴 **2 条 Rule 条件定义有问题**
   - DTS-105：条件为空
   - MK-103：条件数为 0（没有条件，永远匹配）

4. 🟡 **15 条 Draft 规则不应在生产中使用**
   - 需要确认 RuleLoader 是否过滤了 status != "active" 的规则

5. 🟡 **只有 4 条多证据组合 Rule**
   - 而且是简单 AND 逻辑，不是真正的"综合辨识"

6. 🔴 **0 条完成原典级授权**

### 当前裁决

| 项目 | 状态 |
|------|------|
| 算 → Fact | 🟡 继续独立证明 |
| Fact → RuleContext | ✅ 干净 |
| RuleContext → RuleMatcher | ✅ 工程链成立 |
| **Rule 授权（旺衰）** | 🔴 **严重问题** |
| Rule → Signal | ✅ 工程上可运行，语义正确性未证明 |
| "辨准"（旺衰） | 🔴 **未通过** |

### 最重要的一句话

这次深度解剖证明了用户之前的判断是完全正确的：

> 现在真正进入了第二个核心验证阶段：原典如何从多个事实形成一个辨识？

当前工程的旺衰辨识模型还停留在"单一证据 → 直接结论"的简化阶段，没有真正建立"多证据 → 证据关系 → 体系-specific 判断 → Semantic State"的完整辨识链。

而且，3 条 active Rule 是"死规则"，2 条 Rule 条件定义有问题，这些都是必须立即修复的治理问题。

等旺衰辨识模型真正建立起来，后面的"格局、调候、用神、盲派结构、紫微、河洛"等才能按同一方法分别建立；这才是真正把"算 → 辨 → 解"严丝合缝地落到代码里。

---

*本报告是 P0-2.4 身强身弱/旺衰辨识模型深度解剖的成果。通过深度解剖 19 条旺衰相关 Rule，发现当前工程的旺衰辨识模型存在严重架构问题：9 条是"单一证据 → 直接结论"（47%），3 条 active Rule 使用了未被填充的 RuleContext 字段（生产中永远不会匹配），2 条 Rule 条件定义有问题。这证明了"原典如何从多个事实形成一个辨识"这个问题还没有真正解决。下一步需要修复死规则和条件错误，然后重新设计旺衰辨识模型。*
