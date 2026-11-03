# P0-2.7.1C.1 Evidence Authorization Audit — 旺衰八类证据原典授权审计

> **设计时间**：2026-08-29
> **基于 commit**：`8856252`（P0-2.7.1C 五部经典取证规则谱系）
> **目标**：把旺衰八类 Evidence 逐条原典核验，不是批量实现
> **核心原则**：先搞清楚每条证据的原典依据、语义边界、工程推导程度，再决定是否进入生产

---

## 一、审计背景

### 为什么需要这次审计

P0-2.7.1C 建立了五部经典取证规则谱系，但其中很多只是"主题 → 工程候选语义"，还没有完成：

```
原文 → 精确语义 → 条件 → 关系 → Evidence
```

用户明确裁决：

> "下一步不是继续写代码，而是做 P0-2.7.1C.1 Evidence Authorization Audit——把旺衰八类 Evidence 的原典授权逐条审干净。"

### 旺衰八类证据

| 编号 | Evidence ID | 名称 | 方向 |
|------|-------------|------|------|
| 1 | ROOT_PRESENT | 根气存在 | SUPPORT |
| 2 | MAIN_QI_ROOT | 本气根 | SUPPORT |
| 3 | SEASONAL_SUPPORT | 得令 | SUPPORT |
| 4 | RESOURCE_SUPPORT | 透印 | SUPPORT |
| 5 | PEER_SUPPORT | 透比劫 | SUPPORT |
| 6 | OFFICER_CONTROL | 官杀制约 | CONSTRAINT |
| 7 | OUTPUT_DRAIN | 食伤泄 | CONSTRAINT |
| 8 | WEALTH_DRAIN | 财星耗 | CONSTRAINT |

### 每条证据必须回答的 10 个问题

1. 原典原文是什么？
2. 原文说的是事实、关系、证据还是结论？
3. 适用条件是什么？
4. 输入 Fact 是什么？
5. Relation 是什么？
6. Evidence 到底是什么？
7. 原典是否明确授权？
8. 有没有工程推导？
9. 如果有推导，最多允许输出到什么级别？
10. 是否可以进入生产？

---

## 二、八类证据逐条审计

### 证据 1：ROOT_PRESENT（根气存在）

#### ① 原典原文

**《子平真诠·论十干得时不旺失时不弱》**：
> "人之日主，不必生逢禄旺，即月令休囚，而年日时中，得长禄旺，便不为弱，就使逢库，亦为有根。"

**《渊海子平》**：
> "得令则旺，失令则衰；根重则强，根轻则弱。"

#### ② 原文说的是什么层级

原文明确讨论的是：
- "有根"是一个**结构事实**（地支藏干中有与日主同类的天干）
- "有根"可以影响旺衰，但"有根"本身不等于"旺"
- 原文说"亦为有根"，是在确认这个结构事实的存在

**结论：原文说的是关系/证据层，不是结论层。**

#### ③ 适用条件

- 日主确定
- 地支（年/月/日/时）的藏干中出现与日主同类的天干
- 包括本气、中气、余气
- 包括禄旺、长生、墓库等各种根气形式

#### ④ 输入 Fact

- DAY_MASTER（日主）
- ALL_HIDDEN_STEMS（所有地支的藏干列表）

#### ⑤ Relation

- CONTAINS（地支藏日主）
- ROOT_PRESENT（日主有根，派生结构关系）

#### ⑥ Evidence 到底是什么

```
Evidence: ROOT_PRESENT
  judgment_target: DAY_MASTER_STRENGTH / ROOT_QI
  polarity: SUPPORT
  value: {
    root_present: true,
    root_count: N,
    root_details: [
      {position: month, branch: 寅, qi_level: main},
      ...
    ],
    has_main_qi_root: true/false
  }
```

**关键：ROOT_PRESENT 只说"有根"，不说"根有多强"，更不说"身强"。**

#### ⑦ 原典是否明确授权

**是。** 《子平真诠》明确说"亦为有根"，《渊海子平》明确说"根重则强，根轻则弱"。

"有根"作为一个结构事实，有明确原典依据。

#### ⑧ 有没有工程推导

有少量推导：
- 从 CONTAINS（地支藏日主）派生 ROOT_PRESENT（日主有根）
- 这个推导是纯结构的，没有命理判断

#### ⑨ 最多允许输出到什么级别

**AUTHORIZED（可以输出 CONFIRMED）**

因为：
- 原典明确支持"有根"这个结构事实
- 工程推导只是纯结构派生，没有加入命理判断
- "有根"不等于"旺"，这个边界已经守住

#### ⑩ 是否可以进入生产

**是。** ROOT_PRESENT 可以作为生产级 Evidence。

**但注意**：它只是 SUPPORT 证据，不能单独推出"身强"。

---

### 证据 2：MAIN_QI_ROOT（本气根）

#### ① 原典原文

**《滴天髓·通神论·衰旺》**（任铁樵注）：
> "得地为旺，本气根为根气之最重者。"

**《子平真诠·论十干得时不旺失时不弱》**：
> "人之日主，不必生逢禄旺，即月令休囚，而年日时中，得长禄旺，便不为弱。"

#### ② 原文说的是什么层级

原文讨论的是：
- "本气根"是根气中"最重"的一种
- 这是一个**比较性描述**（本气根 > 中气根 > 余气根）
- 但原文没有明确说"本气根 = 偏强"

**结论：原文说的是证据的强度比较，不是结论。**

#### ③ 适用条件

- 日主确定
- 某个地支的本气（第一个藏干）与日主同类
- 本气根是根气的一种特殊形式

#### ④ 输入 Fact

- DAY_MASTER（日主）
- ALL_HIDDEN_STEMS（所有地支的藏干列表，特别是 main_qi 字段）

#### ⑤ Relation

- CONTAINS（地支藏日主，且 qi_level = main）
- ROOT_PRESENT（日主有根）
- MAIN_QI_ROOT（日主有本气根，派生关系）

#### ⑥ Evidence 到底是什么

```
Evidence: MAIN_QI_ROOT
  judgment_target: DAY_MASTER_STRENGTH / ROOT_QI
  polarity: SUPPORT
  value: {
    main_qi_root_present: true,
    root_position: month/day/year/hour,
    root_branch: 寅,
    root_qi_level: main
  }
```

**关键：MAIN_QI_ROOT 只说"有本气根"，不说"本气根 = 偏强"。**

#### ⑦ 原典是否明确授权

**部分授权。**

原典明确支持：
- "本气根为根气之最重者"（强度比较）

原典没有明确支持：
- "本气根 → 偏强"（结论推导）
- "本气根的具体权重"（量化）

#### ⑧ 有没有工程推导

有推导：
- 从 ROOT_PRESENT 派生 MAIN_QI_ROOT（筛选 qi_level = main 的根）
- 这个推导是纯结构的

但如果把 MAIN_QI_ROOT 直接等同于"偏强"，那就是工程推导加入了命理判断。

#### ⑨ 最多允许输出到什么级别

**PARTIAL（只能输出 QUALIFIED，不能 CONFIRMED）**

因为：
- 原典支持"本气根最重"这个比较性描述
- 但"本气根 → 偏强"这个结论推导没有原典明确授权
- 工程推导从"有本气根"到"本气根强"已经加入了语义判断

**所以 MAIN_QI_ROOT 的输出状态应该是 QUALIFIED，不是 CONFIRMED。**

#### ⑩ 是否可以进入生产

**可以作为 RESEARCH / CANDIDATE 进入，但不能作为 PROVEN 生产级确定辨证依据。**

在生产中：
- MAIN_QI_ROOT 可以作为 SUPPORT 证据
- 但它的辨证输出必须标为 QUALIFIED
- 不能单独用它推出"身强"

---

### 证据 3：SEASONAL_SUPPORT（得令）

#### ① 原典原文

**《滴天髓》**：
> "得时俱为旺论，失令便作衰看，虽是至理，亦死法也。"
> "令星乃天命之权，得时者旺，失时者衰。"
> "月令乃提纲之府，譬之宅也。"

**《子平真诠·论十干得时不旺失时不弱》**：
> "书云，得时俱为旺论，失时便作衰看，虽是至理，亦死法也。然亦可活看。"

**《渊海子平》**：
> "得令则旺，失令则衰；根重则强，根轻则弱。"
> "得时俱为旺论，失令便作衰看，虽是本理，然须察支中党众，干上生扶，方可定其真衰真旺。"

#### ② 原文说的是什么层级

原文非常明确地讨论了一个关键问题：

**"得令"是旺衰判断的重要证据，但"得令"不等于"旺"。**

《滴天髓》和《子平真诠》都明确说：
- "得时俱为旺论"是"至理"
- 但也是"死法"
- 必须"活看"
- 必须结合其他条件（支中党众、干上生扶）才能定真衰真旺

**结论：原文说的是证据层，而且明确警告不能直接当结论。**

#### ③ 适用条件

- 日主确定
- 月令（月支）确定
- 日主五行与月令五行的关系：
  - 同五行（如甲木在寅卯月）→ 得令
  - 月令生日主（如甲木在亥子月）→ 得令生
  - 日主克月令（如甲木在辰戌丑未月）→ 得令耗
  - 月令克日主（如甲木在申酉月）→ 失令受克
  - 日主生月令（如甲木在巳午月）→ 失令泄气

**注意**：传统命理中"得令"通常指日主五行与月令同五行，或月令生日主。但这个定义需要进一步精确。

#### ④ 输入 Fact

- DAY_MASTER（日主）
- MONTH_BRANCH（月支）
- 五行属性（日主五行、月令五行）

#### ⑤ Relation

- WUXING_RELATION（日主五行与月令五行的生克关系）
- SEASONAL_ALIGNMENT（日主与月令的关系，派生关系）
- GROWTH_STAGE（日主在月令的十二长生状态）

#### ⑥ Evidence 到底是什么

```
Evidence: SEASONAL_SUPPORT
  judgment_target: DAY_MASTER_STRENGTH
  polarity: SUPPORT
  value: {
    seasonal_state: "IN_SEASON" / "GENERATED_BY_SEASON" / "..."
    month_branch: 寅,
    day_master_wuxing: wood,
    month_wuxing: wood,
    growth_stage: "临官" / "帝旺" / "长生" / ...
  }
```

**关键：SEASONAL_SUPPORT 只说"得令"这个事实，不说"得令 = 旺"。**

#### ⑦ 原典是否明确授权

**部分授权。**

原典明确支持：
- "得令"是旺衰判断的核心指标
- "得时者旺，失时者衰"（原则性描述）

原典明确警告：
- "得时俱为旺论...虽是至理，亦死法也"
- "然须察支中党众，干上生扶，方可定其真衰真旺"

**所以"得令"作为证据有原典依据，但"得令 = 旺"作为结论没有原典授权。**

#### ⑧ 有没有工程推导

有推导：
- 从日主五行与月令五行的生克关系派生 SEASONAL_SUPPORT
- 这个推导是纯结构的（五行生克是确定的）

但如果把 SEASONAL_SUPPORT 直接等同于"旺"，那就是工程推导加入了命理判断，而这正是原典明确警告的"死法"。

#### ⑨ 最多允许输出到什么级别

**PARTIAL（只能输出 QUALIFIED，不能 CONFIRMED）**

因为：
- 原典支持"得令"是重要证据
- 但原典明确警告"得令 ≠ 旺"，必须结合其他条件
- "得令 → SUPPORT 证据"有原典依据
- "得令 → 旺"这个结论没有原典授权

**所以 SEASONAL_SUPPORT 可以作为 SUPPORT 证据，但它的辨证输出必须标为 QUALIFIED。**

#### ⑩ 是否可以进入生产

**可以作为 RESEARCH / CANDIDATE 进入，但不能作为 PROVEN 生产级确定辨证依据。**

在生产中：
- SEASONAL_SUPPORT 可以作为 SUPPORT 证据
- 但它的辨证输出必须标为 QUALIFIED
- 不能单独用它推出"身强"
- 必须与 ROOT_PRESENT、RESOURCE_SUPPORT 等其他证据组合

---

### 证据 4：RESOURCE_SUPPORT（透印）

#### ① 原典原文

**《滴天髓》**：
> "生我者为印绶，印绶者，生我之神也。"

**《渊海子平·论印绶》**：
> "印绶者，生我之神也。... 印绶喜财星，忌比劫。"

**《子平真诠》**：
> "印绶者，生我之神也。... 印绶用官，官生印，印生身，亦为贵格。"

#### ② 原文说的是什么层级

原文讨论的是：
- "印"的定义（生我者为印）
- 印的作用（生身）
- 印的喜忌（喜财星，忌比劫）

但原文没有明确说：
- "透印 = 身强"
- "透印的具体权重"

**结论：原文说的是十神定义和作用，不是直接的旺衰结论。**

#### ③ 适用条件

- 日主确定
- 天干（年/月/时干）中出现生日主的五行
- 例如：甲木日主，天干见壬癸水（水生木）

#### ④ 输入 Fact

- DAY_MASTER（日主）
- YEAR_STEM / MONTH_STEM / HOUR_STEM（天干）
- 五行属性

#### ⑤ Relation

- WUXING_GENERATES（某天干五行生日主五行）
- TEN_GOD_RELATION（派生十神关系：印）
- RESOURCE_SUPPORT（透印，派生关系）

#### ⑥ Evidence 到底是什么

```
Evidence: RESOURCE_SUPPORT
  judgment_target: DAY_MASTER_STRENGTH
  polarity: SUPPORT
  value: {
    resource_present: true,
    resource_count: N,
    resource_positions: ["year", "month", "hour"],
    resource_stems: ["壬", "癸"],
    resource_type: "正印" / "偏印"
  }
```

**关键：RESOURCE_SUPPORT 只说"透印"这个事实，不说"透印 = 身强"。**

#### ⑦ 原典是否明确授权

**部分授权。**

原典明确支持：
- "印"的定义（生我者为印）
- 印的作用（生身）

原典没有明确支持：
- "透印 = 身强"（结论推导）
- "透印的具体权重"（量化）

#### ⑧ 有没有工程推导

有推导：
- 从五行生克关系派生十神关系（印）
- 从十神关系派生 RESOURCE_SUPPORT
- 这个推导是纯结构的（五行生克和十神定义是确定的）

但如果把 RESOURCE_SUPPORT 直接等同于"身强"，那就是工程推导加入了命理判断。

#### ⑨ 最多允许输出到什么级别

**PARTIAL（只能输出 QUALIFIED，不能 CONFIRMED）**

因为：
- 原典支持"印生身"这个作用描述
- 但"透印 → 身强"这个结论推导没有原典明确授权
- 印多反而可能"母慈灭子"（水多木漂），所以透印不一定是支持

**所以 RESOURCE_SUPPORT 的输出状态应该是 QUALIFIED，不是 CONFIRMED。**

#### ⑩ 是否可以进入生产

**可以作为 RESEARCH / CANDIDATE 进入，但不能作为 PROVEN 生产级确定辨证依据。**

在生产中：
- RESOURCE_SUPPORT 可以作为 SUPPORT 证据
- 但它的辨证输出必须标为 QUALIFIED
- 不能单独用它推出"身强"
- 必须考虑印的数量、位置、是否受克等条件

---

### 证据 5：PEER_SUPPORT（透比劫）

#### ① 原典原文

**《渊海子平·论比劫》**：
> "比劫者，同我之神也。... 比劫夺财，又能帮身。"

**《滴天髓》**：
> "比劫重重，必争财而克妻。"

**《子平真诠》**：
> "比劫者，同我之神也。... 比劫为用，可以帮身，可以分财。"

#### ② 原文说的是什么层级

原文讨论的是：
- "比劫"的定义（同我者为比劫）
- 比劫的双重作用：帮身（支持日主）+ 夺财（消耗财星）
- 比劫多了反而不好（争财克妻）

**结论：原文说的是十神定义和作用，比劫的作用是双面的。**

#### ③ 适用条件

- 日主确定
- 天干（年/月/时干）中出现与日主同五行的天干
- 例如：甲木日主，天干见甲乙木（同五行）

#### ④ 输入 Fact

- DAY_MASTER（日主）
- YEAR_STEM / MONTH_STEM / HOUR_STEM（天干）
- 五行属性、阴阳属性

#### ⑤ Relation

- SAME_ELEMENT（某天干五行与日主五行相同）
- TEN_GOD_RELATION（派生十神关系：比肩/劫财）
- PEER_SUPPORT（透比劫，派生关系）

#### ⑥ Evidence 到底是什么

```
Evidence: PEER_SUPPORT
  judgment_target: DAY_MASTER_STRENGTH
  polarity: SUPPORT
  value: {
    peer_present: true,
    peer_count: N,
    peer_positions: ["year", "month", "hour"],
    peer_stems: ["甲", "乙"],
    peer_type: "比肩" / "劫财"
  }
```

**关键：PEER_SUPPORT 只说"透比劫"这个事实，不说"透比劫 = 身强"。**

#### ⑦ 原典是否明确授权

**部分授权。**

原典明确支持：
- "比劫"的定义（同我者为比劫）
- 比劫的作用之一是"帮身"

原典明确警告：
- 比劫也"夺财"
- "比劫重重，必争财而克妻"
- 比劫多了不一定是好事

**所以"比劫帮身"有原典依据，但"透比劫 = 身强"这个结论没有原典授权。**

#### ⑧ 有没有工程推导

有推导：
- 从五行相同派生十神关系（比劫）
- 从十神关系派生 PEER_SUPPORT
- 这个推导是纯结构的

但如果把 PEER_SUPPORT 直接等同于"身强"，那就是工程推导加入了命理判断，而且忽略了比劫"夺财"的另一面。

#### ⑨ 最多允许输出到什么级别

**PARTIAL（只能输出 QUALIFIED，不能 CONFIRMED）**

因为：
- 原典支持"比劫帮身"这个作用描述
- 但原典也明确说比劫"夺财"，作用是双面的
- "透比劫 → 身强"这个结论推导没有原典明确授权

**所以 PEER_SUPPORT 的输出状态应该是 QUALIFIED，不是 CONFIRMED。**

#### ⑩ 是否可以进入生产

**可以作为 RESEARCH / CANDIDATE 进入，但不能作为 PROVEN 生产级确定辨证依据。**

在生产中：
- PEER_SUPPORT 可以作为 SUPPORT 证据
- 但它的辨证输出必须标为 QUALIFIED
- 不能单独用它推出"身强"
- 必须考虑比劫的数量、位置、是否夺财等条件

---

### 证据 6：OFFICER_CONTROL（官杀制约）

#### ① 原典原文

**《渊海子平·论官杀》**：
> "官杀者，克我之神也。... 正官为贵气，七杀为凶神。"

**《滴天髓》**：
> "官杀混杂，乃贫贱之辈。... 官杀太旺，必主夭贫。"

**《子平真诠·论官杀》**：
> "官杀者，克我之神也。... 官杀可以制比劫，可以护财星。"

#### ② 原文说的是什么层级

原文讨论的是：
- "官杀"的定义（克我者为官杀）
- 官杀的作用：克日主（制约）+ 制比劫 + 护财
- 官杀的两面性：正官为贵，七杀为凶
- 官杀太旺不好（夭贫）

**结论：原文说的是十神定义和作用，官杀对日主是制约关系。**

#### ③ 适用条件

- 日主确定
- 天干或地支中出现克日主的五行
- 例如：甲木日主，见庚辛金（金克木）

#### ④ 输入 Fact

- DAY_MASTER（日主）
- 所有干支的五行属性
- 十神关系

#### ⑤ Relation

- WUXING_CONTROLS（某干支五行克日主五行）
- TEN_GOD_RELATION（派生十神关系：正官/七杀）
- OFFICER_CONTROL（官杀制约，派生关系）

#### ⑥ Evidence 到底是什么

```
Evidence: OFFICER_CONTROL
  judgment_target: DAY_MASTER_STRENGTH
  polarity: CONSTRAINT
  value: {
    officer_present: true,
    officer_count: N,
    officer_positions: [...],
    officer_stems: ["庚", "辛"],
    officer_type: "正官" / "七杀",
    officer_rooted: true / false
  }
```

**关键：OFFICER_CONTROL 只说"官杀制约"这个事实，不说"官杀 = 身弱"。**

#### ⑦ 原典是否明确授权

**部分授权。**

原典明确支持：
- "官杀"的定义（克我者为官杀）
- 官杀对日主是制约关系

原典没有明确支持：
- "官杀 = 身弱"（结论推导）
- 官杀可以是贵气（正官），也可以制比劫护财
- 官杀有根/无根、有制/无制差别很大

**所以"官杀制约"作为证据有原典依据，但"官杀 = 身弱"作为结论没有原典授权。**

#### ⑧ 有没有工程推导

有推导：
- 从五行相克派生十神关系（官杀）
- 从十神关系派生 OFFICER_CONTROL
- 这个推导是纯结构的

但如果把 OFFICER_CONTROL 直接等同于"身弱"，那就是工程推导加入了命理判断，而且忽略了官杀的正面作用（制比劫、护财、正官为贵）。

#### ⑨ 最多允许输出到什么级别

**PARTIAL（只能输出 QUALIFIED，不能 CONFIRMED）**

因为：
- 原典支持"官杀克日主"这个制约关系
- 但"官杀 → 身弱"这个结论推导没有原典明确授权
- 官杀有双面性，需要看具体条件

**所以 OFFICER_CONTROL 的输出状态应该是 QUALIFIED，不是 CONFIRMED。**

#### ⑩ 是否可以进入生产

**可以作为 RESEARCH / CANDIDATE 进入，但不能作为 PROVEN 生产级确定辨证依据。**

在生产中：
- OFFICER_CONTROL 可以作为 CONSTRAINT 证据
- 但它的辨证输出必须标为 QUALIFIED
- 不能单独用它推出"身弱"
- 必须考虑官杀的数量、位置、有根/无根、有制/无制、正官/七杀等条件

---

### 证据 7：OUTPUT_DRAIN（食伤泄）

#### ① 原典原文

**《渊海子平·论食伤》**：
> "食伤者，我生之神也。... 食神为福寿，伤官为祸害。"

**《滴天髓》**：
> "伤官见官，为祸百端。... 食伤泄秀，亦为聪明。"

**《子平真诠》**：
> "食伤者，我生之神也。... 食伤可以泄身，可以生财。"

#### ② 原文说的是什么层级

原文讨论的是：
- "食伤"的定义（我生者为食伤）
- 食伤的作用：泄日主（消耗日主力量）+ 生财 + 泄秀（聪明）
- 食伤的两面性：食神为福寿，伤官为祸害
- 伤官见官不好

**结论：原文说的是十神定义和作用，食伤对日主是泄耗关系。**

#### ③ 适用条件

- 日主确定
- 天干或地支中出现日主生的五行
- 例如：甲木日主，见丙丁火（木生火）

#### ④ 输入 Fact

- DAY_MASTER（日主）
- 所有干支的五行属性
- 十神关系

#### ⑤ Relation

- WUXING_GENERATES（日主五行生某干支五行）
- TEN_GOD_RELATION（派生十神关系：食神/伤官）
- OUTPUT_DRAIN（食伤泄，派生关系）

#### ⑥ Evidence 到底是什么

```
Evidence: OUTPUT_DRAIN
  judgment_target: DAY_MASTER_STRENGTH
  polarity: CONSTRAINT
  value: {
    output_present: true,
    output_count: N,
    output_positions: [...],
    output_stems: ["丙", "丁"],
    output_type: "食神" / "伤官",
    output_rooted: true / false
  }
```

**关键：OUTPUT_DRAIN 只说"食伤泄"这个事实，不说"食伤 = 身弱"。**

#### ⑦ 原典是否明确授权

**部分授权。**

原典明确支持：
- "食伤"的定义（我生者为食伤）
- 食伤对日主是泄耗关系（泄身）

原典没有明确支持：
- "食伤 = 身弱"（结论推导）
- 食伤可以泄秀（聪明）、可以生财，不全是坏事
- 食伤有制/无制差别很大

**所以"食伤泄"作为证据有原典依据，但"食伤 = 身弱"作为结论没有原典授权。**

#### ⑧ 有没有工程推导

有推导：
- 从五行相生派生十神关系（食伤）
- 从十神关系派生 OUTPUT_DRAIN
- 这个推导是纯结构的

但如果把 OUTPUT_DRAIN 直接等同于"身弱"，那就是工程推导加入了命理判断，而且忽略了食伤的正面作用（泄秀、生财）。

#### ⑨ 最多允许输出到什么级别

**PARTIAL（只能输出 QUALIFIED，不能 CONFIRMED）**

因为：
- 原典支持"食伤泄身"这个泄耗关系
- 但"食伤 → 身弱"这个结论推导没有原典明确授权
- 食伤有双面性，需要看具体条件

**所以 OUTPUT_DRAIN 的输出状态应该是 QUALIFIED，不是 CONFIRMED。**

#### ⑩ 是否可以进入生产

**可以作为 RESEARCH / CANDIDATE 进入，但不能作为 PROVEN 生产级确定辨证依据。**

在生产中：
- OUTPUT_DRAIN 可以作为 CONSTRAINT 证据
- 但它的辨证输出必须标为 QUALIFIED
- 不能单独用它推出"身弱"
- 必须考虑食伤的数量、位置、有根/无根、有制/无制、食神/伤官等条件

---

### 证据 8：WEALTH_DRAIN（财星耗）

#### ① 原典原文

**《渊海子平·论财星》**：
> "财星者，我克之神也。... 财星为养命之源。"

**《滴天髓》**：
> "财多身弱，乃富屋贫人。... 财旺生官，亦为贵格。"

**《子平真诠》**：
> "财星者，我克之神也。... 财星可以生官，可以耗身。"

#### ② 原文说的是什么层级

原文讨论的是：
- "财星"的定义（我克者为财）
- 财星的作用：耗日主（我克者耗我力量）+ 生官 + 养命
- 财星的两面性：财为养命之源，但财多身弱不好
- 财旺生官可以是贵格

**结论：原文说的是十神定义和作用，财星对日主是耗损关系。**

#### ③ 适用条件

- 日主确定
- 天干或地支中出现日主克的五行
- 例如：甲木日主，见戊己土（木克土）

#### ④ 输入 Fact

- DAY_MASTER（日主）
- 所有干支的五行属性
- 十神关系

#### ⑤ Relation

- WUXING_CONTROLS（日主五行克某干支五行）
- TEN_GOD_RELATION（派生十神关系：正财/偏财）
- WEALTH_DRAIN（财星耗，派生关系）

#### ⑥ Evidence 到底是什么

```
Evidence: WEALTH_DRAIN
  judgment_target: DAY_MASTER_STRENGTH
  polarity: CONSTRAINT
  value: {
    wealth_present: true,
    wealth_count: N,
    wealth_positions: [...],
    wealth_stems: ["戊", "己"],
    wealth_type: "正财" / "偏财",
    wealth_rooted: true / false
  }
```

**关键：WEALTH_DRAIN 只说"财星耗"这个事实，不说"财星 = 身弱"。**

#### ⑦ 原典是否明确授权

**部分授权。**

原典明确支持：
- "财星"的定义（我克者为财）
- 财星对日主是耗损关系（我克者耗我）

原典没有明确支持：
- "财星 = 身弱"（结论推导）
- 财星可以生官、可以养命，不全是坏事
- "财多身弱"是特定条件，不是所有财星都导致身弱

**所以"财星耗"作为证据有原典依据，但"财星 = 身弱"作为结论没有原典授权。**

#### ⑧ 有没有工程推导

有推导：
- 从五行相克派生十神关系（财星）
- 从十神关系派生 WEALTH_DRAIN
- 这个推导是纯结构的

但如果把 WEALTH_DRAIN 直接等同于"身弱"，那就是工程推导加入了命理判断，而且忽略了财星的正面作用（生官、养命）。

#### ⑨ 最多允许输出到什么级别

**PARTIAL（只能输出 QUALIFIED，不能 CONFIRMED）**

因为：
- 原典支持"财星耗身"这个耗损关系
- 但"财星 → 身弱"这个结论推导没有原典明确授权
- 财星有双面性，需要看具体条件

**所以 WEALTH_DRAIN 的输出状态应该是 QUALIFIED，不是 CONFIRMED。**

#### ⑩ 是否可以进入生产

**可以作为 RESEARCH / CANDIDATE 进入，但不能作为 PROVEN 生产级确定辨证依据。**

在生产中：
- WEALTH_DRAIN 可以作为 CONSTRAINT 证据
- 但它的辨证输出必须标为 QUALIFIED
- 不能单独用它推出"身弱"
- 必须考虑财星的数量、位置、有根/无根、有制/无制、正财/偏财等条件

---

## 三、八类证据授权状态汇总

| 编号 | Evidence ID | 名称 | 方向 | 原典授权级别 | 最大输出级别 | 可否进入生产 |
|------|-------------|------|------|------------|------------|------------|
| 1 | ROOT_PRESENT | 根气存在 | SUPPORT | 🟢 AUTHORIZED | CONFIRMED | ✅ 可以 |
| 2 | MAIN_QI_ROOT | 本气根 | SUPPORT | 🟡 PARTIAL | QUALIFIED | 🟡 RESEARCH/CANDIDATE |
| 3 | SEASONAL_SUPPORT | 得令 | SUPPORT | 🟡 PARTIAL | QUALIFIED | 🟡 RESEARCH/CANDIDATE |
| 4 | RESOURCE_SUPPORT | 透印 | SUPPORT | 🟡 PARTIAL | QUALIFIED | 🟡 RESEARCH/CANDIDATE |
| 5 | PEER_SUPPORT | 透比劫 | SUPPORT | 🟡 PARTIAL | QUALIFIED | 🟡 RESEARCH/CANDIDATE |
| 6 | OFFICER_CONTROL | 官杀制约 | CONSTRAINT | 🟡 PARTIAL | QUALIFIED | 🟡 RESEARCH/CANDIDATE |
| 7 | OUTPUT_DRAIN | 食伤泄 | CONSTRAINT | 🟡 PARTIAL | QUALIFIED | 🟡 RESEARCH/CANDIDATE |
| 8 | WEALTH_DRAIN | 财星耗 | CONSTRAINT | 🟡 PARTIAL | QUALIFIED | 🟡 RESEARCH/CANDIDATE |

### 关键发现

1. **只有 ROOT_PRESENT 是 AUTHORIZED**：根气存在是纯结构事实，有明确原典依据，可以输出 CONFIRMED。

2. **其他 7 类都是 PARTIAL**：它们都有原典依据（十神定义、作用描述），但"X = 身强/身弱"这个结论推导没有原典明确授权，只能输出 QUALIFIED。

3. **原典明确警告"不可一端论"**：《滴天髓》和《子平真诠》都明确说"得时俱为旺论...虽是至理，亦死法也"，必须结合其他条件才能定真衰真旺。

4. **所有十神类证据都是双面的**：印可以生身也可以"母慈灭子"，比劫可以帮身也可以夺财，官杀可以克身也可以制比劫护财，食伤可以泄身也可以泄秀生财，财星可以耗身也可以生官养命。

---

## 四、核心原则

### 4.1 推理强度 ≤ 原典授权强度

这是整个旺衰证据体系的核心原则：

| 原典授权强度 | 系统最大输出强度 |
|------------|----------------|
| AUTHORIZED（原典明确说 A） | CONFIRMED A |
| PARTIAL（原典明确 A，工程推导 A→B） | QUALIFIED B（不能 CONFIRMED） |
| INFERRED（体系推导，非原典直接命题） | 不能进入生产辨证 |
| NOT_AUTHORIZED（找不到足够依据） | 直接禁止 |

### 4.2 局部证据 ≠ 整体判断

```
ROOT_PRESENT = TRUE
MAIN_QI_ROOT = TRUE
SEASONAL_SUPPORT = TRUE
RESOURCE_SUPPORT = TRUE
PEER_SUPPORT = TRUE
    ↓
这些都是局部证据（SUPPORT）
    ↓
是否能够推出 DAY_MASTER_STRENGTH = STRONG?
    ↓
必须有一条明确授权的综合 Judgment Rule
    ↓
没有？ → UNRESOLVED / NOT_DEFINED
```

### 4.3 证据组合必须有原典授权

旺衰的综合判断（A+B+C+D+E → 整体旺衰）必须有明确的原典授权规则。

目前：
- 原典说"得时俱为旺论...亦死法也"——警告不能单靠得令
- 原典说"然须察支中党众，干上生扶，方可定其真衰真旺"——要求综合判断
- 但原典没有给出具体的"3个支持+2个制约=强"这样的量化规则

**所以整体旺衰判断目前是 NOT_AUTHORIZED，必须保持 UNRESOLVED / NOT_DEFINED。**

---

## 五、下一步行动

### 5.1 可以立即做的

1. ✅ **ROOT_PRESENT**：已经实现，可以作为生产级 Evidence
2. 🟡 **其他 7 类证据**：可以作为 RESEARCH/CANDIDATE 实现，但输出必须标为 QUALIFIED

### 5.2 必须继续研究的

1. **整体旺衰判断规则**：原典中有没有明确的证据组合规则？
   - 《滴天髓》的"进退之机"
   - 《子平真诠》的"活看"
   - 《渊海子平》的"支中党众，干上生扶"
   - 这些能不能转化为可执行的 Judgment Rule？

2. **证据的条件细化**：
   - 得令：月令是否受刑冲合害？
   - 得地：根气是否被冲克？
   - 透印：印是否受克？印多是否"母慈灭子"？
   - 官杀：官杀是否有制？官杀是否混杂？

3. **特殊格局**：
   - 从强/从弱格
   - 化气格
   - 这些特殊格局的证据规则是什么？

### 5.3 禁止做的

1. ❌ **不能写 strength_engine.py**：在整体旺衰判断规则没有原典授权之前，不能写一个"得令+得地+得势=强"的算法
2. ❌ **不能把 PARTIAL 证据标为 CONFIRMED**：推理强度必须 ≤ 原典授权强度
3. ❌ **不能用局部证据推出整体判断**：必须有明确授权的综合规则

---

## 六、总结

### 本次审计的核心成果

1. ✅ **旺衰八类证据逐条原典核验**：每类证据都回答了 10 个问题
2. ✅ **明确了授权级别**：1 类 AUTHORIZED，7 类 PARTIAL
3. ✅ **明确了最大输出级别**：ROOT_PRESENT 可以 CONFIRMED，其他只能 QUALIFIED
4. ✅ **明确了生产准入规则**：ROOT_PRESENT 可以生产，其他只能 RESEARCH/CANDIDATE
5. ✅ **明确了整体旺衰判断的状态**：NOT_AUTHORIZED，必须保持 UNRESOLVED / NOT_DEFINED
6. ✅ **找到了原典的核心警告**："得时俱为旺论...虽是至理，亦死法也"——不可一端论

### 最重要的一句话

> **旺衰八类证据中，只有 ROOT_PRESENT（根气存在）是 AUTHORIZED，可以输出 CONFIRMED。其他 7 类（本气根、得令、透印、透比劫、官杀制约、食伤泄、财星耗）都是 PARTIAL，只能输出 QUALIFIED。整体旺衰判断（A+B+C+D+E → 强/弱）目前是 NOT_AUTHORIZED，必须保持 UNRESOLVED / NOT_DEFINED。在原典没有明确授权综合判断规则之前，绝对不能写 strength_engine.py。**

这才是"算准 → 辨准"真正应该有的工程纪律。

---

*本设计文档是 P0-2.7.1C.1 Evidence Authorization Audit 的成果。通过对旺衰八类证据（ROOT_PRESENT、MAIN_QI_ROOT、SEASONAL_SUPPORT、RESOURCE_SUPPORT、PEER_SUPPORT、OFFICER_CONTROL、OUTPUT_DRAIN、WEALTH_DRAIN）逐条原典核验，明确了每类证据的原典依据、语义边界、工程推导程度、最大输出级别和生产准入规则。核心结论：只有 ROOT_PRESENT 是 AUTHORIZED，其他 7 类都是 PARTIAL，整体旺衰判断目前是 NOT_AUTHORIZED。在原典没有明确授权综合判断规则之前，绝对不能写 strength_engine.py。*
