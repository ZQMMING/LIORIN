# P0-2.2 RuleContext → Rule → Signal "辨准"审计

> **审计时间**：2026-08-29
> **审计目标**：审计 RuleContext 的字段完整性、Schema 边界、以及 Rule 的来源与授权，确认"辨"到底是怎么辨出来的
> **基于 commit**：`9b71dd2`
> **核心问题**：辨不是基于另一个"结论"，而是基于 Calculation Facts 构造出的 RuleContext，再由经过授权的 Rule 进行匹配。

---

## 一、核心结论

### 🟡 最终裁决：RuleContext 的生产填充路径干净，但 Schema 包含未使用的 Semantic State 字段；"辨准"的下一层是 Rule 授权审计

**关键证据**：

1. **build_rule_context() 生产填充路径干净**
   - 它只从 BaziChart 消费 Calculation Fact（day_master, 四柱, five_element_balance）
   - 它自己从 Calculation Fact 计算 Semantic State（heluo_wuxing_imbalance）
   - 它**没有**从 BaziChart 消费已经"辨过"的 Semantic State（spouse_star_strength, five_element_imbalance）

2. **RuleContext Schema 包含未使用的 Semantic State 字段**
   - 行 165-176 定义了 spouse_star, spouse_star_strength, five_element_imbalance 等字段
   - 注释明确说明："EVENT_TOPIC-only fields... matcher never evaluates them in production"
   - 这些字段没有被 build_rule_context() 填充
   - ⚠️ 这是 Schema 边界问题，不是生产链已经坏掉

3. **RuleContext 中包含正确计算的 Semantic State**
   - heluo_wuxing_imbalance（行 186）是 SignalEngine 自己从 five_element_balance 计算出来的
   - 这是正确的分层：Fact → 辨 → RuleContext → Rule
   - ✅ 这符合"辨基于算出来的事实"的原则

4. **"辨准"的下一层是 Rule 授权审计**
   - 目前已经证明：Calculation Fact → RuleContext 这条链干净
   - 但是还没有证明：RuleContext → RuleMatcher → Signal 这条链中的 Rule 本身是否经过授权
   - 下一阶段需要审计：每条 Rule 的事实依据是什么？阈值从哪里来？是否经过原典授权？

---

## 二、RuleContext 完整字段分析

### RuleContext 字段分类

#### 第一类：基础 Calculation Fact（从 BaziChart 直接消费）

| 字段 | 行号 | 分类 | 来源 | 说明 |
|------|------|------|------|------|
| `day_master` | 139 | CALCULATION_FACT | bazi.day_master | 日主 |
| `day_master_element` | 140 | CALCULATION_FACT | STEM_ELEMENT[bazi.day_master] | 日主五行 |
| `day_branch` | 141 | CALCULATION_FACT | bazi.day_pillar.earthly_branch | 日支 |
| `month_stem` | 142 | CALCULATION_FACT | bazi.month_pillar.heavenly_stem | 月干 |
| `month_branch` | 143 | CALCULATION_FACT | bazi.month_pillar.earthly_branch | 月支 |
| `year_stem` | 144 | CALCULATION_FACT | bazi.year_pillar.heavenly_stem | 年干 |
| `year_branch` | 145 | CALCULATION_FACT | bazi.year_pillar.earthly_branch | 年支 |
| `hour_stem` | 146 | CALCULATION_FACT | bazi.hour_pillar.heavenly_stem | 时干 |
| `hour_branch` | 147 | CALCULATION_FACT | bazi.hour_pillar.earthly_branch | 时支 |
| `gender` | 148 | INPUT | 输入参数 | 性别 |
| `season` | 149 | DERIVED_FACT | SEASON_BY_BRANCH[month_branch] | 季节 |
| `layer` | 155 | META | 输入参数 | 信号层 |
| `theme` | 156 | META | 输入参数 | 主题 |

#### 第二类：派生 Calculation Fact（从基础 Fact 计算）

| 字段 | 行号 | 分类 | 来源 | 说明 |
|------|------|------|------|------|
| `month_hidden_main_ten_god` | 157 | DERIVED_FACT | month_hidden_main_ten_god(day_master, month_branch) | 月令主气十神 |
| `month_hidden_main_ten_god_transparent` | 158 | DERIVED_FACT | hidden_main_stem_is_transparent(month_branch, four_stems) | 月令主气透干 |
| `transparent_ten_gods` | 159 | DERIVED_FACT | transparent_ten_gods_list(day_master, four_stems) | 透干十神 |
| `day_master_stage_month` | 160 | DERIVED_FACT | longhu_stage(day_master, month_branch) | 日主十二长生（月令） |
| `day_master_road_month` | 161 | DERIVED_FACT | road_branch(day_master) == month_branch | 日主禄（月令） |
| `day_master_absolute_month` | 162 | DERIVED_FACT | absolute_branch(day_master) == month_branch | 日主刃（月令） |
| `day_branch_main_ten_god` | 163 | DERIVED_FACT | ten_god(day_master, hidden_main_stem(day_branch)) | 日支主气十神 |
| `tianyi_guiren_branches` | 164 | DERIVED_FACT | tianyi_guiren(day_master) | 天乙贵人 |

#### 第三类：紫微 Calculation Fact（从 ZiweiChart 消费）

| 字段 | 行号 | 分类 | 来源 | 说明 |
|------|------|------|------|------|
| `soul_palace_main_star_key` | 150 | CALCULATION_FACT | ziwei | 命宫主星 |
| `soul_palace_main_star_zh` | 151 | CALCULATION_FACT | ziwei | 命宫主星（中文） |
| `analysis_day_stem` | 152 | CALCULATION_FACT | huangli | 分析日干 |
| `analysis_day_branch` | 153 | CALCULATION_FACT | huangli | 分析日支 |
| `daily_sihua_roles` | 154 | CALCULATION_FACT | ziwei | 日四化 |

#### 第四类：正确计算的 Semantic State（SignalEngine 自己从 Fact 计算）

| 字段 | 行号 | 分类 | 来源 | 说明 |
|------|------|------|------|------|
| `heluo_benming_guawuxing` | 185 | SEMANTIC_STATE | extract_heluo_context() | 本命卦五行 |
| `heluo_wuxing_imbalance` | 186 | SEMANTIC_STATE | extract_heluo_context() | 河洛五行失衡（从 five_element_balance 计算）✅ |
| `heluo_dishu_youyu` | 187 | SEMANTIC_STATE | extract_heluo_context() | 地数有余 |
| `heluo_birth_season_unfavorable` | 188 | SEMANTIC_STATE | extract_heluo_context() | 生于不利时节 |
| `heluo_benming_gong` | 189 | CALCULATION_FACT | extract_heluo_context() | 本命卦宫 |
| `heluo_benming_guaming` | 190 | CALCULATION_FACT | extract_heluo_context() | 本命卦名 |
| `heluo_yuantang` | 191 | CALCULATION_FACT | extract_heluo_context() | 元堂 |
| `heluo_yuantang_index` | 192 | CALCULATION_FACT | extract_heluo_context() | 元堂索引 |
| `heluo_houtian_guaming` | 193 | CALCULATION_FACT | extract_heluo_context() | 后天卦名 |

**关键发现**：
- `heluo_wuxing_imbalance` 是 SignalEngine 自己从 `five_element_balance`（Calculation Fact）计算出来的
- 这是正确的分层：Fact → 辨 → RuleContext → Rule
- ✅ 这符合"辨基于算出来的事实"的原则

#### 第五类：流年应期 Calculation Fact（EventTopicEngine 提供）

| 字段 | 行号 | 分类 | 来源 | 说明 |
|------|------|------|------|------|
| `flow_year_stem` | 178 | CALCULATION_FACT | EventTopicEngine | 流年干 |
| `flow_year_branch` | 179 | CALCULATION_FACT | EventTopicEngine | 流年支 |
| `flow_year_branch_element` | 180 | DERIVED_FACT | EventTopicEngine | 流年支五行 |
| `flow_year_branch_clash_day_branch` | 181 | DERIVED_FACT | EventTopicEngine | 流年支冲日支 |
| `flow_year_branch_harm_day_branch` | 182 | DERIVED_FACT | EventTopicEngine | 流年支害日支 |
| `flow_year_branch_main_ten_god` | 183 | DERIVED_FACT | EventTopicEngine | 流年支主气十神 |
| `flow_year_branch_main_element_clash` | 184 | DERIVED_FACT | EventTopicEngine | 流年支主气五行冲 |

#### 第六类：未使用的 Semantic State 字段（Schema 边界问题）⚠️

| 字段 | 行号 | 分类 | 注释说明 | 状态 |
|------|------|------|----------|------|
| `spouse_star` | 167 | SEMANTIC_STATE | EVENT_TOPIC-only fields | ⚠️ Schema 中定义，未被填充，生产中不评估 |
| `spouse_star_attack` | 168 | SEMANTIC_STATE | EVENT_TOPIC-only fields | ⚠️ Schema 中定义，未被填充，生产中不评估 |
| `officer_mixed` | 169 | SEMANTIC_STATE | EVENT_TOPIC-only fields | ⚠️ Schema 中定义，未被填充，生产中不评估 |
| `day_branch_clash` | 170 | CALCULATION_FACT | EVENT_TOPIC-only fields | ⚠️ Schema 中定义，未被填充，生产中不评估 |
| `day_branch_harm` | 171 | CALCULATION_FACT | EVENT_TOPIC-only fields | ⚠️ Schema 中定义，未被填充，生产中不评估 |
| `spouse_star_strength` | 172 | SEMANTIC_STATE | EVENT_TOPIC-only fields | ⚠️ Schema 中定义，未被填充，生产中不评估 |
| `peach_blossom` | 173 | SEMANTIC_STATE | EVENT_TOPIC-only fields | ⚠️ Schema 中定义，未被填充，生产中不评估 |
| `branch_clash_map` | 174 | CALCULATION_FACT | EVENT_TOPIC-only fields | ⚠️ Schema 中定义，未被填充，生产中不评估 |
| `branch_harm_map` | 175 | CALCULATION_FACT | EVENT_TOPIC-only fields | ⚠️ Schema 中定义，未被填充，生产中不评估 |
| `five_element_imbalance` | 176 | SEMANTIC_STATE | EVENT_TOPIC-only fields | ⚠️ Schema 中定义，未被填充，生产中不评估 |

**注释原文**（行 165-166）：
```python
# EVENT_TOPIC-only fields (kept here so draft EVENT_TOPIC rules can be
# statically validated; matcher never evaluates them in production).
```

**关键发现**：
- 这些字段在 RuleContext Schema 中定义了
- 但是 build_rule_context() 没有填充它们
- 注释明确说 "matcher never evaluates them in production"
- 它们只是为了让 draft EVENT_TOPIC rules 可以静态验证
- ⚠️ 这是 Schema 边界问题，不是生产链已经坏掉
- 建议：后续应该将这些字段移到单独的 EventTopicRuleContext，或者明确标记为 deprecated

---

## 三、RuleContext 生产填充路径确认

### build_rule_context() 实际填充的字段

从 signal_engine.py 的 build_rule_context() 函数（行 137-200+）来看，它实际填充了以下字段：

1. **基础 Calculation Fact**：day_master, day_master_element, day_branch, month_stem, month_branch, year_stem, year_branch, hour_stem, hour_branch, season
2. **派生 Calculation Fact**：month_hidden_main_ten_god, month_hidden_main_ten_god_transparent, transparent_ten_gods, day_master_stage_month, day_master_road_month, day_master_absolute_month, day_branch_main_ten_god
3. **河洛字段**：heluo_*（来自 extract_heluo_context()）
4. **META**：layer, theme（需要确认是否填充）

### build_rule_context() 没有填充的字段

1. **紫微字段**：soul_palace_main_star_key, soul_palace_main_star_zh, analysis_day_stem, analysis_day_branch, daily_sihua_roles（可能由其他地方填充）
2. **流年字段**：flow_year_*（由 EventTopicEngine 填充）
3. **未使用的 Semantic State 字段**：spouse_star, spouse_star_strength, five_element_imbalance 等（明确不填充）

### 关键确认

✅ **build_rule_context() 没有从 BaziChart 消费已经"辨过"的 Semantic State**
- 它没有消费 bazi.spouse_star_strength
- 它没有消费 bazi.five_element_imbalance
- 它没有消费 bazi.kong_wang 的"力量减半"语义

✅ **build_rule_context() 自己从 Calculation Fact 计算 Semantic State**
- 它从 five_element_balance（Calculation Fact）计算 heluo_wuxing_imbalance（Semantic State）
- 这是正确的分层：Fact → 辨 → RuleContext

---

## 四、RuleMatcher 与 Rule 授权审计（初步）

### RuleMatcher 的工作原理

从 matcher.py 的 _eval_leaf() 函数（行 196+）来看：

1. Rule 包含条件（conditions），每个条件是一个 leaf
2. 每个 leaf 包含：field（字段名）、op（操作符）、value（值）
3. RuleMatcher 从 RuleContext 获取字段值，然后评估条件
4. 支持的操作符：exists, eq, ne, in, nin, contains, not_contains, gte, lte, gt, lt, regex

### Rule 授权审计的必要性

目前已经证明：
- Calculation Fact → RuleContext 这条链干净
- RuleContext → RuleMatcher → Signal 这条链在工程上可以运行

但是还没有证明：
- **每条 Rule 的事实依据是什么？**
- **Rule 中的阈值（如 0.6, 0.3）从哪里来？**
- **Rule 是否经过原典授权？**
- **Rule 是五部经典、盲派体系、紫微规则、河洛规则，还是项目自己推导的？**

这才是真正的"辨准"。

### Rule 授权审计的下一步

需要审计：
1. Rule 文件的位置和数量（backend/data/rules/*.json）
2. 每条 Rule 的条件和阈值
3. 每条 Rule 的来源和授权状态
4. Rule 中是否包含未经授权的 Semantic State 字段
5. Rule 中是否包含未经授权的阈值

---

## 五、当前状态总结

### "算 → 辨 → 解"边界状态

| 层 | 状态 | 说明 |
|----|------|------|
| 算（Calculation） | 🟡 继续独立证明 | BaziChart 混合 DTO，但下游未消费 Semantic State |
| Fact → RuleContext | ✅ **干净** | build_rule_context() 只消费 Calculation Fact，自己计算 Semantic State |
| RuleContext Schema | 🟡 **边界问题** | 包含未使用的 Semantic State 字段（EVENT_TOPIC-only） |
| RuleContext → RuleMatcher | ✅ 工程上可运行 | 支持多种操作符，未知字段/操作符报错 |
| Rule 授权 | 🔴 **未审计** | 每条 Rule 的事实依据、阈值来源、原典授权状态未审计 |
| Rule → Signal | ✅ 工程上可运行 | Rule 匹配后生成 Signal |
| Signal → Cross | ✅ 干净 | CrossAnalyzer 只消费 Signal |
| Cross → SIR | ✅ 干净 | CanonicalContent 只使用 bazi.day_master |
| 解 | ⏸️ 冻结 | 不碰 |

### 已关闭的问题

| 问题 | 状态 |
|------|------|
| SignalEngine 是否消费 BaziChart 的 Semantic State？ | ✅ **已关闭**：不消费 |
| build_rule_context() 是否消费已经"辨过"的结果？ | ✅ **已关闭**：不消费，自己从 Fact 计算 |
| RuleContext 生产填充路径是否干净？ | ✅ **已关闭**：干净 |

### 仍然存在的问题

| 问题 | 状态 | 说明 |
|------|------|------|
| RuleContext Schema 包含未使用的 Semantic State 字段 | 🟡 边界问题 | EVENT_TOPIC-only fields，未被填充，生产中不评估 |
| Rule 授权审计 | 🔴 未审计 | 每条 Rule 的事实依据、阈值来源、原典授权状态 |
| Bazi Calculation 正确性 | 🟡 继续独立证明 | 需要 Golden Dataset 验证 |
| Ziwei Signal 来源 | 🟡 后续确认 | 需要审计 ziwei_engine.extract_baseline_signal() |

---

## 六、下一步建议

### P0-2.2.1：Rule 文件盘点与分类（高优先级）

目标：盘点 backend/data/rules/*.json 中的所有 Rule，按体系分类（子平、盲派、紫微、河洛、易经），并记录每条 Rule 的条件和阈值。

### P0-2.2.2：Rule 阈值来源审计（高优先级）

目标：审计每条 Rule 中的阈值（如 0.6, 0.3, 0.4）的来源，确认是否经过原典授权，还是项目自己推导的。

### P0-2.2.3：RuleContext Schema 边界清理（中优先级）

目标：将 EVENT_TOPIC-only fields 从 RuleContext Schema 中移除，或移到单独的 EventTopicRuleContext，明确标记为 deprecated。

### P0-3：Boundary Cases（高优先级）

目标：建立边界测试用例，验证计算引擎在边界情况下的正确性。

### P0-4：Calculation Golden Dataset（高优先级）

目标：建立计算 Golden Dataset，验证 Bazi Calculation 的正确性。

---

## 七、审计总结

### 本次审计的核心发现

1. ✅ **build_rule_context() 生产填充路径干净**
   - 只从 BaziChart 消费 Calculation Fact（day_master, 四柱, five_element_balance）
   - 自己从 Calculation Fact 计算 Semantic State（heluo_wuxing_imbalance）
   - 没有从 BaziChart 消费已经"辨过"的 Semantic State

2. 🟡 **RuleContext Schema 包含未使用的 Semantic State 字段**
   - 行 165-176 定义了 spouse_star, spouse_star_strength, five_element_imbalance 等字段
   - 注释明确说 "EVENT_TOPIC-only fields... matcher never evaluates them in production"
   - 这些字段没有被 build_rule_context() 填充
   - 这是 Schema 边界问题，不是生产链已经坏掉

3. ✅ **RuleContext 中包含正确计算的 Semantic State**
   - heluo_wuxing_imbalance 是 SignalEngine 自己从 five_element_balance 计算出来的
   - 这是正确的分层：Fact → 辨 → RuleContext → Rule

4. 🔴 **"辨准"的下一层是 Rule 授权审计**
   - 目前已经证明：Calculation Fact → RuleContext 这条链干净
   - 但是还没有证明：RuleContext → RuleMatcher → Signal 这条链中的 Rule 本身是否经过授权
   - 下一阶段需要审计：每条 Rule 的事实依据是什么？阈值从哪里来？是否经过原典授权？

### 当前裁决

| 项目 | 状态 |
|------|------|
| Fact → RuleContext 生产填充路径 | ✅ **干净** |
| RuleContext Schema 边界 | 🟡 **包含未使用的 Semantic State 字段** |
| RuleContext → RuleMatcher 工程可行性 | ✅ **可运行** |
| Rule 授权审计 | 🔴 **未审计，下一阶段最高优先级** |
| Rule → Signal 工程可行性 | ✅ **可运行** |
| "算 → 辨"第一道门 | ✅ **已立住** |
| "辨准" | 🟡 **数据入口正确，Rule 授权未审计** |

---

*本报告是 P0-2.2 RuleContext → Rule → Signal "辨准"审计的成果。通过审计 RuleContext 的完整字段、生产填充路径、Schema 边界，确认 build_rule_context() 生产填充路径干净，只消费 Calculation Fact，自己计算 Semantic State。RuleContext Schema 包含未使用的 Semantic State 字段（EVENT_TOPIC-only），这是 Schema 边界问题，不是生产链已经坏掉。"辨准"的下一层是 Rule 授权审计，需要审计每条 Rule 的事实依据、阈值来源、原典授权状态。*
