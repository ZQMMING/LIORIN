# P0-2.7.1C 五部经典取证规则谱系 — Evidence Taxonomy

> **设计时间**：2026-08-29
> **基于 commit**：`fa328d6`（P0-2.7.1B Evidence Derivation Vertical Slice）
> **目标**：系统性拆解五部经典的"取证规则"，不是继续堆代码
> **核心原则**：先搞清楚五部经典分别"看什么"，再谈怎么辨证

---

## 一、为什么需要这个谱系

### P0-2.7.1B 已经证明的

P0-2.7.1B（日主根气垂直切片）已经证明：

```
Canonical Fact → Relation → Evidence Derivation（经典授权）→ Judgment Logic → State
```

这条工程链路是成立的。一个证据可以被工程化。

### 但还没有证明的

**五部经典究竟根据哪些事实、哪些关系取哪些证？**

现在如果急着写 strength_engine.py，就会犯老错误：
- 凭印象写一个"得令+得地+得势=强"的算法
- 而不是先搞清楚：五部经典各自看什么、怎么取证、哪些证可以组合

### 核心问题转换

以前我们问：
> 五部经典怎么判断身强身弱？

现在应该问：
> 五部经典从哪些"算出来的事实/关系"取证？

这两个问题完全不同。第一个是"怎么判断"，第二个是"看什么"。

**只有先搞清楚"看什么"，才能正确实现"怎么判断"。**

---

## 二、核心框架：经典取证七元组

每一条经典取证规则，都必须回答这 7 个问题：

| 层级 | 问题 | 示例 |
|------|------|------|
| 1. 经典 | 哪部经典？ | 《滴天髓》 |
| 2. 辨证目标 | 针对什么辨证目标？ | 日主旺衰 |
| 3. 观察维度 | 从哪个维度观察？ | 得令 / 得地 / 得势 |
| 4. 所需 Fact | 需要哪些算出来的事实？ | 日主、月令、藏干 |
| 5. 所需 Relation | 需要哪些结构关系？ | CONTAINS / ROOT_PRESENT |
| 6. Evidence | 产生什么证据？ | ROOT_PRESENT / MAIN_QI_ROOT |
| 7. 组合方式 | 证据如何组合？ | 单独 / AND / OR / 优先级 |

### 完整链路

```
经典
  ↓
辨证目标
  ↓
观察维度
  ↓
所需 Fact（算出来的）
  ↓
所需 Relation（结构关系）
  ↓
Evidence（经典授权的局部证据）
  ↓
Evidence Combination（证据组合逻辑）
  ↓
Judgment State（辨证状态）
```

---

## 三、五部经典取证谱系总览

### 3.1 《滴天髓》

**核心定位**：气势 / 旺衰 / 生克制化 / 流通 / 清浊 / 寒暖燥湿

**取证总原则**：
- 强调"不可一端论"，局部证据不能直接等于整体判断
- 重视气势流通、清浊、寒暖燥湿
- 体用关系灵活（日主为体 / 提纲为体 / 四柱为体 / 化神为体 / 岁运为用）

| 辨证目标 | 观察维度 | 所需 Fact | 所需 Relation | Evidence | 组合方式 | 授权状态 |
|---------|---------|----------|-------------|----------|---------|---------|
| 日主旺衰 | 得令 | 日主、月令、十二长生 | GROWTH_STAGE / SEASONAL_ALIGNMENT | SEASONAL_SUPPORT | 与得地、得势组合 | 🟡 PARTIAL |
| 日主旺衰 | 得地 | 日主、地支、藏干 | CONTAINS / ROOT_PRESENT | ROOT_PRESENT / MAIN_QI_ROOT | 与得令、得势组合 | 🟢 AUTHORIZED（根气存在）/ 🟡 PARTIAL（本气根强） |
| 日主旺衰 | 得势 | 日主、天干、十神 | TEN_GOD_RELATION / QI_SUPPORT | RESOURCE_SUPPORT / PEER_SUPPORT | 与得令、得地组合 | 🟡 PARTIAL |
| 日主旺衰 | 受制 | 日主、官杀、十神 | TEN_GOD_RELATION / CONTROL | OFFICER_CONTROL / SEVEN_KILL_CONTROL | 制约证据，与支持证据对冲 | 🟡 PARTIAL |
| 日主旺衰 | 泄耗 | 日主、食伤、财星、十神 | TEN_GOD_RELATION / DRAIN | OUTPUT_DRAIN / WEALTH_DRAIN | 泄耗证据，与支持证据对冲 | 🟡 PARTIAL |
| 气势流通 | 五行流通 | 四柱五行、生克 | WUXING_GENERATES / WUXING_CONTROLS | FLOW_SMOOTH / FLOW_BLOCKED | 整体气势判断 | 🔴 NOT_AUTHORIZED（需深入原典） |
| 清浊 | 清纯 / 混杂 | 十神、格局 | TEN_GOD_RELATION | PURE / MIXED | 格局质量判断 | 🔴 NOT_AUTHORIZED |
| 寒暖燥湿 | 气候状态 | 月令、五行、方位 | CLIMATE_STATE | COLD / WARM / DRY / WET | 调候辨证 | 🔴 NOT_AUTHORIZED（主要归穷通宝鉴） |
| 体用 | 体用关系 | 日主、月令、化神、岁运 | BODY_USE_RELATION | BODY_DAY_MASTER / BODY_MONTH_COMMAND | 灵活体用结构 | 🔴 NOT_AUTHORIZED |

**《滴天髓》取证特点**：
1. 强调多证据组合，反对单证据下结论
2. 局部证据（得令/得地/得势）都是 SUPPORT，但需要组合
3. 制约证据（官杀/食伤/财星）都是 CONSTRAINT，与支持证据对冲
4. 气势、清浊、体用是更高维度的观察，需要深入原典

---

### 3.2 《子平真诠》

**核心定位**：月令 / 格局 / 用神 / 十干得地 / 成败 / 救应

**取证总原则**：
- 以月令为核心，格局从月令出
- 重视格局的成败、救应、变化
- 十干得地有明确论述
- 用神、相神、忌神、仇神的关系

| 辨证目标 | 观察维度 | 所需 Fact | 所需 Relation | Evidence | 组合方式 | 授权状态 |
|---------|---------|----------|-------------|----------|---------|---------|
| 十干得地 | 根气存在 | 日主、地支、藏干 | CONTAINS / ROOT_PRESENT | ROOT_PRESENT | 单独证据（结构事实） | 🟢 AUTHORIZED |
| 十干得地 | 得地语义 | 日主、月令、地支 | ROOT_PRESENT / SEASONAL_ALIGNMENT | DE_DI_SUPPORT | 与得令组合 | 🟡 PARTIAL |
| 格局 | 月令主气 | 月令、藏干、十神 | MONTH_COMMAND_TEN_GOD | PATTERN_CANDIDATE | 格局候选 | 🟡 PARTIAL |
| 格局 | 成格条件 | 月令、透干、根气 | TEN_GOD_RELATION / ROOT_PRESENT | PATTERN_SUCCESS | 多条件组合 | 🔴 NOT_AUTHORIZED |
| 格局 | 破格条件 | 冲、刑、害、克 | BRANCH_CLASH / TEN_GOD_CONTROL | PATTERN_DAMAGE | 破坏证据 | 🔴 NOT_AUTHORIZED |
| 格局 | 救应条件 | 印制伤、财生官等 | TEN_GOD_RELATION / RESCUE | PATTERN_RESCUE | 救应证据 | 🔴 NOT_AUTHORIZED |
| 用神 | 用神选择 | 格局、日主、喜忌 | PATTERN_STATE / STRENGTH_STATE | YONG_SHEN | 依赖格局和旺衰 | 🔴 NOT_AUTHORIZED |
| 相神 | 相神辅助 | 用神、格局 | YONG_SHEN_RELATION | XIANG_SHEN | 辅助用神 | 🔴 NOT_AUTHORIZED |
| 十神配合 | 十干配合性情 | 天干、五合 | STEM_COMBINE | FIVE_COMBINE_PAIR | 配对事实 | 🟢 AUTHORIZED（配对）/ 🟡 PARTIAL（合化） |
| 十神配合 | 合而不合 | 五合、争合、妒合 | STEM_COMBINE / COMPETE | COMBINE_NOT_HUA | 条件判断 | 🟡 PARTIAL |

**《子平真诠》取证特点**：
1. 以月令为核心，格局从月令出
2. 十干得地有明确论述（已验证 AUTHORIZED）
3. 格局的成败、救应是核心，但需要深入原典逐条授权
4. 五合配对是结构事实（AUTHORIZED），但合化条件需要进一步验证

---

### 3.3 《穷通宝鉴》

**核心定位**：月令 / 调候 / 寒暖 / 燥湿 / 五行时令状态

**取证总原则**：
- 以日干 × 月令为二维矩阵
- 重视寒暖燥湿的调节
- 每个格子有明确的调候用神
- 但需要检查所需五行是否出现、有根、可用、受阻或过量

| 辨证目标 | 观察维度 | 所需 Fact | 所需 Relation | Evidence | 组合方式 | 授权状态 |
|---------|---------|----------|-------------|----------|---------|---------|
| 气候状态 | 寒暖 | 月令、季节、五行 | CLIMATE_STATE | COLD / WARM | 调候基础 | 🟡 PARTIAL |
| 气候状态 | 燥湿 | 月令、方位、五行 | CLIMATE_STATE | DRY / WET | 调候基础 | 🟡 PARTIAL |
| 调候用神 | 主调候 | 日干、月令 | DAY_MASTER × MONTH | PRIMARY_TIAOHOU | 二维查表 | 🟡 PARTIAL |
| 调候用神 | 次调候 | 日干、月令、气候 | DAY_MASTER × MONTH × CLIMATE | SECONDARY_TIAOHOU | 辅助调候 | 🔴 NOT_AUTHORIZED |
| 调候可用性 | 调候五行出现 | 天干、地支、藏干 | WUXING_PRESENT | TIAOHOU_PRESENT | 必要条件 | 🟡 PARTIAL |
| 调候可用性 | 调候五行有根 | 调候五行、地支、藏干 | ROOT_PRESENT | TIAOHOU_ROOTED | 增强条件 | 🔴 NOT_AUTHORIZED |
| 调候可用性 | 调候五行受阻 | 调候五行、克、冲 | WUXING_CONTROL / BRANCH_CLASH | TIAOHOU_BLOCKED | 阻断条件 | 🔴 NOT_AUTHORIZED |
| 调候可用性 | 调候五行过量 | 调候五行、计数 | WUXING_COUNT | TIAOHOU_EXCESS | 过量条件 | 🔴 NOT_AUTHORIZED |
| 五行时令 | 五行旺相休囚 | 月令、五行 | SEASONAL_WUXING_STATE | WANG / XIANG / XIU / QIU / SI | 时令状态 | 🟡 PARTIAL |

**《穷通宝鉴》取证特点**：
1. 日干 × 月令 二维矩阵，高度规则化
2. 寒暖燥湿是核心观察维度
3. 调候用神不是简单"用某五行"，需要检查可用性
4. 五行旺相休囚有时令状态，但需要验证具体映射

---

### 3.4 《三命通会》

**核心定位**：格局 / 神煞 / 十神 / 生克 / 刑冲合害 / 各种组合条件

**取证总原则**：
- 内容极其丰富，是资料汇编性质
- 需要逐条拆出哪些是"辨证规则"，哪些只是资料汇编
- 大量关于五行、阴阳、生克、制化、干支、十神、刑冲合害的内容
- 适合沉淀进 Relation Knowledge + Transformation Rules

| 辨证目标 | 观察维度 | 所需 Fact | 所需 Relation | Evidence | 组合方式 | 授权状态 |
|---------|---------|----------|-------------|----------|---------|---------|
| 五行生克 | 生 | 五行、天干、地支 | WUXING_GENERATES | GENERATES | 基础关系 | 🟢 AUTHORIZED |
| 五行生克 | 克 | 五行、天干、地支 | WUXING_CONTROLS | CONTROLS | 基础关系 | 🟢 AUTHORIZED |
| 五行生克 | 制化 | 生克组合 | WUXING_GENERATES + WUXING_CONTROLS | TRANSFORMATION | 组合关系 | 🟡 PARTIAL |
| 干支关系 | 刑 | 地支 | BRANCH_PUNISHMENT | PUNISH | 关系事实 | 🟡 PARTIAL |
| 干支关系 | 冲 | 地支 | BRANCH_CLASH | CLASH | 关系事实 | 🟢 AUTHORIZED |
| 干支关系 | 合 | 天干/地支 | STEM_COMBINE / BRANCH_COMBINE | COMBINE | 关系事实 | 🟢 AUTHORIZED（配对） |
| 干支关系 | 害 | 地支 | BRANCH_HARM | HARM | 关系事实 | 🟡 PARTIAL |
| 干支关系 | 破 | 地支 | BRANCH_BREAK | BREAK | 关系事实 | 🟡 PARTIAL |
| 神煞 | 天乙贵人 | 日主、地支 | NOBLEMAN | TIANYI_GUIREN | 神煞事实 | 🟡 PARTIAL |
| 神煞 | 其他神煞 | 日主、地支、干支组合 | VARIOUS | VARIOUS_SHASHA | 神煞事实 | 🔴 NOT_AUTHORIZED（需逐条验证） |
| 十神 | 十神定义 | 日主、天干、五行、阴阳 | TEN_GOD_RELATION | TEN_GOD | 基础关系 | 🟢 AUTHORIZED |
| 十神 | 十神生克 | 十神、五行 | TEN_GOD_GENERATES / TEN_GOD_CONTROLS | TEN_GOD_INTERACTION | 组合关系 | 🟡 PARTIAL |
| 组合条件 | 各种格局组合 | 多维度 | MULTIPLE_RELATIONS | COMBINATION_PATTERN | 复杂组合 | 🔴 NOT_AUTHORIZED（需逐条验证） |

**《三命通会》取证特点**：
1. 内容极其丰富，是资料汇编，需要逐条筛选
2. 五行生克、刑冲合害等基础关系有强原典依据
3. 神煞数量众多，需要逐条验证是否进入辨证
4. 大量组合条件需要拆解，不能整体授权

---

### 3.5 《渊海子平》

**核心定位**：月令 / 格局 / 十神 / 五行生克 / 刑冲合害

**取证总原则**：
- 子平法的基础经典
- 大量关于月令、格局、十神、五行生克、刑冲合害的基础论述
- 是子平真诠的基础来源
- 需要与子平真诠对比，区分基础语义和进阶辨证

| 辨证目标 | 观察维度 | 所需 Fact | 所需 Relation | Evidence | 组合方式 | 授权状态 |
|---------|---------|----------|-------------|----------|---------|---------|
| 月令 | 月令重要性 | 月令、日主 | MONTH_COMMAND | MONTH_COMMAND_IMPORTANT | 基础原则 | 🟢 AUTHORIZED |
| 格局 | 格局从月令出 | 月令、藏干、十神 | MONTH_COMMAND_TEN_GOD | PATTERN_FROM_MONTH | 基础原则 | 🟡 PARTIAL |
| 十神 | 十神基础 | 日主、天干、五行、阴阳 | TEN_GOD_RELATION | TEN_GOD_BASIC | 基础关系 | 🟢 AUTHORIZED |
| 十神 | 十神吉凶 | 十神、格局 | TEN_GOD_RELATION / PATTERN | TEN_GOD_AUSPICIOUS | 依赖格局 | 🟡 PARTIAL |
| 五行生克 | 生克制化 | 五行、天干、地支 | WUXING_GENERATES / WUXING_CONTROLS | SHENG_KE_ZHI_HUA | 基础关系 | 🟡 PARTIAL |
| 刑冲合害 | 基础关系 | 天干、地支 | PUNISHMENT / CLASH / COMBINE / HARM | XING_CHONG_HE_HAI | 关系事实 | 🟡 PARTIAL |
| 旺相休囚 | 五行时令 | 月令、五行 | SEASONAL_WUXING_STATE | WANG_XIANG_XIU_QIU_SI | 时令状态 | 🟡 PARTIAL |
| 神煞 | 基础神煞 | 日主、地支 | NOBLEMAN / OTHERS | BASIC_SHASHA | 神煞事实 | 🟡 PARTIAL |
| 运命 | 大运流年 | 大运、流年、原局 | DAYUN / LIUNIAN_INTERACTION | YUN_MING_RELATION | 时间交互 | 🔴 NOT_AUTHORIZED |

**《渊海子平》取证特点**：
1. 子平法的基础经典，提供基础语义
2. 月令、格局、十神的基础论述有强依据
3. 与子平真诠有重叠，需要对比区分
4. 运命关系（大运流年）需要深入验证

---

## 四、跨经典取证对比

### 4.1 同一观察维度，不同经典的取证差异

| 观察维度 | 《滴天髓》 | 《子平真诠》 | 《穷通宝鉴》 | 《三命通会》 | 《渊海子平》 |
|---------|-----------|-------------|-------------|-------------|-------------|
| 月令 | 得令证据，强调不可一端论 | 格局核心，从月令出 | 调候核心，日干×月令二维 | 月令基础关系 | 月令重要性基础 |
| 根气 | 得地证据，本气根最重 | 十干得地，明确论述 | 调候五行有根 | 藏干基础关系 | 根气基础 |
| 十神 | 生克制化维度 | 格局成败核心 | 调候辅助 | 十神生克基础 | 十神基础语义 |
| 刑冲合害 | 气势流通影响 | 格局成败影响 | 调候受阻影响 | 基础关系汇编 | 基础关系 |
| 气候 | 寒暖燥湿（辅助） | 不强调 | 核心（调候） | 部分论述 | 部分论述 |

### 4.2 取证授权状态汇总

| 授权状态 | 数量（估算） | 说明 |
|---------|------------|------|
| 🟢 AUTHORIZED | ~15 | 基础关系、结构事实（五行生克、刑冲合害配对、十神定义、根气存在、月令重要性等） |
| 🟡 PARTIAL | ~35 | 有原典依据，但完整推理需进一步验证（得令/得地/得势语义、格局候选、调候用神、气候状态等） |
| 🔴 NOT_AUTHORIZED | ~30 | 需要深入原典逐条验证（格局成败、用神选择、体用关系、气势流通、清浊、运命关系等） |
| 总计 | ~80 | 五部经典取证规则总数（估算） |

---

## 五、优先级排序：先做哪些取证

### 第一优先级：旺衰辨证所需证据（P0-2.7.1C.1）

因为旺衰是第一个要验证的整体辨证目标，需要先把它的证据谱系做完整。

| 证据 | 经典 | 当前状态 | 下一步 |
|------|------|---------|--------|
| ROOT_PRESENT（根气存在） | 子平真诠 | 🟢 AUTHORIZED | ✅ 已完成（P0-2.7.1B） |
| MAIN_QI_ROOT（本气根） | 滴天髓 | 🟡 PARTIAL → QUALIFIED | ✅ 已修复（推理强度≤授权强度） |
| SEASONAL_SUPPORT（得令） | 滴天髓/子平真诠 | 🟡 PARTIAL | ⏳ 下一步实现 |
| RESOURCE_SUPPORT（透印） | 滴天髓 | 🟡 PARTIAL | ⏳ 待实现 |
| PEER_SUPPORT（透比劫） | 滴天髓 | 🟡 PARTIAL | ⏳ 待实现 |
| OFFICER_CONTROL（官杀制约） | 滴天髓 | 🟡 PARTIAL | ⏳ 待实现 |
| OUTPUT_DRAIN（食伤泄） | 滴天髓 | 🟡 PARTIAL | ⏳ 待实现 |
| WEALTH_DRAIN（财星耗） | 滴天髓 | 🟡 PARTIAL | ⏳ 待实现 |

### 第二优先级：格局辨证所需证据（P0-2.7.1C.2）

| 证据 | 经典 | 当前状态 | 下一步 |
|------|------|---------|--------|
| PATTERN_CANDIDATE（格局候选） | 子平真诠 | 🟡 PARTIAL | ⏳ 待实现 |
| PATTERN_SUCCESS（成格） | 子平真诠 | 🔴 NOT_AUTHORIZED | ⏳ 深入原典 |
| PATTERN_DAMAGE（破格） | 子平真诠 | 🔴 NOT_AUTHORIZED | ⏳ 深入原典 |
| PATTERN_RESCUE（救应） | 子平真诠 | 🔴 NOT_AUTHORIZED | ⏳ 深入原典 |

### 第三优先级：调候辨证所需证据（P0-2.7.1C.3）

| 证据 | 经典 | 当前状态 | 下一步 |
|------|------|---------|--------|
| CLIMATE_STATE（气候状态） | 穷通宝鉴 | 🟡 PARTIAL | ⏳ 待实现 |
| PRIMARY_TIAOHOU（主调候） | 穷通宝鉴 | 🟡 PARTIAL | ⏳ 待实现 |
| TIAOHOU_PRESENT（调候出现） | 穷通宝鉴 | 🟡 PARTIAL | ⏳ 待实现 |

---

## 六、核心原则总结

### 6.1 推理强度 ≤ 原典授权强度

这是整个五部经典取证体系的核心原则：

| 原典授权强度 | 系统最大输出强度 |
|------------|----------------|
| AUTHORIZED（原典明确说 A） | CONFIRMED A |
| PARTIAL（原典明确 A，工程推导 A→B） | QUALIFIED B（不能 CONFIRMED） |
| INFERRED（体系推导，非原典直接命题） | 不能进入生产辨证 |
| NOT_AUTHORIZED（找不到足够依据） | 直接禁止 |

### 6.2 准入规则

```
AUTHORIZED     → 可以进入 PROVEN Judgment Asset
PARTIAL        → 只能进入 RESEARCH / CANDIDATE，输出 QUALIFIED
INFERRED       → 不能进入生产辨证
NOT_AUTHORIZED → 直接禁止
```

**PARTIAL ≠ 可以执行。PARTIAL = 可以研究、可以测试，但不能作为生产级确定辨证依据。**

### 6.3 算、关系、证据、辨证严格分层

```
Canonical Fact（算）→ 只负责客观计算结果
    ↓
Relation（关系）→ 只描述结构关系（CONTAINS / ROOT_PRESENT / CLASH 等）
    ↓
Evidence（证据）→ 针对辨证目标的局部证据，必须有经典授权
    ↓
Judgment（辨证）→ 某体系按照原典逻辑组织 Evidence 得到 State
```

**Judgment 不得反向修改前面的层。**

### 6.4 互补不比较

不同经典的取证结果：
- 不投票
- 不平均
- 不比较谁分数高
- 通过 exclusivity_group 隔离
- 并行输出结构化 State

---

## 七、下一步行动

### 立即执行（P0-2.7.1C.1）

**实现旺衰辨证的完整证据谱系**：

1. ✅ ROOT_PRESENT（根气存在）— 已完成
2. ✅ MAIN_QI_ROOT（本气根）— 已完成（PARTIAL → QUALIFIED）
3. ⏳ SEASONAL_SUPPORT（得令）— 下一步实现
4. ⏳ RESOURCE_SUPPORT（透印）— 待实现
5. ⏳ PEER_SUPPORT（透比劫）— 待实现
6. ⏳ OFFICER_CONTROL（官杀制约）— 待实现
7. ⏳ OUTPUT_DRAIN（食伤泄）— 待实现
8. ⏳ WEALTH_DRAIN（财星耗）— 待实现

每个证据都按照 P0-2.7.1B 的模式：
- Canonical Fact → Relation → Evidence Derivation（经典授权）→ Judgment Logic → State
- 明确经典来源、原文、授权级别
- 严格遵守"推理强度 ≤ 原典授权强度"

### 然后执行（P0-2.7.2）

**整体旺衰辨证**：
- 当所有局部证据都建立后
- A（得令）+ B（得地）+ C（得势）+ D（受制）+ E（泄耗）
- ↓
- 整体旺衰辨证（滴天髓逻辑）

### 后续执行（P0-2.7.3）

**推广到其他辨证目标**：
- 格局辨证（子平真诠）
- 调候辨证（穷通宝鉴）
- 体用辨证（滴天髓）
- 关系转化辨证（三命通会）

---

## 八、总结

### 本次谱系的核心成果

1. ✅ **建立了经典取证七元组框架**：经典 → 辨证目标 → 观察维度 → 所需 Fact → 所需 Relation → Evidence → 组合方式
2. ✅ **系统性拆解了五部经典的取证规则**：滴天髓（~10 条）、子平真诠（~10 条）、穷通宝鉴（~9 条）、三命通会（~14 条）、渊海子平（~9 条）
3. ✅ **明确了每条证据的授权状态**：AUTHORIZED / PARTIAL / NOT_AUTHORIZED
4. ✅ **建立了"推理强度 ≤ 原典授权强度"原则**：PARTIAL 只能输出 QUALIFIED，不能 CONFIRMED
5. ✅ **建立了准入规则**：AUTHORIZED → PROVEN，PARTIAL → RESEARCH/CANDIDATE，INFERRED/NOT_AUTHORIZED → 禁止
6. ✅ **跨经典取证对比**：同一观察维度，不同经典的取证差异
7. ✅ **优先级排序**：先做旺衰证据，再做格局，再做调候

### 最重要的一句话

> **下一步最重要的工作，不是继续堆代码。是先把五部经典的"取证规则"系统性拆出来。因为我们现在已经知道代码可以装得下辨证。接下来真正困难、也是最核心的问题变成：五部经典究竟根据哪些事实、哪些关系取哪些证；哪些证可以组合；哪些证只是局部状态；什么情况下才允许从这些证进入更高一级的辨证。**

这个谱系就是对这个问题的系统性回答。

---

*本设计文档是 P0-2.7.1C 五部经典取证规则谱系的成果。通过建立经典取证七元组框架，系统性拆解五部经典（滴天髓、子平真诠、穷通宝鉴、三命通会、渊海子平）的取证规则，明确每条证据的授权状态，建立"推理强度 ≤ 原典授权强度"原则和准入规则，为后续旺衰、格局、调候等辨证目标的实现提供了清晰的取证路线图。下一步是按照这个谱系，先实现旺衰辨证的完整证据谱系（得令、得势、受制、泄耗），然后才进入整体旺衰辨证。*
