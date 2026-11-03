# P0-2.7 命理语义本体与辨证接口设计

> **设计时间**：2026-08-29
> **设计目标**：建立命理语义本体与辨证接口，完成四张表（Fact Registry、Relation Registry、Evidence Registry、Judgment Registry），定义"事实—关系—证据—辨证"的精确边界
> **基于 commit**：`564ccc1`
> **核心原则**：同源事实，不同辨法；共享关系，不共享结论。
> **核心定义**：辨不是 Rule 的执行结果；辨是某一命理体系在共享的事实与关系空间中，对特定辨证目标进行证据组织、条件判断和状态归纳的过程。

---

## 一、四层架构总览

```
【算】 Calculation
    ↓
Raw Facts（原始事实，确定性计算）
    ↓
┌───────────────┬───────────────┐
    ↓               ↓
Entity          Context
（实体）        （上下文）
    └───────────────┬───────────────┘
                    ↓
【关系】 Relation Engine（越笨越好，只回答"A与B是什么关系"）
    ↓
Semantic Relations（语义关系）
    ↓
┌───────────────┬───────────────┬───────────────┐
    ↓               ↓               ↓
Strength      Pattern       Tiaohou
Context       Context       Context
（旺衰上下文） （格局上下文） （调候上下文）
    ↓               ↓               ↓
【证据】 Evidence Derivation（针对特定辨证目标的语义化）
    ↓
Evidence Set（证据集合，每个 Evidence 带 judgment_target）
    ↓
【辨证】 Judgment Strategy（某一经典如何组织证据得到 State）
    ↓
┌───────────────┬───────────────┬───────────────┐
    ↓               ↓               ↓
滴天髓辨证     子平真诠辨证    穷通宝鉴辨证
（气势/体用）   （格局）        （调候）
    └───────────────┼───────────────┘
                    ↓
Semantic State（语义状态，UNRESOLVED 是合法结果）
    ↓
Signal
    ↓
【解】 Interpretation
```

### 四层的精确边界

| 层 | 回答的问题 | 不应该做的事 | 示例 |
|----|-----------|-------------|------|
| **Fact** | 这个命局客观上是什么？ | 不做任何判断、不做任何解释 | DM=甲，Month=寅，寅藏甲丙戊 |
| **Relation** | A 与 B 是什么关系？ | 不说事业压力、身体疾病、身强身弱、吉凶 | 甲--SAME_ELEMENT-->乙，寅--CONTAINS-->甲，寅--CLASH-->申 |
| **Evidence** | 针对某个辨证目标，这个关系意味着什么局部证据？ | 不做最终判断、不综合多个证据 | For strength: ROOT_SUPPORT（得地证据），SEASONAL_ALIGNMENT（得令证据） |
| **Judgment** | 某一经典如何组织这些证据得到 State？ | 不重新计算 Fact、不重新计算 Relation | 滴天髓旺衰辨证：得令+得地+得势→偏强；证据不足→UNRESOLVED |

---

## 二、表 1：Fact Registry（事实注册表）

### 定义
Fact 是确定性计算的结果，描述命局的客观状态。Fact 不做任何判断、不做任何解释。

### Fact 列表（基于当前 BaziChart）

| Fact ID | 名称 | 来源 | 值类型 | 计算模块 | 是否确定性 | 说明 |
|---------|------|------|--------|----------|-----------|------|
| F-001 | year_pillar | 输入计算 | (stem, branch) | bazi_engine | ✅ | 年柱 |
| F-002 | month_pillar | 输入计算 | (stem, branch) | bazi_engine | ✅ | 月柱 |
| F-003 | day_pillar | 输入计算 | (stem, branch) | bazi_engine | ✅ | 日柱 |
| F-004 | hour_pillar | 输入计算 | (stem, branch) | bazi_engine | ✅ | 时柱 |
| F-005 | day_master | 派生 | stem | bazi_engine | ✅ | 日主（日干） |
| F-006 | gender | 输入 | male/female | bazi_engine | ✅ | 性别 |
| F-007 | solar_date | 输入 | datetime | bazi_engine | ✅ | 公历出生日期 |
| F-008 | luck_pillars | 派生 | list[(stem, branch)] | bazi_engine | ✅ | 大运柱 |
| F-009 | start_age | 派生 | float | bazi_engine | ✅ | 起运年龄 |
| F-010 | hidden_stems | 派生 | dict[branch -> list[stem]] | bazi_l1_facts | ✅ | 藏干（本气/中气/余气） |
| F-011 | ten_gods | 派生 | dict[position -> ten_god] | bazi_ten_gods | ✅ | 十神 |
| F-012 | twelve_growth | 派生 | dict[stem -> dict[branch -> stage]] | bazi_l1_facts | ✅ | 十二长生（丁已修正，己UNRESOLVED） |
| F-013 | five_element_counts | 派生 | dict[element -> int] | bazi_engine | ✅ | 五行计数（客观统计） |
| F-014 | five_element_balance | 派生 | dict[element -> float] | bazi_engine | ✅ | 五行比例（客观统计） |
| F-015 | climate | 派生 | dict[season -> properties] | bazi_engine | ✅ | 气候状态（寒暖燥湿） |
| F-016 | kong_wang | 派生 | list[branch] | bazi_engine | ✅ | 空亡（计算事实，不包含"力量减半"） |

### Fact 层的硬约束

1. **Fact 必须是确定性计算**：相同输入必须产生相同输出
2. **Fact 不做任何判断**：不包含"强/弱/吉/凶/喜/忌"等语义
3. **Fact 不做任何解释**：不包含"主.../断.../为..."等解释
4. **Fact 必须有完整的测试覆盖**：特别是边界情况（子初、节气、真太阳时等）
5. **Fact 允许 UNRESOLVED**：无法确定时保持 UNRESOLVED，不强行计算（如己土十二长生）

---

## 三、表 2：Relation Registry（关系注册表）

### 定义
Relation 是两个或多个 Fact 之间的命理关系。Relation Engine 越笨越好，只回答"A 与 B 是什么关系"，不做任何判断或解释。

### Relation 类型

| Relation ID | 名称 | Source Fact | Target Fact | Relation Type | 产生条件 | 是否可逆 | 说明 |
|-------------|------|-------------|-------------|---------------|----------|---------|------|
| R-001 | SAME_ELEMENT | stem A | stem B | 五行相同 | A.element == B.element | ✅ | 甲与乙同属木 |
| R-002 | SAME_YIN_YANG | stem A | stem B | 阴阳相同 | A.yin_yang == B.yin_yang | ✅ | 甲与丙同属阳 |
| R-003 | GENERATES | stem A | stem B | 五行相生 | A.element generates B.element | ❌ | 甲生丙（木生火） |
| R-004 | CONTROLS | stem A | stem B | 五行相克 | A.element controls B.element | ❌ | 甲克戊（木克土） |
| R-005 | CONTROLLED_BY | stem A | stem B | 被克 | B.element controls A.element | ❌ | 甲被庚克（金克木） |
| R-006 | DRAINS | stem A | stem B | 被泄 | B.element generates A.element | ❌ | 甲被丁泄（木生火） |
| R-007 | CONTAINS | branch | stem | 藏干 | stem in branch.hidden_stems | ❌ | 寅藏甲丙戊 |
| R-008 | MAIN_QI | branch | stem | 本气 | stem == branch.main_qi | ❌ | 寅本气甲 |
| R-009 | ROOT_PRESENT | day_master | branch | 有根 | day_master in branch.hidden_stems | ❌ | 甲日主在寅有根 |
| R-010 | ROOT_MAIN_QI | day_master | branch | 本气根 | day_master == branch.main_qi | ❌ | 甲日主在寅为本气根 |
| R-011 | STEM_COMBINATION | stem A | stem B | 天干五合 | (A,B) in FIVE_COMBINATIONS | ✅ | 甲己合 |
| R-012 | BRANCH_COMBINATION | branch A | branch B | 地支六合 | (A,B) in SIX_COMBINATIONS | ✅ | 子丑合 |
| R-013 | BRANCH_CLASH | branch A | branch B | 地支六冲 | (A,B) in SIX_CLASHES | ✅ | 子午冲 |
| R-014 | BRANCH_HARM | branch A | branch B | 地支六害 | (A,B) in SIX_HARMS | ✅ | 子未害 |
| R-015 | BRANCH_PUNISH | branch A | branch B | 地支三刑 | (A,B,C) in THREE_PUNISHMENTS | ✅ | 寅巳申三刑 |
| R-016 | BRANCH_BREAK | branch A | branch B | 地支相破 | (A,B) in SIX_BREAKS | ✅ | 子酉破 |
| R-017 | THREE_COMBINATION | branches A,B,C | element | 三合局 | (A,B,C) in THREE_COMBINATIONS | ❌ | 寅午戌三合火 |
| R-018 | THREE_MEETING | branches A,B,C | element | 三会局 | (A,B,C) in THREE_MEETINGS | ❌ | 寅卯辰三会木 |
| R-019 | TEN_GOD | day_master | stem | 十神 | derived from element+yin_yang relation | ❌ | 甲日主+丙=食神 |
| R-020 | SEASONAL_ALIGNMENT | day_master | month_branch | 得令 | day_master.stage in month == [临官,帝旺,长生] | ❌ | 甲日主在寅月得令 |
| R-021 | KONG_WANG | branch | - | 空亡 | branch in xun_kong | ❌ | 甲子旬中戌亥空 |

### Relation 层的硬约束

1. **Relation Engine 越笨越好**：只回答"A 与 B 是什么关系"，不做任何判断或解释
2. **Relation 不说吉凶**：不包含"事业压力/身体疾病/身强身弱/贵贱吉凶"等语义
3. **Relation 不做综合**：不综合多个 Relation 得出结论
4. **Relation 必须是确定性计算**：相同 Fact 必须产生相同 Relation
5. **Relation 允许 UNRESOLVED**：无法确定时保持 UNRESOLVED（如合化条件未满足时，只记录"合"，不记录"化"）

---

## 四、表 3：Evidence Registry（证据注册表）

### 定义
Evidence 是针对特定辨证目标，对 Relation 进行的语义化。Evidence 必须带 judgment_target，说明这个证据是为哪个辨证目标服务的。

### Evidence 与 Relation 的区别

- **Relation**：甲日主在寅有根（ROOT_PRESENT）——这是客观关系
- **Evidence**：For strength judgment: ROOT_SUPPORT（得地证据）——这是针对旺衰辨证目标的语义化

同一个 Relation 可以为不同的辨证目标产生不同的 Evidence：
- ROOT_PRESENT → For strength: ROOT_SUPPORT（得地支持）
- ROOT_PRESENT → For pattern: ROOT_AVAILABLE（根气可用）
- ROOT_PRESENT → For tiaohou: ROOT_STABILITY（根气稳定）

### Evidence 列表（旺衰辨证目标）

| Evidence ID | Judgment Target | 类型 | Source Relation | Context | Evidence Meaning | Provenance |
|-------------|-----------------|------|-----------------|---------|------------------|------------|
| E-S-001 | DAY_MASTER_STRENGTH | SEASONAL_SUPPORT | R-020 SEASONAL_ALIGNMENT | 月令 | 得令支持 | 滴天髓·通神论·衰旺 |
| E-S-002 | DAY_MASTER_STRENGTH | SEASONAL_OPPOSE | NOT R-020 | 月令 | 失令制约 | 滴天髓·通神论·衰旺 |
| E-S-003 | DAY_MASTER_STRENGTH | ROOT_SUPPORT | R-009 ROOT_PRESENT | 日支/年支/时支 | 得地支持 | 滴天髓·通神论·地支 |
| E-S-004 | DAY_MASTER_STRENGTH | ROOT_MAIN_QI_SUPPORT | R-010 ROOT_MAIN_QI | 日支/年支/时支 | 本气根强支持 | 滴天髓·通神论·地支 |
| E-S-005 | DAY_MASTER_STRENGTH | QI_SUPPORT | transparent stems of same element | 天干 | 得势支持（透干） | 滴天髓·通神论·衰旺 |
| E-S-006 | DAY_MASTER_STRENGTH | RESOURCE_SUPPORT | R-003 GENERATES (印生身) | 天干/地支 | 印星生扶支持 | 子平真诠·论用神 |
| E-S-007 | DAY_MASTER_STRENGTH | OUTPUT_DRAIN | R-006 DRAINS (食伤泄身) | 天干/地支 | 食伤泄耗 | 子平真诠·论用神 |
| E-S-008 | DAY_MASTER_STRENGTH | WEALTH_DRAIN | R-004 CONTROLS (财耗身) | 天干/地支 | 财星耗泄 | 子平真诠·论用神 |
| E-S-009 | DAY_MASTER_STRENGTH | OFFICER_CONTROL | R-005 CONTROLLED_BY (官杀克身) | 天干/地支 | 官杀制约 | 子平真诠·论用神 |
| E-S-010 | DAY_MASTER_STRENGTH | ROOT_DAMAGED | R-013 BRANCH_CLASH (根被冲) | 日支/年支/时支 | 根气受损 | 滴天髓·通神论·地支 |
| E-S-011 | DAY_MASTER_STRENGTH | COMBINATION_TRANSFORM | R-011/R-012 (合化) | 天干/地支 | 合化改变力量（需条件授权） | 三命通会·论合化 |

### Evidence 数据结构

```python
@dataclass
class Evidence:
    evidence_id: str              # 证据 ID，如 E-S-001
    judgment_target: str          # 辨证目标，如 DAY_MASTER_STRENGTH
    evidence_type: str            # 证据类型，如 SEASONAL_SUPPORT
    source_relation_ids: list[str] # 来源 Relation ID 列表
    context: dict                 # 上下文，如 {position: "month_branch"}
    evidence_meaning: str         # 证据含义，如 "得令支持"
    polarity: str                 # 极性：SUPPORT / DRAIN / CONTROL / NEUTRAL
    scope: str                    # 范围：DAY_MASTER / MONTH_COMMAND / etc.
    provenance: str               # 来源，如 "滴天髓·通神论·衰旺"
    confidence: float             # 置信度（0.0-1.0，不是评分，是证据确定性）
```

### Evidence 层的硬约束

1. **Evidence 必须带 judgment_target**：说明这个证据是为哪个辨证目标服务的
2. **Evidence 不做最终判断**：不综合多个 Evidence 得出结论
3. **Evidence 不使用数值评分**：confidence 是证据确定性，不是力量评分
4. **Evidence 必须可追溯**：每个 Evidence 必须有 source_relation_ids 和 provenance
5. **Evidence 允许 UNRESOLVED**：无法确定时保持 UNRESOLVED

---

## 五、表 4：Judgment Registry（辨证注册表）

### 定义
Judgment 是某一命理体系在共享的事实与关系空间中，对特定辨证目标进行证据组织、条件判断和状态归纳的过程。

### Judgment 列表

| Judgment ID | 体系/经典 | 辨证目标 | 必要证据 | 支持证据 | 制约证据 | 转化条件 | 例外条件 | 输出状态 | 经典来源 |
|-------------|-----------|----------|----------|----------|----------|----------|----------|----------|----------|
| J-DTS-001 | 滴天髓 | DAY_MASTER_STRENGTH | E-S-001 得令 | E-S-003 得地, E-S-005 得势, E-S-006 印生 | E-S-007 食伤泄, E-S-008 财耗, E-S-009 官杀克 | E-S-011 合化 | E-S-010 根被冲 | 偏强/偏弱/中和/偏枯/UNRESOLVED | 滴天髓·通神论·衰旺 |
| J-ZP-001 | 子平真诠 | PATTERN | 月令主气十神 | 透干, 根气, 财生官, 印护官 | 伤官见官, 破格 | 救应 | 从格 | 格成/格破/待成/UNRESOLVED | 子平真诠·论格局 |
| J-QTB-001 | 穷通宝鉴 | CLIMATE_ADJUSTMENT | 日主+月令+气候 | 调候五行出现, 有根, 可用 | 调候五行受阻, 过量 | - | - | 调候成立/调候不足/调候太过/UNRESOLVED | 穷通宝鉴·各月论 |
| J-DTS-002 | 滴天髓 | TI_YONG | 体候选（日主/提纲/四柱/化神/岁运） | 用候选 | 体用关系 | 从格 | - | 体用结构/UNRESOLVED | 滴天髓·通神论·体用 |
| J-SM-001 | 三命通会 | RELATION_TRANSFORMATION | 合/冲/刑/害关系 | 化气条件 | 合而不化 | - | - | 合化成立/合绊/UNRESOLVED | 三命通会·论合化 |

### Judgment 数据结构

```python
@dataclass
class Judgment:
    judgment_id: str              # 辨证 ID，如 J-DTS-001
    system: str                   # 体系/经典，如 DITIANSUI / ZIPING_ZHENQUAN
    target: str                   # 辨证目标，如 DAY_MASTER_STRENGTH
    required_evidence: list[str]  # 必要证据 ID 列表
    supporting_evidence: list[str] # 支持证据 ID 列表
    constraining_evidence: list[str] # 制约证据 ID 列表
    transformation_conditions: list[str] # 转化条件
    exception_conditions: list[str] # 例外条件
    output_states: list[str]      # 可能的输出状态列表
    classical_source: str         # 经典来源
    judgment_strategy: str        # 辨证策略描述（如何组织证据）
    unresolved_policy: str        # UNRESOLVED 策略（证据不足时如何处理）
```

### Judgment 策略示例：滴天髓旺衰辨证

```
Judgment ID: J-DTS-001
System: 滴天髓
Target: DAY_MASTER_STRENGTH

辨证策略：
1. 收集所有旺衰相关 Evidence（E-S-001 ~ E-S-011）
2. 按极性分类：
   - SUPPORT 类：得令、得地、得势、印生
   - DRAIN 类：食伤泄、财耗
   - CONTROL 类：官杀克
   - MODIFIER 类：根被冲、合化
3. 检查必要证据：
   - 如果得令证据缺失 → 降低置信度
4. 综合判断（不使用数值评分，使用符号推理）：
   - 得令 + 得地 + 得势 + 无明显制约 → 偏强
   - 失令 + 无地 + 无势 + 明显制约 → 偏弱
   - 得令但受制严重 → 需进一步判断（可能 UNRESOLVED）
   - 失令但有强根帮扶 → 需进一步判断（可能 UNRESOLVED）
   - 证据不足或存在矛盾 → UNRESOLVED
5. 检查转化条件：
   - 合化可能改变力量分布（需合化条件授权）
6. 检查例外条件：
   - 从格（从强/从弱）需要特殊处理
7. 输出状态：
   - 偏强 / 偏弱 / 中和 / 偏枯 / 太过 / 不及 / UNRESOLVED

UNRESOLVED 策略：
- 证据不足时，不强行判断，输出 UNRESOLVED
- 记录缺失的证据和矛盾的证据
- 不使用 fallback 到旧算法
```

### Judgment 层的硬约束

1. **Judgment 不重新计算 Fact**：只消费 Fact 和 Relation
2. **Judgment 不重新计算 Relation**：只消费 Relation 和 Evidence
3. **Judgment 不使用数值评分**：使用符号推理（必要条件、充分条件、组合条件、抵消条件、优先条件、转化条件、例外条件）
4. **Judgment 必须按体系分类**：不同经典有不同的辨证策略，不混在一起
5. **Judgment 允许并行**：同一个 Fact State 可以同时进入旺衰辨证、格局辨证、调候辨证，不是串行依赖
6. **Judgment 允许 UNRESOLVED**：证据不足时输出 UNRESOLVED，不强行判断
7. **Judgment 必须可追溯**：每个 Judgment 结果必须记录使用了哪些 Evidence、遵循了哪些规则、为什么得出这个结论

---

## 六、最小垂直切片验证：旺衰辨证

### 目标
验证完整链：BaziChart → L1 Facts → Relations → Strength Evidence → 滴天髓/子平相关辨证 → Strength State，全程禁止任何 score。

### 示例：甲日主，寅月

```
【Fact 层】
F-003 day_pillar = (甲, ?)
F-002 month_pillar = (?, 寅)
F-005 day_master = 甲
F-010 hidden_stems = {寅: [甲(本气), 丙(中气), 戊(余气)]}
F-012 twelve_growth = {甲: {寅: 临官}} （丁已修正，己UNRESOLVED）
F-013 five_element_counts = {木: ?, 火: ?, 土: ?, 金: ?, 水: ?}
F-015 climate = {季节: 春, 寒暖: 温, 燥湿: 燥}

【Relation 层】
R-020 SEASONAL_ALIGNMENT: 甲日主在寅月 = 得令（临官）
R-009 ROOT_PRESENT: 甲日主在寅 = 有根
R-010 ROOT_MAIN_QI: 甲日主在寅 = 本气根
R-007 CONTAINS: 寅藏甲丙戊
R-003 GENERATES: 甲生丙（木生火）
R-004 CONTROLS: 甲克戊（木克土）

【Evidence 层】（judgment_target = DAY_MASTER_STRENGTH）
E-S-001 SEASONAL_SUPPORT: 得令支持（来源 R-020）
E-S-003 ROOT_SUPPORT: 得地支持（来源 R-009）
E-S-004 ROOT_MAIN_QI_SUPPORT: 本气根强支持（来源 R-010）
（其他 Evidence 取决于完整八字）

【Judgment 层】（J-DTS-001 滴天髓旺衰辨证）
输入 Evidence:
  - SUPPORT 类：得令、得地（本气根）
  - DRAIN 类：（取决于完整八字）
  - CONTROL 类：（取决于完整八字）
  - MODIFIER 类：（取决于完整八字）

辨证过程：
  1. 得令 + 本气根 = 强支持
  2. 检查是否有明显制约（官杀克、食伤泄、财耗）
  3. 如果无明显制约 → 偏强
  4. 如果有明显制约 → 需进一步判断（可能 UNRESOLVED）
  5. 证据不足 → UNRESOLVED

输出状态：偏强 / 偏弱 / 中和 / UNRESOLVED

全程禁止：
  - 禁止使用 wang_score / de_ling_weight / de_di_weighted
  - 禁止使用 >4.0 / <1.5 等阈值
  - 禁止 fallback 到旧 strength_engine.py
```

---

## 七、代码目录结构（目标）

```
tongshu/
│
├── engines/                          # 计算引擎（Fact 层）
│   ├── bazi_engine.py               # 八字计算
│   ├── bazi_l1_facts.py             # L1 原始事实
│   ├── ziwei_engine.py              # 紫微计算
│   ├── blind_bazi_engine.py         # 盲派计算
│   └── heluo_yi_flow.py             # 河洛计算
│
├── ontology/                         # 命理本体（Fact 定义）
│   ├── yin_yang.py                  # 阴阳
│   ├── wuxing.py                    # 五行
│   ├── stems.py                     # 天干
│   ├── branches.py                  # 地支
│   ├── hidden_stems.py              # 藏干
│   └── ten_gods.py                  # 十神
│
├── relations/                        # 关系引擎（Relation 层）
│   ├── base.py                      # Relation 基类
│   ├── wuxing.py                    # 五行关系（生克泄耗）
│   ├── yin_yang.py                  # 阴阳关系（同异）
│   ├── root.py                      # 根气关系
│   ├── ten_god.py                   # 十神关系（派生）
│   ├── stem.py                      # 天干关系（五合等）
│   ├── branch.py                    # 地支关系（六合/六冲/三合/三会/三刑/六害/相破）
│   └── transformation.py            # 转化关系（合化/制化）
│
├── evidence/                         # 证据层（Evidence 层）
│   ├── base.py                      # Evidence 基类
│   ├── derivation.py                # Evidence 推导
│   ├── strength.py                  # 旺衰证据
│   ├── pattern.py                   # 格局证据
│   ├── tiaohou.py                   # 调候证据
│   └── provenance.py                # 证据来源追踪
│
└── judgment/                         # 辨证层（Judgment 层）
    ├── base.py                      # Judgment 基类
    ├── strength/                    # 旺衰辨证
    │   ├── ditiansui.py            # 滴天髓旺衰辨证
    │   └── ziping.py               # 子平旺衰辨证
    ├── pattern/                     # 格局辨证
    │   └── ziping_zhenquan.py      # 子平真诠格局辨证
    ├── tiaohou/                     # 调候辨证
    │   └── qiongtong_baojian.py    # 穷通宝鉴调候辨证
    ├── ti_yong/                     # 体用辨证
    │   └── ditiansui.py            # 滴天髓体用辨证
    └── classics/                    # 经典规则库
        ├── ditiansui/
        ├── ziping_zhenquan/
        ├── qiongtong_baojian/
        ├── sanming_tonghui/
        └── yuanhai_ziping/
```

### 关键区别

- **engines/**：计算 Fact，确定性计算
- **ontology/**：定义命理本体（阴阳、五行、天干、地支等）
- **relations/**：描述命理世界本身有什么关系（越笨越好）
- **evidence/**：描述针对某个辨证目标，这些关系意味着什么局部证据（必须带 judgment_target）
- **judgment/**：描述经典如何把证据组织成辨证（按体系分类，允许并行）

---

## 八、迁移路径

### 第一阶段：建立接口（不改生产代码）
1. 建立 ontology/ 目录，定义命理本体
2. 建立 relations/ 目录，定义 Relation 基类和接口
3. 建立 evidence/ 目录，定义 Evidence 基类和接口
4. 建立 judgment/ 目录，定义 Judgment 基类和接口
5. 完成四张表的完整定义

### 第二阶段：最小垂直切片（旺衰）
1. 实现 Relations：五行关系、阴阳关系、根气关系、十神关系
2. 实现 Evidence：旺衰证据推导（得令、得地、得势、受制等）
3. 实现 Judgment：滴天髓旺衰辨证（符号推理，禁止 score）
4. 端到端测试：BaziChart → Facts → Relations → Evidence → Judgment → State
5. 验证：全程无 score，UNRESOLVED 是合法结果

### 第三阶段：推广到其他辨证目标
1. 格局辨证（子平真诠）
2. 调候辨证（穷通宝鉴）
3. 体用辨证（滴天髓）
4. 关系转化辨证（三命通会）

### 第四阶段：迁移现有 Rule
1. 将 34 条 RELATION 层 Rule 迁移到 relations/
2. 将 2 条 EVIDENCE 层 Rule 迁移到 evidence/
3. 将 94 条 JUDGMENT 层 Rule 重构为 Judgment Strategy
4. 人工审查 6 条 UNCERTAIN 层 Rule
5. 删除旧 Rule 文件

### 第五阶段：清理 Legacy
1. 隔离 strength_engine.py（Legacy Reference）
2. 隔离 judgment_engine.py（Legacy Reference）
3. 隔离 annual_event_evaluator.py（Legacy Reference）
4. 确认生产路径不依赖 Legacy 代码

---

## 九、当前状态总结

### 四层架构状态

| 层 | 当前状态 | 目标状态 | 差距 |
|----|---------|---------|------|
| Fact | 🟡 在 engines/ 中实现，但混在 BaziChart | ✅ ontology/ + engines/ 分离 | 需要分离纯 Fact 和 Semantic State |
| Relation | 🔴 混在 Rule 层，34 条应该迁移 | ✅ relations/ 统一处理 | 需要建立 Relation Engine |
| Evidence | 🔴 只有 2 条，严重不足 | ✅ evidence/ 针对辨证目标语义化 | 需要建立 Evidence Derivation |
| Judgment | 🟡 94 条 Rule，但质量参差不齐 | ✅ judgment/ + classics/ 按体系分类 | 需要重构为 Judgment Strategy |

### "算 → 辨 → 解"边界状态

| 层 | 状态 | 说明 |
|----|------|------|
| 算（Calculation） | 🟡 继续独立证明 | Fact 在代码中实现，需要完整测试覆盖 |
| Relation Engine | 🔴 缺失 | 34 条 Rule 应该迁移到这里 |
| Evidence Derivation | 🔴 严重不足 | 只有 2 条 Evidence 层的 Rule |
| Judgment Strategy | 🔴 需要重构 | 94 条 Rule 质量参差不齐，需要按体系分类 |
| "辨准" | 🔴 **未通过** | 辨识层需要重新建模 |

---

## 十、下一步建议

### P0-2.7.1：建立四层接口定义（最高优先级）

目标：建立 ontology/、relations/、evidence/、judgment/ 四层的基类和接口定义，不改生产代码。

### P0-2.7.2：最小垂直切片实现（高优先级）

目标：实现旺衰辨证的完整链：Facts → Relations → Evidence → Judgment → State，全程禁止 score。

### P0-2.7.3：端到端测试验证（高优先级）

目标：验证最小垂直切片的正确性，特别是 UNRESOLVED 是合法结果。

### P0-3：Boundary Cases（高优先级）

目标：建立边界测试用例，验证计算引擎在边界情况下的正确性。

### P0-4：Calculation Golden Dataset（高优先级）

目标：建立计算 Golden Dataset，验证 Bazi Calculation 的正确性。

---

## 十一、审计总结

### 本次设计的核心成果

1. ✅ **定义了四层的精确边界**：Fact（客观是什么）、Relation（A与B是什么关系）、Evidence（针对辨证目标的语义化）、Judgment（某一经典如何组织证据得到 State）
2. ✅ **完成了四张表**：Fact Registry（16 条）、Relation Registry（21 条）、Evidence Registry（11 条旺衰）、Judgment Registry（5 条）
3. ✅ **定义了 Evidence 必须带 judgment_target**：同一个 Relation 可以为不同辨证目标产生不同 Evidence
4. ✅ **定义了 Judgment 允许并行**：同一个 Fact State 可以同时进入旺衰、格局、调候辨证，不是串行依赖
5. ✅ **定义了 UNRESOLVED 是合法结果**：证据不足时不强行判断
6. ✅ **全程禁止数值评分**：使用符号推理（必要条件、充分条件、组合条件、抵消条件、优先条件、转化条件、例外条件）
7. ✅ **给出了最小垂直切片验证方案**：旺衰辨证的完整链
8. ✅ **给出了代码目录结构和迁移路径**

### 核心原则

> 辨不是 Rule 的执行结果；辨是某一命理体系在共享的事实与关系空间中，对特定辨证目标进行证据组织、条件判断和状态归纳的过程。

> 同源事实，不同辨法；共享关系，不共享结论。

### 最重要的一句话

这次 P0-2.7 设计真正从"理论上应该怎么做"进入了"代码究竟怎么做"。四层的精确边界、四张表的完整定义、最小垂直切片的验证方案，都已经明确。下一步就是建立接口定义，然后实现最小垂直切片（旺衰），验证这个架构是否真正可行。

等这个最小垂直切片验证通过，再推广到格局、调候、体用等其他辨证目标，最后迁移现有 136 条 Rule。这样整个辨识层的重构就有了坚实的基础。

---

*本设计文档是 P0-2.7 命理语义本体与辨证接口设计的成果。通过定义 Fact、Relation、Evidence、Judgment 四层的精确边界，完成四张表（Fact Registry 16 条、Relation Registry 21 条、Evidence Registry 11 条、Judgment Registry 5 条），给出最小垂直切片验证方案（旺衰辨证），以及代码目录结构和迁移路径。核心原则是：同源事实，不同辨法；共享关系，不共享结论。辨不是 Rule 的执行结果，而是某一命理体系在共享的事实与关系空间中，对特定辨证目标进行证据组织、条件判断和状态归纳的过程。*
