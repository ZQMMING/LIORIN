# P0-2.3 RULE AUTHORIZATION AUDIT — 辨凭什么

> **审计时间**：2026-08-29
> **审计目标**：逐条审计 backend/data/rules/*.json 中的所有 Rule，确认每条 Rule 的体系归属、原典来源、条件、阈值、授权状态
> **基于 commit**：`dee101a`
> **核心问题**：辨凭什么？每一条"辨"必须回答为什么这么辨，而不是代码能不能这么算。

---

## 一、核心结论

### 🔴 最终裁决：136 条 Rule 中，没有一条完成原典级授权；15 条工程种子规则无原典来源；51 条 Draft 规则不应在生产中使用

**关键证据**：

1. **总共 136 条 Rule**
   - active: 75 条
   - draft: 51 条
   - validated: 10 条

2. **授权状态初步分类**
   - PROVISIONAL: 60 条（有来源但未验证原典）
   - DRAFT: 51 条
   - ENGINEERING_SEED: 15 条（工程种子规则，无原典来源）
   - UNAUTHORIZED: 10 条

3. **没有 Rule 直接使用阈值操作符（gte/lte/gt/lt）**
   - 但是，heluo_wuxing_imbalance 的阈值（0.30/0.10）在 signal_engine.py 中硬编码
   - 这意味着阈值不在 Rule 中，而在代码中，更难审计

4. **15 条工程种子规则无原典来源**
   - source.work = "工程种子"
   - source.location = "v1.0 种子规则(非经典原文直引)"
   - 这些规则没有原典授权依据

5. **51 条 Draft 规则不应在生产中使用**
   - status = "draft"
   - 这些规则是草稿状态，不应该在生产中被评估

---

## 二、Rule 总体统计

### 按体系统计（136 条）

| 体系 | 数量 | 说明 |
|------|------|------|
| 河洛 | 38 | HL/HLT 前缀 |
| 子平真诠 | 35 | ZPZ 前缀 |
| 婚姻 | 8 | MAR 前缀 |
| 滴天髓 | 7 | DTS 前缀 |
| 文昌 | 6 | WLT 前缀 |
| 盲派 | 5 | MK 前缀 |
| 三命通会 | 5 | SMTH 前缀 |
| 渊海子平 | 5 | YHZP 前缀 |
| 财运 | 4 | CRR 前缀 |
| 鬼谷子 | 4 | GW 前缀 |
| 桃花 | 4 | TF/TH 前缀 |
| 紫微 | 4 | ZW 前缀 |
| 河图 | 3 | HH 前缀 |
| 学业 | 2 | EDU 前缀 |
| 岁运 | 2 | SUY 前缀 |
| 神煞 | 2 | SX 前缀 |
| 洛书 | 1 | LM 前缀 |
| 其他 | 1 | QTB 前缀 |

### 按状态统计（136 条）

| 状态 | 数量 | 说明 |
|------|------|------|
| active | 75 | 生产中活跃 |
| draft | 51 | 草稿，不应在生产中使用 |
| validated | 10 | 已验证（但验证标准未审计） |

### 按授权状态初步分类（136 条）

| 授权状态 | 数量 | 说明 |
|----------|------|------|
| PROVISIONAL | 60 | 有来源但未验证原典 |
| DRAFT | 51 | 草稿状态 |
| ENGINEERING_SEED | 15 | 工程种子规则，无原典来源 |
| UNAUTHORIZED | 10 | 未授权 |

---

## 三、关键发现详细分析

### 发现 1：15 条工程种子规则无原典来源

这些规则的 source.work = "工程种子"，source.location = "v1.0 种子规则(非经典原文直引)"。

| Rule ID | 标题 | 说明 |
|---------|------|------|
| HLT-201 | 木元素过弱 → 肝胆失养风险 | 健康断事 |
| HLT-202 | 火元素过弱 → 心小肠失养风险 | 健康断事 |
| HLT-203 | 土元素过弱 → 脾胃失养风险 | 健康断事 |
| HLT-204 | 金元素过弱 → 肺大肠失养风险 | 健康断事 |
| HLT-205 | 水元素过弱 → 肾膀胱失养风险 | 健康断事 |
| QTB-014 | 己日 → DAILY ACTION | 其他 |
| SUY-101 | 岁运并临且主气十神为喜用(比印) → 吉信号放大 | 岁运 |
| SUY-102 | 岁运并临且主气十神为忌神(食伤财官) → 凶信号放大 | 岁运 |
| TF-101 | 偏印强于正印出玄学天赋;偏印不可临正官 | 桃花 |
| TF-102 | 印食伤需相融(燥土印×寒水食伤则相斥) | 桃花 |

**关键问题**：
- 这些规则没有原典授权依据
- 它们是项目开发者自己编写的工程种子规则
- 其中 HLT-201~205 使用了"元素过弱"这个 Semantic State，而这个状态的阈值可能在代码中硬编码
- 这些规则在生产中是否被评估？需要确认

### 发现 2：阈值不在 Rule 中，而在代码中

审计发现，没有 Rule 直接使用 gte/lte/gt/lt 操作符。但是，heluo_wuxing_imbalance 的阈值在 signal_engine.py 中硬编码：

```python
# signal_engine.py 行 47-49
_WUXING_OVER_THRESHOLD = 0.30  # >30% 为过旺
_WUXING_UNDER_THRESHOLD = 0.10  # <10% 为不及
```

然后，HL-101 等 Rule 使用了 heluo_wuxing_imbalance == "over" 作为条件。

**关键问题**：
- 阈值 0.30 和 0.10 是从哪里来的？
- 是原典依据？盲派传统？还是项目开发者自己定的？
- 这些阈值没有在 Rule 中显式声明，更难审计
- 这是一个隐藏的授权问题

### 发现 3：51 条 Draft 规则不应在生产中使用

status = "draft" 的规则有 51 条，包括：
- DTS-101~107（滴天髓）
- GW-101~104（鬼谷子）
- HL-101~121（河洛）
- 等等

**关键问题**：
- 这些 Draft 规则在生产中是否被评估？
- RuleLoader 是否过滤了 status != "active" 的规则？
- 如果 Draft 规则被评估，那是一个严重的治理问题

### 发现 4：只有 10 条 validated 规则

status = "validated" 的规则只有 10 条。

**关键问题**：
- 这 10 条规则的验证标准是什么？
- 是原典验证？还是测试通过？
- 验证过程是否可追溯？

### 发现 5：60 条 PROVISIONAL 规则有来源但未验证原典

这些规则的 source.work 不是"工程种子"，但也没有完成原典级验证。

**关键问题**：
- 这些规则的来源声明是否准确？
- 例如 ZPZ-001 的 source.work = "工程种子"，但 rule_id 前缀是 ZPZ（子平真诠），这是一个矛盾
- 需要逐条验证来源声明的准确性

---

## 四、Rule 授权审计框架

### 每条 Rule 必须建立的字段

| 字段 | 说明 | 当前状态 |
|------|------|----------|
| rule_id | 规则 ID | ✅ 已有 |
| source_system | 哪个体系（子平/盲派/紫微/河洛/易经） | ⚠️ 从前缀推断，需验证 |
| source_work | 哪本经典/哪套体系 | ⚠️ 部分有，部分是"工程种子" |
| source_chapter | 哪一章 | ⚠️ 部分有 |
| source_text | 原典依据原文 | ❌ 大部分没有 |
| feature_basis | 基于什么 Fact | ⚠️ 可从 conditions 推断 |
| condition | 什么条件 | ✅ 已有 |
| threshold | 有没有阈值 | ⚠️ 不在 Rule 中，在代码中 |
| threshold_source | 阈值从哪里来 | ❌ 没有 |
| match_strategy | EXACT/SET/RANGE/GRAPH | ⚠️ 可从 op 推断 |
| semantic_output | 辨出了什么 | ✅ 已有（produces_signal_type） |
| authorization | AUTHORIZED/PROVISIONAL/UNAUTHORIZED | ⚠️ 初步分类，需逐条验证 |
| provenance | 可追溯证据 | ⚠️ evidence_refs 有，但证据本身未审计 |

### 授权等级定义

| 等级 | 含义 | 能否进入生产 |
|------|------|-------------|
| AUTHORIZED | 原典直接支持该命题，且来源可追溯 | ✅ 可以 |
| PROVISIONAL | 有相关依据，但不足以覆盖完整工程规则 | 🟡 需标注，限制使用 |
| ENGINEERING_SEED | 项目开发者自己编写，无原典来源 | 🔴 不应作为授权规则 |
| DRAFT | 草稿状态 | 🔴 不应在生产中使用 |
| UNAUTHORIZED | 找不到足够依据 | 🔴 不能进入生产 |

---

## 五、当前状态总结

### "算 → 辨 → 解"边界状态

| 层 | 状态 | 说明 |
|----|------|------|
| 算（Calculation） | 🟡 继续独立证明 | BaziChart 混合 DTO，但下游未消费 Semantic State |
| Fact → RuleContext | ✅ 干净 | build_rule_context() 只消费 Calculation Fact |
| RuleContext → RuleMatcher | ✅ 工程链成立 | 支持多种操作符 |
| **Rule 授权** | 🔴 **未审计，当前最高优先级** | 136 条中无一条完成原典级授权 |
| Rule → Signal | ✅ 工程上可运行 | 但语义正确性未证明 |
| Signal → Cross | ✅ 干净 | CrossAnalyzer 只消费 Signal |
| Cross → SIR | ✅ 干净 | CanonicalContent 只使用 bazi.day_master |
| 解 | ⏸️ 冻结 | 不碰 |

### Rule 授权审计结果

| 项目 | 数量 | 说明 |
|------|------|------|
| 总 Rule 数 | 136 | |
| active | 75 | 生产中活跃 |
| draft | 51 | 草稿，不应在生产中使用 |
| validated | 10 | 已验证（但验证标准未审计） |
| PROVISIONAL | 60 | 有来源但未验证原典 |
| ENGINEERING_SEED | 15 | 工程种子规则，无原典来源 |
| UNAUTHORIZED | 10 | 未授权 |
| 直接使用阈值操作符 | 0 | 但阈值在代码中硬编码 |
| 完成原典级授权 | 0 | 无一条完成 |

---

## 六、下一步建议

### P0-2.3.1：RuleLoader 生产过滤确认（高优先级）

目标：确认 RuleLoader 是否过滤了 status != "active" 的规则，确保 Draft 规则不在生产中被评估。

### P0-2.3.2：代码中硬编码阈值审计（高优先级）

目标：审计 signal_engine.py 和其他代码中硬编码的阈值（如 _WUXING_OVER_THRESHOLD = 0.30），确认这些阈值的来源和授权状态。

### P0-2.3.3：工程种子规则隔离（高优先级）

目标：将 15 条 ENGINEERING_SEED 规则标记为未授权，确保它们不在生产中作为授权规则使用。

### P0-2.3.4：逐条 Rule 原典验证（高优先级，长期工作）

目标：对 60 条 PROVISIONAL 规则逐条进行原典验证，确认来源声明的准确性，以及是否有原典直接支持。

### P0-3：Boundary Cases（高优先级）

目标：建立边界测试用例，验证计算引擎在边界情况下的正确性。

### P0-4：Calculation Golden Dataset（高优先级）

目标：建立计算 Golden Dataset，验证 Bazi Calculation 的正确性。

---

## 七、审计总结

### 本次审计的核心发现

1. 🔴 **136 条 Rule 中，没有一条完成原典级授权**
   - 60 条 PROVISIONAL（有来源但未验证原典）
   - 15 条 ENGINEERING_SEED（工程种子，无原典来源）
   - 51 条 DRAFT（草稿状态）
   - 10 条 UNAUTHORIZED

2. 🔴 **15 条工程种子规则无原典来源**
   - source.work = "工程种子"
   - 这些规则是项目开发者自己编写的
   - 不应作为授权规则在生产中使用

3. 🔴 **阈值不在 Rule 中，而在代码中**
   - 没有 Rule 直接使用 gte/lte/gt/lt 操作符
   - 但是 heluo_wuxing_imbalance 的阈值（0.30/0.10）在 signal_engine.py 中硬编码
   - 这些阈值的来源和授权状态未审计

4. 🟡 **51 条 Draft 规则不应在生产中使用**
   - 需要确认 RuleLoader 是否过滤了 status != "active" 的规则

5. 🟡 **只有 10 条 validated 规则**
   - 验证标准未审计
   - 验证过程是否可追溯未确认

### 当前裁决

| 项目 | 状态 |
|------|------|
| 算 → Fact | 🟡 继续独立证明 |
| Fact → RuleContext | ✅ 干净 |
| RuleContext → RuleMatcher | ✅ 工程链成立 |
| **Rule 授权** | 🔴 **未审计，无一条完成原典级授权** |
| Rule → Signal | ✅ 工程上可运行，语义正确性未证明 |
| "辨准" | 🔴 **未通过**：数据入口正确，但 Rule 授权未建立 |

### 最重要的一句话

dee101a 只通过了"辨的输入边界"这一关。

现在我们已经基本搞清楚：算给辨什么。

下一步必须搞清楚：辨凭什么。

而 P0-2.3 的审计结果表明：目前 136 条 Rule 中，没有一条完成原典级授权。

这意味着："辨准"这一层还远远没有建立起来。

等 Rule Authorization 这一层真正建立起来，我们才有资格说：算准 → 辨有依据。

然后再去验证：辨准。

最后才轮到：解准。

这条顺序不要再倒。

---

*本报告是 P0-2.3 RULE AUTHORIZATION AUDIT 的成果。通过逐条审计 136 条 Rule，确认没有一条完成原典级授权；15 条工程种子规则无原典来源；51 条 Draft 规则不应在生产中使用；阈值不在 Rule 中而在代码中硬编码。"辨准"这一层还远远没有建立起来。下一步需要审计 RuleLoader 生产过滤、代码中硬编码阈值、工程种子规则隔离，以及逐条 Rule 原典验证。*
