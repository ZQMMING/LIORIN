# P0-2.1.8 SignalEngine.build() 逐字段审计 — "算 → 辨"边界确认

> **审计时间**：2026-08-29
> **审计目标**：逐字段审计 SignalEngine.build() 消费的所有 BaziChart 字段，确认哪些是 Calculation Fact，哪些是 Semantic State，以及消费方式是否符合"算 → 辨"边界
> **基于 commit**：`9673c33`
> **核心问题**：命理的辨，到底是基于什么数据辨出来的？

---

## 一、核心结论

### 🟢 最终裁决：SignalEngine.build() 只消费 Calculation Fact，不消费 Semantic State；"算 → 辨"边界干净

**关键证据**：

1. **SignalEngine.build() 消费的所有 BaziChart 字段都是 Calculation Fact**
   - day_master, day_pillar, month_pillar, year_pillar, hour_pillar（四柱）
   - five_element_balance（纯五行计数比例）
   - **没有**消费 spouse_star_strength（Semantic State）
   - **没有**消费 five_element_imbalance（Semantic State）
   - **没有**消费 kong_wang（MIXED）
   - **没有**消费 spouse_star, officer_mixed, peach_blossom 等其他字段

2. **SignalEngine.build() 的消费方式符合"算 → 辨"边界**
   - 它从 Calculation Fact 构造 RuleContext
   - 然后通过 RuleMatcher 匹配规则，生成 Signal
   - 它**没有**直接消费已经"辨过"的 Semantic State
   - 它自己从 Fact 做 Semantic 判断（例如 heluo_wuxing_imbalance）

3. **five_element_balance 这条链是正确范式**
   - BaziChart.five_element_balance（纯五行计数比例，Calculation Fact）
   - ↓ SignalEngine.build()
   - ↓ 自己根据 ratio + threshold 判断
   - ↓ heluo_wuxing_imbalance（Semantic Signal）
   - ✅ 这是正确的：Fact → 辨 → Signal

4. **spouse_star_strength 未被消费，可以关闭**
   - 全仓搜索 signal_engine.py，没有发现对 spouse_star_strength 的引用
   - ✅ 这一条可以关闭

---

## 二、SignalEngine.build() 完整调用链

### 调用链

```
SignalEngine.build(bazi, ziwei, huangli, gender, theme, heluo_result)
    ↓
build_signals(bazi, ziwei, huangli, matcher, gender, theme, heluo_result)
    ↓
_build_layer_signals(matcher, bazi, ziwei, huangli, layer, gender, theme, heluo_result)
    ↓
build_rule_context(bazi, ziwei, huangli, layer, theme, heluo_result)
    ↓
    ├── extract_heluo_context(heluo_result, bazi)
    └── 直接从 bazi 构造 RuleContext 字段
    ↓
RuleContext
    ↓
RuleMatcher.match(RuleContext)
    ↓
Signal[]
```

### 关键发现

1. **SignalEngine.build() 是一个包装器**
   - 它调用 build_signals()
   - build_signals() 调用 _build_layer_signals()
   - _build_layer_signals() 调用 build_rule_context()
   - build_rule_context() 是真正消费 BaziChart 字段的地方

2. **build_rule_context() 是"算 → 辨"的边界**
   - 它从 BaziChart（Calculation Fact）构造 RuleContext
   - RuleContext 是规则匹配的输入
   - RuleMatcher 根据 RuleContext 匹配规则，生成 Signal
   - 这是正确的分层：Calculation Fact → RuleContext → Rule Matching → Signal

---

## 三、逐字段审计表

### build_rule_context() 消费的 BaziChart 字段

| BaziChart 字段 | 行号 | 分类 | 消费方式 | 是否符合"算 → 辨"边界 |
|----------------|------|------|----------|----------------------|
| `bazi.day_master` | 141, 142, 155, 177, 199 | CALCULATION_FACT | 直接使用日主 | ✅ 是 |
| `bazi.day_pillar.earthly_branch` | 143, 199 | CALCULATION_FACT | 直接使用日支 | ✅ 是 |
| `bazi.month_pillar.heavenly_stem` | 144, 163, 179 | CALCULATION_FACT | 直接使用月干 | ✅ 是 |
| `bazi.month_pillar.earthly_branch` | 145, 151, 155, 160, 187, 191, 195 | CALCULATION_FACT | 直接使用月支 | ✅ 是 |
| `bazi.year_pillar.heavenly_stem` | 146, 162, 178 | CALCULATION_FACT | 直接使用年干 | ✅ 是 |
| `bazi.year_pillar.earthly_branch` | 147 | CALCULATION_FACT | 直接使用年支 | ✅ 是 |
| `bazi.hour_pillar.heavenly_stem` | 148, 165, 180 | CALCULATION_FACT | 直接使用时干 | ✅ 是 |
| `bazi.hour_pillar.earthly_branch` | 149 | CALCULATION_FACT | 直接使用时支 | ✅ 是 |

### extract_heluo_context() 消费的 BaziChart 字段

| BaziChart 字段 | 行号 | 分类 | 消费方式 | 是否符合"算 → 辨"边界 |
|----------------|------|------|----------|----------------------|
| `bazi.month_pillar.earthly_branch` | 85-88 | CALCULATION_FACT | 判断是否生于不利时节（辰月） | ✅ 是 |
| `bazi.five_element_balance` | 90-103 | CALCULATION_FACT | 纯五行计数比例，自己根据 ratio + threshold 判断 heluo_wuxing_imbalance | ✅ 是 |

### _FOUR_BRANCHES() 消费的 BaziChart 字段

| BaziChart 字段 | 行号 | 分类 | 消费方式 | 是否符合"算 → 辨"边界 |
|----------------|------|------|----------|----------------------|
| `bazi.year_pillar.earthly_branch` | 130 | CALCULATION_FACT | 四支列表 | ✅ 是 |
| `bazi.month_pillar.earthly_branch` | 131 | CALCULATION_FACT | 四支列表 | ✅ 是 |
| `bazi.day_pillar.earthly_branch` | 132 | CALCULATION_FACT | 四支列表 | ✅ 是 |
| `bazi.hour_pillar.earthly_branch` | 133 | CALCULATION_FACT | 四支列表 | ✅ 是 |

### 未被消费的 BaziChart 字段（Semantic State / MIXED / UNKNOWN）

| BaziChart 字段 | 分类 | 是否被 SignalEngine 消费 | 说明 |
|----------------|------|--------------------------|------|
| `spouse_star_strength` | SEMANTIC_STATE | ❌ **未被消费** | score → strong/weak/rootless 阈值分类 |
| `five_element_imbalance` | SEMANTIC_STATE | ❌ **未被消费** | 基于阈值的失衡判断 |
| `kong_wang` | MIXED | ❌ **未被消费** | 空亡计算 + "力量减半"语义 |
| `spouse_star` | UNKNOWN | ❌ **未被消费** | 配偶星 |
| `spouse_star_attack` | UNKNOWN | ❌ **未被消费** | 配偶星攻击 |
| `officer_mixed` | UNKNOWN | ❌ **未被消费** | 官杀混杂 |
| `peach_blossom` | UNKNOWN | ❌ **未被消费** | 桃花 |
| `branch_clash_map` | CALCULATION_FACT | ❌ **未被消费** | 六冲表 |
| `branch_harm_map` | CALCULATION_FACT | ❌ **未被消费** | 六害表 |
| `branch_he_map` | CALCULATION_FACT | ❌ **未被消费** | 六合表 |
| `branch_sanhe_map` | CALCULATION_FACT | ❌ **未被消费** | 三合表 |
| `branch_sanxing_map` | CALCULATION_FACT | ❌ **未被消费** | 三刑表 |
| `day_branch_clash` | CALCULATION_FACT | ❌ **未被消费** | 日支冲 |
| `day_branch_harm` | CALCULATION_FACT | ❌ **未被消费** | 日支害 |
| `day_branch_main_ten_god` | CALCULATION_FACT | ❌ **未被消费** | 日支主气十神（SignalEngine 自己计算） |

---

## 四、关键发现详细分析

### 1. five_element_balance 消费方式是正确范式

```python
# signal_engine.py 行 90-103
if benming_wuxing and bazi and getattr(bazi, "five_element_balance", None):
    bazi_key = _HELUO_WUXING_TO_BASI_KEY.get(benming_wuxing)
    if bazi_key and bazi_key in bazi.five_element_balance:
        ratio = bazi.five_element_balance[bazi_key]  # 纯五行计数比例（Calculation Fact）
        if ratio > _WUXING_OVER_THRESHOLD:
            out["heluo_wuxing_imbalance"] = "over"     # 自己做 Semantic 判断
        elif ratio < _WUXING_UNDER_THRESHOLD:
            out["heluo_wuxing_imbalance"] = "under"
        else:
            out["heluo_wuxing_imbalance"] = "none"
```

**关键发现**：
- SignalEngine 消费的是 `bazi.five_element_balance`（纯五行计数比例，Calculation Fact）
- 它**没有**消费 `bazi.five_element_imbalance`（基于阈值的 Semantic State）
- 它自己根据 ratio + threshold 判断 `heluo_wuxing_imbalance`
- ✅ **这是正确的分层：Fact → 辨 → Signal**

### 2. spouse_star_strength 未被消费，可以关闭

全仓搜索 signal_engine.py，没有发现对 `spouse_star_strength` 的引用。

**关键发现**：
- SignalEngine **没有**消费 `bazi.spouse_star_strength`
- 这个 Semantic State 字段没有进入 Signal 层
- ✅ **这一条可以关闭**

### 3. five_element_imbalance 未被消费，可以关闭

全仓搜索 signal_engine.py，没有发现对 `five_element_imbalance` 的引用。

**关键发现**：
- SignalEngine **没有**消费 `bazi.five_element_imbalance`
- 它自己根据 `five_element_balance` 做判断
- ✅ **这一条可以关闭**

### 4. kong_wang 未被消费，可以关闭

全仓搜索 signal_engine.py，没有发现对 `kong_wang` 的引用。

**关键发现**：
- SignalEngine **没有**消费 `bazi.kong_wang`
- 这个 MIXED 字段没有进入 Signal 层
- ✅ **这一条可以关闭**

### 5. SignalEngine 只消费基础四柱字段

从审计结果来看，SignalEngine 只消费了以下基础 Calculation Fact 字段：
- day_master
- day_pillar.earthly_branch
- month_pillar.heavenly_stem / earthly_branch
- year_pillar.heavenly_stem / earthly_branch
- hour_pillar.heavenly_stem / earthly_branch
- five_element_balance（纯五行计数比例）

**关键发现**：
- SignalEngine 没有消费任何 Semantic State 字段
- SignalEngine 没有消费任何 MIXED 字段
- SignalEngine 只消费纯 Calculation Fact
- ✅ **"算 → 辨"边界干净**

---

## 五、"算 → 辨 → 解"完整链路确认

### 当前生产路径的完整链路

```
用户输入
    ↓
BaziEngine.compute()
    ↓
BaziChart (混合 DTO)
    ├── Calculation Fact: 四柱, 日主, 藏干, 十神, 合冲刑害, five_element_balance, kong_wang
    └── Semantic State: spouse_star_strength, five_element_imbalance ⚠️
    ↓
SignalEngine.build()  ← 【只消费 Calculation Fact，不消费 Semantic State】✅
    ↓
    消费: day_master, 四柱, five_element_balance
    不消费: spouse_star_strength, five_element_imbalance, kong_wang
    ↓
RuleContext
    ↓
RuleMatcher.match()
    ↓
Signal
    ↓
┌─────────────────────┬─────────────────────┐
↓                     ↓                     ↓
CrossAnalyzer.analyze()    _build_atomic_claims()
    ↓                     ↓
CrossResult            atomic_claims
    └─────────────────────┬─────────────────────┘
                          ↓
              CanonicalComposer.compose()
              (只使用 bazi.day_master)
                          ↓
              CanonicalContent (SIR)
```

### 关键确认

1. ✅ **算层干净**：BaziEngine 产生 Calculation Fact
2. ✅ **辨层干净**：SignalEngine 只消费 Calculation Fact，自己做 Semantic 判断
3. ✅ **跨体系干净**：CrossAnalyzer 只消费 Signal，不直接消费 BaziChart
4. ✅ **解层干净**：atomic_claims 只消费 Signal，不直接消费 BaziChart
5. ✅ **SIR 干净**：CanonicalContent 只使用 bazi.day_master，不直接复制 Semantic State
6. ⚠️ **BaziChart 混合 DTO 问题仍然存在**：但目前下游没有直接消费其 Semantic State 字段

---

## 六、当前状态总结

### "算 → 辨 → 解"边界状态

| 层 | 状态 | 说明 |
|----|------|------|
| 算（Calculation） | 🟡 继续独立证明 | BaziChart 混合 DTO，但下游未消费 Semantic State |
| 辨（Signal） | ✅ **干净** | SignalEngine 只消费 Calculation Fact，不消费 Semantic State |
| 跨体系（Cross） | ✅ **干净** | CrossAnalyzer 只消费 Signal |
| 解（Atomic Claims） | ✅ **干净** | _build_atomic_claims 只消费 Signal |
| SIR（CanonicalContent） | ✅ **干净** | 只使用 bazi.day_master |

### 已关闭的问题

| 问题 | 状态 | 说明 |
|------|------|------|
| spouse_star_strength 是否被 SignalEngine 消费？ | ✅ **已关闭** | 未被消费 |
| five_element_imbalance 是否被 SignalEngine 消费？ | ✅ **已关闭** | 未被消费 |
| kong_wang 是否被 SignalEngine 消费？ | ✅ **已关闭** | 未被消费 |
| cross_result 是否直接消费 BaziChart？ | ✅ **已关闭**（P0-2.1.7） | 只消费 Signal |
| atomic_claims 是否直接消费 BaziChart？ | ✅ **已关闭**（P0-2.1.7） | 只消费 Signal |
| CanonicalContent 是否直接复制 Semantic State？ | ✅ **已关闭**（P0-2.1.6） | 只使用 bazi.day_master |

### 仍然存在的问题

| 问题 | 状态 | 说明 |
|------|------|------|
| BaziChart 混合 DTO | 🟡 架构边界问题 | 同时承载 Calculation Fact 和 Semantic State，但目前下游未消费 Semantic State |
| Bazi Calculation 正确性 | 🟡 继续独立证明 | 需要 Golden Dataset 验证计算正确性 |
| Ziwei Signal 来源 | 🟡 后续确认 | 需要审计 ziwei_engine.extract_baseline_signal() |

---

## 七、下一步建议

### P0-2.1.9：BaziChart 字段分类与隔离文档化（低优先级）

目标：将 BaziChart 的所有字段分类为 Calculation Fact / Semantic State / MIXED / UNKNOWN，并文档化。

注意：这只是文档化，不是修改代码。BaziChart 的混合 DTO 问题目前没有造成实际污染，可以后续处理。

### P0-2.2：Ziwei Signal 来源审计（中优先级）

目标：审计 ziwei_engine.extract_baseline_signal() 是否消费了 ZiweiChart 的 Semantic State 字段。

### P0-3：Boundary Cases（高优先级）

目标：建立边界测试用例，验证计算引擎在边界情况下的正确性。

### P0-4：Calculation Golden Dataset（高优先级）

目标：建立计算 Golden Dataset，验证 Bazi Calculation 的正确性。

---

## 八、审计总结

### 本次审计的核心发现

1. ✅ **SignalEngine.build() 只消费 Calculation Fact，不消费 Semantic State**
   - 消费：day_master, 四柱, five_element_balance（纯五行计数比例）
   - 不消费：spouse_star_strength, five_element_imbalance, kong_wang

2. ✅ **five_element_balance 消费方式是正确范式**
   - Fact → 辨 → Signal
   - SignalEngine 自己根据 ratio + threshold 判断 heluo_wuxing_imbalance

3. ✅ **spouse_star_strength、five_element_imbalance、kong_wang 均未被消费，可以关闭**

4. ✅ **"算 → 辨 → 解"完整链路干净**
   - 算层：BaziEngine 产生 Calculation Fact
   - 辨层：SignalEngine 只消费 Calculation Fact，自己做 Semantic 判断
   - 跨体系：CrossAnalyzer 只消费 Signal
   - 解层：atomic_claims 只消费 Signal
   - SIR：CanonicalContent 只使用 bazi.day_master

5. 🟡 **BaziChart 混合 DTO 问题仍然存在，但目前没有造成实际污染**
   - 它同时承载 Calculation Fact 和 Semantic State
   - 但下游没有直接消费其 Semantic State 字段
   - 这是一个架构边界问题，不是当前生产链已经坏掉

### 当前裁决

| 项目 | 状态 |
|------|------|
| SignalEngine.build() 字段消费 | ✅ **干净，只消费 Calculation Fact** |
| spouse_star_strength 消费 | ✅ **未被消费，已关闭** |
| five_element_imbalance 消费 | ✅ **未被消费，已关闭** |
| kong_wang 消费 | ✅ **未被消费，已关闭** |
| "算 → 辨"边界 | ✅ **干净** |
| "算 → 辨 → 解"完整链路 | ✅ **干净** |
| BaziChart 混合 DTO | 🟡 架构边界问题，当前未造成污染 |
| Bazi Calculation 正确性 | 🟡 继续独立证明 |

---

*本报告是 P0-2.1.8 SignalEngine.build() 逐字段审计的成果。通过逐字段审计，确认 SignalEngine.build() 只消费 Calculation Fact（day_master, 四柱, five_element_balance），不消费 Semantic State（spouse_star_strength, five_element_imbalance, kong_wang）。five_element_balance 的消费方式是正确范式（Fact → 辨 → Signal）。"算 → 辨 → 解"完整链路干净。BaziChart 混合 DTO 问题仍然存在，但目前下游没有直接消费其 Semantic State 字段，没有造成实际污染。*
