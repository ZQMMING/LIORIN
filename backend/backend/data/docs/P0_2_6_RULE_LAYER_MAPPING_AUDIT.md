# P0-2.6 RULE LAYER MAPPING AUDIT — Rule 层级映射审计

> **审计时间**：2026-08-29
> **审计目标**：把当前 wisdom 里的 136 条 Rule 全部映射到 Fact、Relation、Evidence、Judgment 四类里，看看究竟多少其实应该是关系规则、多少是证据生成规则、多少才真正属于五部经典辨证规则
> **基于 commit**：`d3fe138`
> **核心原则**：同源事实，不同辨法；共享关系，不共享结论。

---

## 一、核心结论

### 🔴 最终裁决：136 条 Rule 中，36 条（26.5%）应该迁移出 Rule 层；只有 2 条（1.5%）是真正的 Evidence 层规则；94 条（69.1%）被归类为 Judgment，但其中很多实际上是单一证据 → 直接结论，没有真正的综合辨证

**关键证据**：

| 层级 | 数量 | 占比 | 说明 |
|------|------|------|------|
| FACT | 0 | 0% | 没有纯事实计算规则（正确，Fact 应该在代码中确定性计算） |
| RELATION | 34 | 25.0% | **应该迁移到 relations/ 层** |
| EVIDENCE | 2 | 1.5% | 只有 2 条是真正的证据生成规则 |
| JUDGMENT | 94 | 69.1% | 被归类为辨证判断，但很多是单一证据 → 直接结论 |
| UNCERTAIN | 6 | 4.4% | 无法确定层级，需要人工审查 |
| **需要迁移** | **36** | **26.5%** | RELATION + EVIDENCE |

---

## 二、各层级详细分析

### 第一层：FACT（0 条，0%）

**状态**：✅ 正确

**说明**：
- 没有 Rule 被归类为纯事实计算规则
- 这是正确的，因为 Fact 应该是确定性计算，在代码中实现（bazi_engine.py 等），不应该是 Rule
- Fact 包括：四柱、日主、藏干、十神、五行、十二长生等

**问题**：
- 虽然没有 FACT 层的 Rule，但需要确认所有 Fact 计算都在代码中正确实现，并且有完整的测试覆盖

---

### 第二层：RELATION（34 条，25.0%）

**状态**：🔴 应该迁移

**说明**：
- 34 条 Rule 被归类为关系计算规则
- 这些 Rule 描述的是两个或多个 Fact 之间的关系（生克、合冲刑害、十神等）
- 它们应该迁移到 relations/ 层，由 Relation Engine 统一处理，而不是在 Rule 层

**代表性 Rule**：
- CRR-103: 流年伤官当值 → 事业风险/变动
- CRR-104: 流年偏印当值 → 事业新机会/变动
- HH-101: 合化需得令（化神得月令旺气）
- HH-103: 合而能化才论化神，否则仅合绊
- HLT-104: 巳亥冲 → 心肾疾病风险

**按状态统计**：
- active: 18
- draft: 6
- validated: 10

**迁移目标**：
- relations/wuxing_relation.py（五行生克）
- relations/yin_yang_relation.py（阴阳关系）
- relations/ten_god_relation.py（十神关系）
- relations/stem_relation.py（天干关系：五合等）
- relations/branch_relation.py（地支关系：六合、六冲、三合、三会、三刑、六害、相破等）
- relations/transformation.py（合化、制化等）

---

### 第三层：EVIDENCE（2 条，1.5%）

**状态**：🔴 严重不足

**说明**：
- 只有 2 条 Rule 被归类为证据生成规则
- 这意味着绝大多数 Rule 直接从 Fact/Relation 跳到了 Judgment，没有经过 Evidence 层
- 这正是"把 Evidence 当成 Judgment"的核心问题

**代表性 Rule**：
- ZPZ-113: 比肩当令且主气透干 → RELATION（司权显性）
- ZPZ-114: 劫财当令且主气透干 → RELATION（司权显性）

**按状态统计**：
- active: 2

**问题**：
- 旺衰辨识需要的 Evidence 包括：得令、得地、得势、受制、生扶、克泄耗、制化等
- 但当前只有 2 条 Evidence 层的 Rule
- 绝大多数 Rule 直接使用 Fact/Relation 作为条件，然后直接宣布 Judgment
- 例如：DTS-101 直接使用 month_hidden_main_ten_god in [印比劫] 作为条件，然后直接宣布 SUPPORT（身强）
- 正确的做法应该是：month_hidden_main_ten_god in [印比劫] → 得令 Evidence → 然后由 Strength Judgment 综合所有 Evidence 后判断身强/身弱

**迁移目标**：
- evidence/evidence.py（Evidence 数据结构）
- evidence/derivation.py（Evidence 推导规则）
- evidence/provenance.py（Evidence 来源追踪）

---

### 第四层：JUDGMENT（94 条，69.1%）

**状态**：🟡 数量最多，但质量参差不齐

**说明**：
- 94 条 Rule 被归类为辨证判断规则
- 这是数量最多的层级
- 但其中很多实际上是单一证据 → 直接结论，没有真正的综合辨证

**代表性 Rule**：
- CRR-101: 流年正官/七杀当值 → 事业变动压力
- CRR-102: 流年正印/偏印当值 → 事业助力
- DTS-101: 日主得令（月支主气生扶）→ SUPPORT
- DTS-102: 日主失令（月支主气克泄耗）→ CONSTRAINT
- DTS-103: 日支通根（主气比劫）→ SUPPORT

**按状态统计**：
- active: 49
- draft: 45

**问题**：
1. **很多是单一证据 → 直接结论**：例如 DTS-101~105，只有一个条件就直接宣布身强/身弱
2. **没有真正的综合辨证**：即使是多条件组合，也只是简单的 AND 逻辑，没有 Evidence 之间的关系处理
3. **没有按体系分类**：所有 Rule 混在一个 Pool 中，没有区分滴天髓、子平真诠、穷通宝鉴等不同体系的辨证策略
4. **没有 Judgment Strategy**：没有定义必要条件、充分条件、组合条件、抵消条件、优先条件、转化条件、例外条件等辨证策略

**迁移目标**：
- judgment/base.py（Judgment 基类）
- judgment/strength.py（旺衰辨证）
- judgment/pattern.py（格局辨证）
- judgment/tiaohou.py（调候辨证）
- judgment/ti_yong.py（体用辨证）
- judgment/transformation.py（制化辨证）
- classics/ditiansui/（滴天髓辨证策略）
- classics/ziping_zhenquan/（子平真诠辨证策略）
- classics/qiongtong_baojian/（穷通宝鉴辨证策略）
- classics/sanming_tonghui/（三命通会辨证策略）
- classics/yuanhai_ziping/（渊海子平辨证策略）

---

### 第五层：UNCERTAIN（6 条，4.4%）

**状态**：🟡 需要人工审查

**说明**：
- 6 条 Rule 无法确定层级，需要人工审查

**代表性 Rule**：
- QTB-014: 己日 → DAILY ACTION
- ZPZ-102: 比劫当令 → RELATION
- ZW-405: 四化·化禄 → RESOURCE
- ZW-406: 四化·化权 → ACTION
- ZW-407: 四化·化科 → SUPPORT

**按状态统计**：
- active: 6

**问题**：
- 这些 Rule 的层级不明确，需要人工审查确定它们应该属于哪一层
- 例如 ZW-405~407（紫微四化），它们可能是 RELATION（四化是一种关系），也可能是 JUDGMENT（四化产生某种状态）

---

## 三、层级映射的核心发现

### 发现 1：没有 FACT 层的 Rule（正确）

0 条 Rule 被归类为纯事实计算规则。这是正确的，因为 Fact 应该是确定性计算，在代码中实现，不应该是 Rule。

### 发现 2：25% 的 Rule 应该迁移到 RELATION 层

34 条 Rule（25.0%）实际上是关系计算规则，应该迁移到 relations/ 层，由 Relation Engine 统一处理。

### 发现 3：只有 1.5% 的 Rule 是真正的 Evidence 层规则

只有 2 条 Rule（1.5%）是真正的证据生成规则。这意味着绝大多数 Rule 直接从 Fact/Relation 跳到了 Judgment，没有经过 Evidence 层。

这是"把 Evidence 当成 Judgment"的核心问题。

### 发现 4：69% 的 Rule 被归类为 Judgment，但质量参差不齐

94 条 Rule（69.1%）被归类为辨证判断规则。但其中很多实际上是单一证据 → 直接结论，没有真正的综合辨证。

### 发现 5：4.4% 的 Rule 无法确定层级

6 条 Rule（4.4%）无法确定层级，需要人工审查。

---

## 四、正确的四层架构应该是什么

### 目标架构

```
算
↓
Calculation Facts（在代码中确定性计算，不是 Rule）
↓
Relation Engine（relations/ 层，统一处理所有关系）
├── 五行关系（生克泄耗）
├── 阴阳关系（同异）
├── 十神关系（派生关系）
├── 天干关系（五合等）
├── 地支关系（六合、六冲、三合、三会、三刑、六害、相破等）
└── 转化关系（合化、制化等）
↓
Evidence Derivation（evidence/ 层，从 Fact 和 Relation 中提取证据）
├── 得令证据
├── 得地证据
├── 得势证据
├── 受制证据
├── 生扶证据
├── 克泄耗证据
├── 制化证据
└── 其他证据
↓
Judgment Strategy（judgment/ + classics/ 层，基于 Evidence 进行综合辨证）
├── 滴天髓：气势/体用辨证
├── 子平真诠：格局辨证
├── 穷通宝鉴：调候辨证
├── 三命通会：关系/转化辨证
└── 渊海子平：传统语义辨证
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

1. **Fact 不是 Rule**：Fact 是确定性计算，在代码中实现，有完整的测试覆盖
2. **Relation 不是 Rule**：Relation 是两个或多个 Fact 之间的关系，由 Relation Engine 统一处理
3. **Evidence 不是 Judgment**：Evidence 是从 Fact 和 Relation 中提取的证据，不是最终判断
4. **Judgment 需要 Strategy**：Judgment 基于 Evidence 进行综合辨证，需要定义必要条件、充分条件、组合条件、抵消条件、优先条件、转化条件、例外条件等
5. **五部经典是五种辨证策略**：不是五套计算器，也不是五套 Rule，而是五种不同的辨证策略
6. **同源事实，不同辨法；共享关系，不共享结论**

---

## 五、迁移计划

### 第一阶段：RELATION 层迁移（34 条）

目标：将 34 条 RELATION 层的 Rule 迁移到 relations/ 层。

步骤：
1. 建立 relations/ 目录结构
2. 实现 Relation Engine 基类
3. 实现五行关系、阴阳关系、十神关系、天干关系、地支关系、转化关系
4. 将 34 条 RELATION 层的 Rule 转换为 Relation Engine 的配置或代码
5. 删除原 Rule 文件
6. 测试验证

### 第二阶段：EVIDENCE 层建立（2 条 + 新增）

目标：建立 evidence/ 层，将 2 条 EVIDENCE 层的 Rule 迁移过去，并新增缺失的 Evidence 推导规则。

步骤：
1. 建立 evidence/ 目录结构
2. 定义 Evidence 数据结构
3. 实现 Evidence 推导规则（得令、得地、得势、受制、生扶、克泄耗、制化等）
4. 将 2 条 EVIDENCE 层的 Rule 迁移过去
5. 新增缺失的 Evidence 推导规则
6. 测试验证

### 第三阶段：JUDGMENT 层重构（94 条）

目标：将 94 条 JUDGMENT 层的 Rule 重构为 Judgment Strategy，按体系分类。

步骤：
1. 建立 judgment/ 和 classics/ 目录结构
2. 实现 Judgment Strategy 基类
3. 实现旺衰、格局、调候、体用、制化等辨证策略
4. 按体系分类（滴天髓、子平真诠、穷通宝鉴、三命通会、渊海子平）
5. 将 94 条 JUDGMENT 层的 Rule 转换为 Judgment Strategy 的配置或代码
6. 删除原 Rule 文件
7. 测试验证

### 第四阶段：UNCERTAIN 层人工审查（6 条）

目标：人工审查 6 条 UNCERTAIN 层的 Rule，确定它们应该属于哪一层。

步骤：
1. 人工审查每条 Rule
2. 确定层级
3. 迁移到对应层级
4. 测试验证

---

## 六、当前状态总结

### Rule 层级映射状态

| 层级 | 数量 | 占比 | 状态 | 迁移目标 |
|------|------|------|------|----------|
| FACT | 0 | 0% | ✅ 正确 | 不需要迁移（在代码中实现） |
| RELATION | 34 | 25.0% | 🔴 应该迁移 | relations/ |
| EVIDENCE | 2 | 1.5% | 🔴 严重不足 | evidence/ |
| JUDGMENT | 94 | 69.1% | 🟡 质量参差不齐 | judgment/ + classics/ |
| UNCERTAIN | 6 | 4.4% | 🟡 需要人工审查 | 待定 |
| **需要迁移** | **36** | **26.5%** | | |

### "算 → 辨 → 解"边界状态

| 层 | 状态 | 说明 |
|----|------|------|
| 算（Calculation） | 🟡 继续独立证明 | Fact 在代码中实现，需要完整测试覆盖 |
| Relation Engine | 🔴 缺失 | 34 条 Rule 应该迁移到这里 |
| Evidence Derivation | 🔴 严重不足 | 只有 2 条 Evidence 层的 Rule |
| Judgment Strategy | 🔴 需要重构 | 94 条 Rule 质量参差不齐，需要按体系分类 |
| "辨准" | 🔴 **未通过** | 辨识层需要重新建模 |

---

## 七、下一步建议

### P0-2.6.1：RELATION 层迁移设计（最高优先级）

目标：设计 relations/ 层的架构，包括 Relation Engine 基类、五行关系、阴阳关系、十神关系、天干关系、地支关系、转化关系。

### P0-2.6.2：EVIDENCE 层建立设计（高优先级）

目标：设计 evidence/ 层的架构，包括 Evidence 数据结构、Evidence 推导规则（得令、得地、得势、受制、生扶、克泄耗、制化等）。

### P0-2.6.3：JUDGMENT 层重构设计（高优先级）

目标：设计 judgment/ 和 classics/ 层的架构，包括 Judgment Strategy 基类、旺衰/格局/调候/体用/制化等辨证策略、按体系分类。

### P0-2.6.4：UNCERTAIN 层人工审查（高优先级）

目标：人工审查 6 条 UNCERTAIN 层的 Rule，确定它们应该属于哪一层。

### P0-3：Boundary Cases（高优先级）

目标：建立边界测试用例，验证计算引擎在边界情况下的正确性。

### P0-4：Calculation Golden Dataset（高优先级）

目标：建立计算 Golden Dataset，验证 Bazi Calculation 的正确性。

---

## 八、审计总结

### 本次审计的核心发现

1. 🔴 **25% 的 Rule 应该迁移到 RELATION 层**
   - 34 条 Rule 实际上是关系计算规则
   - 应该由 Relation Engine 统一处理，而不是在 Rule 层

2. 🔴 **只有 1.5% 的 Rule 是真正的 Evidence 层规则**
   - 只有 2 条 Evidence 层的 Rule
   - 绝大多数 Rule 直接从 Fact/Relation 跳到了 Judgment
   - 这是"把 Evidence 当成 Judgment"的核心问题

3. 🟡 **69% 的 Rule 被归类为 Judgment，但质量参差不齐**
   - 94 条 Judgment 层的 Rule
   - 很多是单一证据 → 直接结论
   - 没有真正的综合辨证
   - 没有按体系分类

4. ✅ **没有 FACT 层的 Rule（正确）**
   - Fact 应该是确定性计算，在代码中实现

5. 🟡 **4.4% 的 Rule 无法确定层级**
   - 6 条 UNCERTAIN 层的 Rule
   - 需要人工审查

### 当前裁决

| 项目 | 状态 |
|------|------|
| Fact 层 | ✅ 正确（在代码中实现） |
| Relation 层 | 🔴 缺失（34 条 Rule 应该迁移） |
| Evidence 层 | 🔴 严重不足（只有 2 条） |
| Judgment 层 | 🟡 需要重构（94 条，质量参差不齐） |
| "辨准" | 🔴 **未通过** |

### 最重要的一句话

这次 RULE LAYER MAPPING AUDIT 证明了用户之前的判断是完全正确的：

> 下一步应该是先把当前 wisdom 里的 136 条 Rule 全部映射到：Fact Relation Evidence Judgment 四类里，看看究竟多少其实应该是关系规则、多少是证据生成规则、多少才真正属于五部经典辨证规则。

审计结果显示：
- 25% 的 Rule 应该是关系规则（RELATION）
- 只有 1.5% 的 Rule 是真正的证据生成规则（EVIDENCE）
- 69% 的 Rule 被归类为辨证判断（JUDGMENT），但质量参差不齐

这意味着当前的 Rule 层混了三个不同层级的东西：关系计算、证据生成、辨证判断。需要重新分层，建立 Relation Engine、Evidence Derivation、Judgment Strategy 三层。

等这三层真正建立起来，五部经典的工程体系才能真正落地，而不是再凭理论想象写一个漂亮架构。

---

*本报告是 P0-2.6 RULE LAYER MAPPING AUDIT 的成果。通过将 136 条 Rule 映射到 Fact、Relation、Evidence、Judgment 四层，发现 25% 的 Rule 应该迁移到 RELATION 层，只有 1.5% 是真正的 Evidence 层规则，69% 被归类为 Judgment 但质量参差不齐。这证明了当前 Rule 层混了三个不同层级的东西，需要重新分层。下一步需要建立 Relation Engine、Evidence Derivation、Judgment Strategy 三层。*
