# P0-2.7.2 L4 Evidence Construction — 外势/生扶/克泄耗 Evidence 构造与授权审计

> **设计时间**：2026-08-30
> **基于 commit**：`dc09469`（P0-2.7.1C.1-R 原典证据真实性与 Provenance 加固）
> **触发原因**：用户裁决 dc09469 为 🟢 PASS，明确建议项目正式进入 P0-2.7.2 — L4 Evidence Construction
> **核心原则**：不要再做 strength_engine.py；先把各类 Evidence 逐条构造干净，明确来源、经典授权、授权程度，然后才进入 Combination → Judgment
> **工程分层**：L0 算 → L1 Fact/Relation ✅ → L2 月令状态 Evidence ✅ → L3 通根 Evidence ✅ → **L4 外势/生扶/克泄耗（当前）** → L5 结构变化 → L6 Evidence Combination → L7 Classical Judgment → 解

---

## 一、L4 Evidence 总览

### 1.1 为什么需要 L4

L1-L3 已经建立了基础事实和结构关系：
- L1：Fact / Relation（日主、月令、藏干、十神、干支关系）
- L2：月令状态 Evidence（得令/失令）
- L3：通根 Evidence（ROOT_PRESENT）

但旺衰辨证还需要"外势"——日主在命局中受到的生扶和克泄耗。这就是 L4。

### 1.2 L4 Evidence 清单

| 编号 | Evidence ID | 名称 | 方向 | 核心问题 |
|------|-------------|------|------|---------|
| L4-1 | RESOURCE_SUPPORT | 印生身 | SUPPORT | 命局中有没有生日主的五行？ |
| L4-2 | PEER_SUPPORT | 比劫帮身 | SUPPORT | 命局中有没有同日主的五行？ |
| L4-3 | OFFICER_CONTROL | 官杀克身 | CONSTRAINT | 命局中有没有克日主的五行？ |
| L4-4 | OUTPUT_DRAIN | 食伤泄身 | CONSTRAINT | 命局中有没有日主生的五行？ |
| L4-5 | WEALTH_DRAIN | 财星耗身 | CONSTRAINT | 命局中有没有日主克的五行？ |
| L4-6 | SEASONAL_STATE | 季节状态 | CONTEXT | 日主处于什么季节？寒暖燥湿如何？ |
| L4-7 | ENVIRONMENT_STATE | 环境状态 | CONTEXT | 命局整体的寒暖燥湿环境如何？ |
| L4-8 | STRUCTURAL_CHANGE | 结构变化 | MODIFIER | 有没有刑冲合害改变了基础结构？ |

### 1.3 绝对禁止

❌ **禁止做数量统计后直接判断强弱**：
```
比劫数量 = 3
印数量 = 2
支持 = 5
支持 > 克泄耗 → 身强
```

✅ **正确做法**：
```
Fact → Relation → Evidence（局部证）
  ↓
五部经典各自如何观察这组 Evidence？
  ↓
Evidence Combination（需要原典授权）
  ↓
Classical Judgment
```

---

## 二、L4 Evidence 逐条授权审计

### L4-1：RESOURCE_SUPPORT（印生身）

#### ① 从哪个 Canonical Fact + Relation 得来

```
Canonical Fact:
  - DAY_MASTER（日主，如甲木）
  - 所有干支的五行属性

Relation:
  - WUXING_GENERATES（某干支五行生日主五行）
    例：壬水 → 生 → 甲木
  - TEN_GOD_RELATION（派生十神关系：正印/偏印）
    例：壬水（同阳）生甲木 → 偏印
        癸水（异阴阳）生甲木 → 正印

Evidence Derivation:
  - 扫描所有干支，找出生日主的五行
  - 记录位置（年/月/日/时干或支）
  - 记录十神类型（正印/偏印）
  - 记录是否有根（在地支藏干中有同类五行）
```

#### ② 原典原文

**《滴天髓》（原注）**：
> "旺则宜泄宜伤，衰则喜帮喜助，子平之理也。"

**《子平真诠·论用神》（沈孝瞻原文）**：
> "财官印食，此用神之善而顺用之者也；煞伤劫刃，用神之不善而逆用之者也。"

**《穷通宝鉴·五行总论》（原文）**：
> "五行者，本乎天地之间而不穷者也，故谓之行。北方阴极而生寒，寒生水。南方阳极而生热，热生火。东方阳散以泄而生风，风生木。西方阴止以收而生燥，燥生金。中央阴阳交而生温，温生土。"

#### ③ 授权级别评估

| 维度 | 评估 |
|------|------|
| 十神定义（生我者为印） | 🟢 所有命理书共识，不需要特别授权 |
| 印的作用（印生身） | 🟡 有原典依据，但"印生身 → 身强"需要进一步授权 |
| text_type | ORIGINAL（子平真诠）+ COMMENTARY（滴天髓原注） |
| verification_status | PARTIALLY_VERIFIED |
| 授权级别 | 🟡 PARTIAL |
| 最大输出 | QUALIFIED |
| 可否进入生产 | 🟡 RESEARCH/CANDIDATE |

#### ④ 关键边界

- **"印出现"是结构事实**：命局中有生日主的五行，这是确定的
- **"印生身"是作用描述**：印的作用是生身，这有原典依据
- **"印生身 → 身强"是辨证判断**：这需要原典授权，不能直接推导
- **印多可能"母慈灭子"**：水多木漂，印多反而不好，这是原典警告的

#### ⑤ Evidence 数据结构

```python
@dataclass(frozen=True)
class ResourceSupportEvidence:
    evidence_id: str              # "E-CASE-XXX-RESOURCE_SUPPORT"
    judgment_target: str          # "DAY_MASTER_STRENGTH"
    polarity: str                 # "SUPPORT"
    value: dict
    # {
    #   "resource_present": true,
    #   "resource_count": 2,
    #   "resource_details": [
    #     {"position": "year_stem", "stem": "壬", "type": "偏印", "rooted": true},
    #     {"position": "hour_stem", "stem": "癸", "type": "正印", "rooted": false}
    #   ],
    #   "main_resource": "壬",
    #   "resource_rooted_count": 1
    # }
    source_fact_ids: list        # 来源 Canonical Fact ID
    source_relation_ids: list    # 来源 Relation ID
    derivation_rule_id: str      # 推导规则 ID
    classical_source: dict       # 原典来源（Provenance）
    certainty_state: str         # "DERIVED" / "QUALIFIED" / "UNKNOWN"
```

---

### L4-2：PEER_SUPPORT（比劫帮身）

#### ① 从哪个 Canonical Fact + Relation 得来

```
Canonical Fact:
  - DAY_MASTER（日主，如甲木）
  - 所有干支的五行属性、阴阳属性

Relation:
  - SAME_ELEMENT（某干支五行与日主五行相同）
    例：甲木 = 甲木（比肩），甲木 = 乙木（劫财）
  - TEN_GOD_RELATION（派生十神关系：比肩/劫财）
    例：甲（同阳）→ 比肩
        乙（异阴阳）→ 劫财

Evidence Derivation:
  - 扫描所有干支，找出与日主同五行的干支
  - 记录位置、十神类型（比肩/劫财）
  - 记录是否有根
```

#### ② 原典原文

**《滴天髓》（原文）**：
> "劫财，比肩，阳刃，皆兄弟，要与提纲之神及喜神，较其轻重..."

**《子平真诠·论用神》（沈孝瞻原文）**：
> "煞伤劫刃，用神之不善而逆用之者也。"

**《命理探源·论比肩宜忌》（袁树珊，引用《子平撮要》《玄机赋》）**：
> "《子平撮要》云：比肩要逢官煞制。《玄机赋》云：日干无气遇劫为强。"

#### ③ 授权级别评估

| 维度 | 评估 |
|------|------|
| 十神定义（同我者为比劫） | 🟢 所有命理书共识 |
| 比劫的作用（帮身/夺财） | 🟡 有原典依据，但是双面的 |
| text_type | ORIGINAL（滴天髓/子平真诠）+ LATER_COMPILATION（命理探源引用） |
| verification_status | PARTIALLY_VERIFIED |
| 授权级别 | 🟡 PARTIAL |
| 最大输出 | QUALIFIED |
| 可否进入生产 | 🟡 RESEARCH/CANDIDATE |

#### ④ 关键边界

- **"比劫出现"是结构事实**：确定的
- **"比劫帮身"是作用之一**：有原典依据（"日干无气遇劫为强"）
- **"比劫夺财"是作用之二**：也有原典依据（"比肩要逢官煞制"）
- **比劫是双面的**：身弱时帮身是好事，身旺时夺财是坏事
- **不能简单说"比劫 = 支持"**：必须看具体语境

#### ⑤ Evidence 数据结构

```python
@dataclass(frozen=True)
class PeerSupportEvidence:
    evidence_id: str
    judgment_target: str          # "DAY_MASTER_STRENGTH"
    polarity: str                 # "SUPPORT"（但标注双面性）
    value: dict
    # {
    #   "peer_present": true,
    #   "peer_count": 2,
    #   "peer_details": [
    #     {"position": "month_stem", "stem": "甲", "type": "比肩", "rooted": true},
    #     {"position": "hour_stem", "stem": "乙", "type": "劫财", "rooted": false}
    #   ],
    #   "jian_count": 1,  # 比肩
    #   "jie_count": 1,   # 劫财
    #   "dual_nature": true  # 双面性标记
    # }
    source_fact_ids: list
    source_relation_ids: list
    derivation_rule_id: str
    classical_source: dict
    certainty_state: str
```

---

### L4-3：OFFICER_CONTROL（官杀克身）

#### ① 从哪个 Canonical Fact + Relation 得来

```
Canonical Fact:
  - DAY_MASTER（日主，如甲木）
  - 所有干支的五行属性、阴阳属性

Relation:
  - WUXING_CONTROLS（某干支五行克日主五行）
    例：庚金 → 克 → 甲木
  - TEN_GOD_RELATION（派生十神关系：正官/七杀）
    例：庚（同阳）克甲 → 七杀
        辛（异阴阳）克甲 → 正官

Evidence Derivation:
  - 扫描所有干支，找出克日主的五行
  - 记录位置、十神类型（正官/七杀）
  - 记录是否有根、是否有制
```

#### ② 原典原文

**《子平真诠·论用神》（沈孝瞻原文）**：
> "财官印食，此用神之善而顺用之者也；煞伤劫刃，用神之不善而逆用之者也。当顺而顺，当逆而逆，配合得宜，皆为贵格。"

**《滴天髓阐微》（任铁樵）**：
> "命中至理，只存用神，不拘财、官、印绶、比劫、食伤、枭杀，皆可为用，勿以名之美者为佳，恶者为憎。"

**《命理探源·论比肩宜忌》（袁树珊）**：
> "比肩何以要官煞制，盖日主太强，八字中比肩、劫财、败财曾见叠出，而伤官、食神鲜见，必须官煞以制之，始可循正轨。"

#### ③ 授权级别评估

| 维度 | 评估 |
|------|------|
| 十神定义（克我者为官杀） | 🟢 所有命理书共识 |
| 官杀的作用（克身/制比劫/护财） | 🟡 有原典依据，但是双面的 |
| text_type | ORIGINAL（子平真诠）+ COMMENTARY（滴天髓阐微） |
| verification_status | PARTIALLY_VERIFIED |
| 授权级别 | 🟡 PARTIAL |
| 最大输出 | QUALIFIED |
| 可否进入生产 | 🟡 RESEARCH/CANDIDATE |

#### ④ 关键边界

- **"官杀出现"是结构事实**：确定的
- **"官杀克身"是作用之一**：有原典依据
- **"官杀制比劫/护财"是作用之二**：也有原典依据
- **正官和七杀不同**：正官为"善神"，七杀为"不善神"，处理方式不同
- **官杀有制/无制差别很大**：七杀有制为权，无制为祸
- **不能简单说"官杀 = 制约"**：必须看具体语境（正官/七杀、有制/无制）

#### ⑤ Evidence 数据结构

```python
@dataclass(frozen=True)
class OfficerControlEvidence:
    evidence_id: str
    judgment_target: str
    polarity: str                 # "CONSTRAINT"（但标注双面性）
    value: dict
    # {
    #   "officer_present": true,
    #   "officer_count": 2,
    #   "officer_details": [
    #     {"position": "month_stem", "stem": "庚", "type": "七杀", "rooted": true, "controlled": false},
    #     {"position": "year_stem", "stem": "辛", "type": "正官", "rooted": false, "controlled": true}
    #   ],
    #   "zhengguan_count": 1,
    #   "qisha_count": 1,
    #   "officer_mixed": true,  # 官杀混杂
    #   "dual_nature": true
    # }
    source_fact_ids: list
    source_relation_ids: list
    derivation_rule_id: str
    classical_source: dict
    certainty_state: str
```

---

### L4-4：OUTPUT_DRAIN（食伤泄身）

#### ① 从哪个 Canonical Fact + Relation 得来

```
Canonical Fact:
  - DAY_MASTER（日主，如甲木）
  - 所有干支的五行属性、阴阳属性

Relation:
  - WUXING_GENERATES（日主五行生某干支五行）
    例：甲木 → 生 → 丙火
  - TEN_GOD_RELATION（派生十神关系：食神/伤官）
    例：丙（同阳）由甲生 → 食神
        丁（异阴阳）由甲生 → 伤官

Evidence Derivation:
  - 扫描所有干支，找出日主生的五行
  - 记录位置、十神类型（食神/伤官）
  - 记录是否有根
```

#### ② 原典原文

**《子平真诠·论用神》（沈孝瞻原文）**：
> "财官印食，此用神之善而顺用之者也；煞伤劫刃，用神之不善而逆用之者也。"

**《滴天髓》（原注）**：
> "旺则宜泄宜伤，衰则喜帮喜助，子平之理也。"

**《穷通宝鉴·附论四时之火宜忌》（节录）**：
> "春月之火，母旺子相，势力并行。喜木生扶，不宜过旺，旺则火炎；欲水既济，不宜太多，多则火灭。土多则晦光，火盛则燥烈。"

#### ③ 授权级别评估

| 维度 | 评估 |
|------|------|
| 十神定义（我生者为食伤） | 🟢 所有命理书共识 |
| 食伤的作用（泄身/生财/制杀） | 🟡 有原典依据，但是双面的 |
| text_type | ORIGINAL（子平真诠/穷通宝鉴）+ COMMENTARY（滴天髓原注） |
| verification_status | PARTIALLY_VERIFIED |
| 授权级别 | 🟡 PARTIAL |
| 最大输出 | QUALIFIED |
| 可否进入生产 | 🟡 RESEARCH/CANDIDATE |

#### ④ 关键边界

- **"食伤出现"是结构事实**：确定的
- **"食伤泄身"是作用之一**：有原典依据（"旺则宜泄宜伤"）
- **"食伤生财/制杀"是作用之二**：也有原典依据
- **食神和伤官不同**：食神为"善神"，伤官为"不善神"
- **身旺时食伤泄秀是好事，身弱时食伤泄身是坏事**
- **不能简单说"食伤 = 泄耗"**：必须看具体语境

#### ⑤ Evidence 数据结构

```python
@dataclass(frozen=True)
class OutputDrainEvidence:
    evidence_id: str
    judgment_target: str
    polarity: str                 # "CONSTRAINT"（但标注双面性）
    value: dict
    # {
    #   "output_present": true,
    #   "output_count": 2,
    #   "output_details": [
    #     {"position": "hour_stem", "stem": "丙", "type": "食神", "rooted": true},
    #     {"position": "year_stem", "stem": "丁", "type": "伤官", "rooted": false}
    #   ],
    #   "shishen_count": 1,
    #   "shangguan_count": 1,
    #   "dual_nature": true
    # }
    source_fact_ids: list
    source_relation_ids: list
    derivation_rule_id: str
    classical_source: dict
    certainty_state: str
```

---

### L4-5：WEALTH_DRAIN（财星耗身）

#### ① 从哪个 Canonical Fact + Relation 得来

```
Canonical Fact:
  - DAY_MASTER（日主，如甲木）
  - 所有干支的五行属性、阴阳属性

Relation:
  - WUXING_CONTROLS（日主五行克某干支五行）
    例：甲木 → 克 → 戊土
  - TEN_GOD_RELATION（派生十神关系：正财/偏财）
    例：戊（同阳）被甲克 → 偏财
        己（异阴阳）被甲克 → 正财

Evidence Derivation:
  - 扫描所有干支，找出日主克的五行
  - 记录位置、十神类型（正财/偏财）
  - 记录是否有根
```

#### ② 原典原文

**《子平真诠·论用神》（沈孝瞻原文）**：
> "财官印食，此用神之善而顺用之者也；煞伤劫刃，用神之不善而逆用之者也。当顺而顺，当逆而逆，配合得宜，皆为贵格。"

**《子平真诠·论用神成败救应》（沈孝瞻原文）**：
> "财生官旺，或财逢食生而身强带比，或财格透印而位置妥贴，两不相克，财格成也。"

#### ③ 授权级别评估

| 维度 | 评估 |
|------|------|
| 十神定义（我克者为财） | 🟢 所有命理书共识 |
| 财星的作用（耗身/生官/养命） | 🟡 有原典依据，但是双面的 |
| text_type | ORIGINAL（子平真诠） |
| verification_status | PARTIALLY_VERIFIED |
| 授权级别 | 🟡 PARTIAL |
| 最大输出 | QUALIFIED |
| 可否进入生产 | 🟡 RESEARCH/CANDIDATE |

#### ④ 关键边界

- **"财星出现"是结构事实**：确定的
- **"财星耗身"是作用之一**：我克者耗我力量，这是基础作用
- **"财星生官/养命"是作用之二**：也有原典依据
- **身旺能任财是好事，身弱财多是坏事（"富屋贫人"）**
- **不能简单说"财星 = 耗损"**：必须看具体语境

#### ⑤ Evidence 数据结构

```python
@dataclass(frozen=True)
class WealthDrainEvidence:
    evidence_id: str
    judgment_target: str
    polarity: str                 # "CONSTRAINT"（但标注双面性）
    value: dict
    # {
    #   "wealth_present": true,
    #   "wealth_count": 2,
    #   "wealth_details": [
    #     {"position": "month_stem", "stem": "戊", "type": "偏财", "rooted": true},
    #     {"position": "hour_stem", "stem": "己", "type": "正财", "rooted": false}
    #   ],
    #   "zhengcai_count": 1,
    #   "piancai_count": 1,
    #   "dual_nature": true
    # }
    source_fact_ids: list
    source_relation_ids: list
    derivation_rule_id: str
    classical_source: dict
    certainty_state: str
```

---

### L4-6：SEASONAL_STATE（季节状态）

#### ① 从哪个 Canonical Fact + Relation 得来

```
Canonical Fact:
  - DAY_MASTER（日主，如甲木）
  - MONTH_BRANCH（月支，如寅）
  - 五行属性（日主五行、月令五行）
  - 十二长生（日主在月令的长生状态）

Relation:
  - WUXING_RELATION（日主五行与月令五行的生克关系）
  - SEASONAL_ALIGNMENT（日主与月令的关系）
  - GROWTH_STAGE（十二长生状态）

Evidence Derivation:
  - 确定日主五行
  - 确定月令五行和季节
  - 确定日主在月令的十二长生状态
  - 确定寒暖燥湿状态
```

#### ② 原典原文

**《滴天髓》（原文）**：
> "能知衰旺之真机，其于三命之奥，思过半矣。"

**《滴天髓》（原注）**：
> "旺则宜泄宜伤，衰则喜帮喜助，子平之理也。然旺中有衰者存，不可损也；衰中有旺者存，不可益也。"

**《穷通宝鉴·五行总论》（原文）**：
> "北方阴极而生寒，寒生水。南方阳极而生热，热生火。东方阳散以泄而生风，风生木。西方阴止以收而生燥，燥生金。中央阴阳交而生温，温生土。"

**《穷通宝鉴·附论四时之火宜忌》（原文）**：
> "春月之火，母旺子相，势力并行。喜木生扶，不宜过旺，旺则火炎；欲水既济，不宜太多，多则火灭。"

#### ③ 授权级别评估

| 维度 | 评估 |
|------|------|
| 季节状态（春/夏/秋/冬） | 🟢 客观事实，确定的 |
| 寒暖燥湿 | 🟢 有原典依据（穷通宝鉴） |
| 日主在月令的状态（得令/失令） | 🟡 有原典依据，但"得令 ≠ 旺"需要授权 |
| text_type | ORIGINAL（滴天髓/穷通宝鉴）+ COMMENTARY（滴天髓原注） |
| verification_status | PARTIALLY_VERIFIED |
| 授权级别 | 🟡 PARTIAL |
| 最大输出 | QUALIFIED |
| 可否进入生产 | 🟡 RESEARCH/CANDIDATE |

#### ④ 关键边界

- **"季节"是客观事实**：春/夏/秋/冬，确定的
- **"寒暖燥湿"是季节属性**：有原典依据（穷通宝鉴）
- **"得令/失令"是关系描述**：日主与月令的关系，有原典依据
- **"得令 → 旺"是辨证判断**：原典明确警告"虽是至理，亦死法也"
- **季节状态是 CONTEXT，不是直接的 SUPPORT/CONSTRAINT**：它为其他 Evidence 提供语境

#### ⑤ Evidence 数据结构

```python
@dataclass(frozen=True)
class SeasonalStateEvidence:
    evidence_id: str
    judgment_target: str
    polarity: str                 # "CONTEXT"（语境，不是直接支持/制约）
    value: dict
    # {
    #   "season": "春",
    #   "month_branch": "寅",
    #   "day_master_wuxing": "木",
    #   "month_wuxing": "木",
    #   "growth_stage": "临官",
    #   "seasonal_alignment": "IN_SEASON",  # 得令
    #   "climate": {
    #     "temperature": "温",
    #     "humidity": "风",
    #     "dryness": "润"
    #   }
    # }
    source_fact_ids: list
    source_relation_ids: list
    derivation_rule_id: str
    classical_source: dict
    certainty_state: str
```

---

### L4-7：ENVIRONMENT_STATE（环境状态）

#### ① 从哪个 Canonical Fact + Relation 得来

```
Canonical Fact:
  - 所有干支的五行属性
  - 月令（决定基础寒暖燥湿）
  - 干支组合（可能改变基础环境）

Relation:
  - 五行分布统计（水火多少决定寒暖，木金多少决定燥湿）
  - 干支合化（可能改变五行属性）

Evidence Derivation:
  - 基于月令确定基础寒暖燥湿
  - 基于全局五行分布调整
  - 确定整体环境状态（偏寒/偏暖/偏燥/偏润/中和）
```

#### ② 原典原文

**《穷通宝鉴·五行总论》（原文）**：
> "北方阴极而生寒，寒生水。南方阳极而生热，热生火。东方阳散以泄而生风，风生木。西方阴止以收而生燥，燥生金。中央阴阳交而生温，温生土。其相生也所以相维，其相克也所以相制，此之谓有伦。"

**《穷通宝鉴·论土》（原文）**：
> "夏月之土，其势燥烈，得盛水滋润成功，忌旺火煆炼焦坼，木助火炎，水克无碍，金生水泛，妻才有益，见比肩蹇滞不通，如太过又宜木克。"

#### ③ 授权级别评估

| 维度 | 评估 |
|------|------|
| 寒暖燥湿的定义 | 🟢 有原典依据（穷通宝鉴） |
| 全局环境状态的判断 | 🟡 需要进一步授权（如何综合判断？） |
| text_type | ORIGINAL（穷通宝鉴） |
| verification_status | PARTIALLY_VERIFIED |
| 授权级别 | 🟡 PARTIAL |
| 最大输出 | QUALIFIED |
| 可否进入生产 | 🟡 RESEARCH/CANDIDATE |

#### ④ 关键边界

- **"寒暖燥湿"是五行属性**：有原典依据
- **"全局环境状态"是综合判断**：需要原典授权如何综合
- **环境状态是 CONTEXT**：为调候辨证提供语境，不是直接的旺衰判断
- **调候是独立的辨证目标**：不是旺衰的子集，《穷通宝鉴》有自己的体系

#### ⑤ Evidence 数据结构

```python
@dataclass(frozen=True)
class EnvironmentStateEvidence:
    evidence_id: str
    judgment_target: str          # "CLIMATE_ADJUSTMENT"（调候，独立目标）
    polarity: str                 # "CONTEXT"
    value: dict
    # {
    #   "base_climate": {"season": "夏", "temp": "热", "humidity": "燥"},
    #   "global_climate": {
    #     "water_count": 1,
    #     "fire_count": 3,
    #     "wood_count": 2,
    #     "metal_count": 1,
    #     "earth_count": 1,
    #     "overall": "偏燥热"
    #   },
    #   "adjustment_needed": true,
    #   "primary_adjustment": "水"（调候用神候选）
    # }
    source_fact_ids: list
    source_relation_ids: list
    derivation_rule_id: str
    classical_source: dict
    certainty_state: str
```

---

### L4-8：STRUCTURAL_CHANGE（结构变化）

#### ① 从哪个 Canonical Fact + Relation 得来

```
Canonical Fact:
  - 所有干支
  - 地支藏干

Relation:
  - 刑（寅巳申三刑、丑戌未三刑等）
  - 冲（子午冲、丑未冲、寅申冲等）
  - 合（天干五合、地支六合、三合局）
  - 害（子未害、丑午害等）
  - 破（子酉破、卯午破等）

Evidence Derivation:
  - 扫描所有干支组合，找出刑冲合害破
  - 记录涉及的干支、位置
  - 记录对基础结构的影响（根被冲、合化等）
```

#### ② 原典原文

**《滴天髓》（原文）**：
> "生方怕动库宜开，败地逢冲仔细推。"

**《子平真诠·论用神成败救应》（沈孝瞻原文）**：
> "如官逢财印，又无刑冲破害，官格成也。"

#### ③ 授权级别评估

| 维度 | 评估 |
|------|------|
| 刑冲合害破的定义 | 🟢 所有命理书共识，确定的 |
| 结构变化对基础事实的影响 | 🟡 需要进一步授权（如何影响？） |
| text_type | ORIGINAL（滴天髓/子平真诠） |
| verification_status | PARTIALLY_VERIFIED |
| 授权级别 | 🟡 PARTIAL |
| 最大输出 | QUALIFIED |
| 可否进入生产 | 🟡 RESEARCH/CANDIDATE |

#### ④ 关键边界

- **"刑冲合害破"是结构关系**：确定的
- **"结构变化"是对基础事实的修改**：如根被冲，则 ROOT_PRESENT 的有效性改变
- **结构变化是 MODIFIER**：它不直接支持/制约，而是修改其他 Evidence 的有效性
- **"刑冲合害 → 吉凶"是辨证判断**：需要原典授权，不能直接推导

#### ⑤ Evidence 数据结构

```python
@dataclass(frozen=True)
class StructuralChangeEvidence:
    evidence_id: str
    judgment_target: str
    polarity: str                 # "MODIFIER"（修饰符，修改其他Evidence）
    value: dict
    # {
    #   "changes_present": true,
    #   "changes": [
    #     {
    #       "type": "clash",  # 冲
    #       "involved": ["子", "午"],
    #       "positions": ["year_branch", "hour_branch"],
    #       "affects": ["ROOT_PRESENT"],  # 影响哪些Evidence
    #       "effect": "root_damaged"
    #     },
    #     {
    #       "type": "combine",  # 合
    #       "involved": ["甲", "己"],
    #       "positions": ["day_stem", "month_stem"],
    #       "affects": ["DAY_MASTER"],
    #       "effect": "day_master_combined"
    #     }
    #   ],
    #   "root_damaged": true,
    #   "day_master_combined": false
    # }
    source_fact_ids: list
    source_relation_ids: list
    derivation_rule_id: str
    classical_source: dict
    certainty_state: str
```

---

## 三、L4 Evidence 授权状态汇总

| 编号 | Evidence ID | 名称 | 极性 | 授权级别 | 最大输出 | 可否生产 | 关键边界 |
|------|-------------|------|------|---------|---------|---------|---------|
| L4-1 | RESOURCE_SUPPORT | 印生身 | SUPPORT | 🟡 PARTIAL | QUALIFIED | 🟡 | 印多可能"母慈灭子" |
| L4-2 | PEER_SUPPORT | 比劫帮身 | SUPPORT | 🟡 PARTIAL | QUALIFIED | 🟡 | 双面性：帮身/夺财 |
| L4-3 | OFFICER_CONTROL | 官杀克身 | CONSTRAINT | 🟡 PARTIAL | QUALIFIED | 🟡 | 双面性：克身/制比劫/护财；正官/七杀不同 |
| L4-4 | OUTPUT_DRAIN | 食伤泄身 | CONSTRAINT | 🟡 PARTIAL | QUALIFIED | 🟡 | 双面性：泄身/生财/制杀；食神/伤官不同 |
| L4-5 | WEALTH_DRAIN | 财星耗身 | CONSTRAINT | 🟡 PARTIAL | QUALIFIED | 🟡 | 双面性：耗身/生官/养命 |
| L4-6 | SEASONAL_STATE | 季节状态 | CONTEXT | 🟡 PARTIAL | QUALIFIED | 🟡 | 得令 ≠ 旺；是语境不是直接判断 |
| L4-7 | ENVIRONMENT_STATE | 环境状态 | CONTEXT | 🟡 PARTIAL | QUALIFIED | 🟡 | 调候是独立目标，不是旺衰子集 |
| L4-8 | STRUCTURAL_CHANGE | 结构变化 | MODIFIER | 🟡 PARTIAL | QUALIFIED | 🟡 | 修饰其他Evidence，不直接支持/制约 |

### 关键发现

1. **十神定义都是 AUTHORIZED**：生我者为印、同我者为比劫、克我者为官杀、我生者为食伤、我克者为财——这些是所有命理书共识，确定的。

2. **十神作用都是 PARTIAL**：印生身、比劫帮身、官杀克身、食伤泄身、财星耗身——这些有原典依据，但都是双面的，不能简单等同于支持/制约。

3. **没有一类 L4 Evidence 是 AUTHORIZED 到可以直接 CONFIRMED**：所有 L4 Evidence 最多输出 QUALIFIED，因为"十神作用 → 旺衰判断"这一步需要原典授权的 Combination 规则。

4. **极性不是简单的 SUPPORT/CONSTRAINT**：
   - SEASONAL_STATE 和 ENVIRONMENT_STATE 是 CONTEXT（语境）
   - STRUCTURAL_CHANGE 是 MODIFIER（修饰符）
   - 十神类 Evidence 都有双面性标记

5. **L4 Evidence 只是局部证**：它们回答的是"命局中有没有 X"，不是"所以身强/身弱"。

---

## 四、L4 Evidence Derivation 标准接口

### 4.1 统一接口

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass(frozen=True)
class CanonicalFact:
    fact_id: str
    fact_type: str
    value: dict
    source: str
    certainty: str  # "CALCULATED" / "DERIVED" / "UNKNOWN"

@dataclass(frozen=True)
class SemanticRelation:
    relation_id: str
    relation_type: str  # "WUXING_GENERATES" / "SAME_ELEMENT" / ...
    source_fact_id: str
    target_fact_id: str
    value: dict
    certainty: str

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    evidence_type: str  # "RESOURCE_SUPPORT" / "PEER_SUPPORT" / ...
    judgment_target: str
    polarity: str  # "SUPPORT" / "CONSTRAINT" / "CONTEXT" / "MODIFIER"
    value: dict
    source_fact_ids: List[str]
    source_relation_ids: List[str]
    derivation_rule_id: str
    classical_source: dict  # Provenance
    certainty_state: str  # "DERIVED" / "QUALIFIED" / "UNKNOWN" / "UNRESOLVED"

class EvidenceDerivationRule(ABC):
    """Evidence 推导规则基类"""
    
    @property
    @abstractmethod
    def rule_id(self) -> str:
        pass
    
    @property
    @abstractmethod
    def evidence_type(self) -> str:
        pass
    
    @property
    @abstractmethod
    def classical_source(self) -> dict:
        pass
    
    @abstractmethod
    def derive(self, facts: List[CanonicalFact], 
               relations: List[SemanticRelation]) -> Optional[Evidence]:
        pass
```

### 4.2 推导流程

```
Canonical Facts
    ↓
Semantic Relations（从 Facts 派生）
    ↓
Evidence Derivation Rules（逐条应用）
    ↓
L4 Evidence 集合
    ↓
（等待 L6 Evidence Combination 授权后才进入 Judgment）
```

---

## 五、下一步行动

### 5.1 立即执行

1. ✅ **L4 Evidence 清单和授权审计**（本文档）
2. ⏳ **实现 L4 Evidence Derivation 代码**：8 类 Evidence 的推导规则
3. ⏳ **验证 L4 Evidence**：用测试命例验证推导正确性

### 5.2 高优先级（下一步）

1. **P0-2.7.3 L5 Structural Change Evidence**：结构变化对基础事实的影响
2. **P0-2.7.4 Evidence Combination Authorization 研究**：原典中有没有明确的证据组合规则？
3. **P0-2.7.5 Classical Judgment Strategy**：五部经典各自的辨证策略

### 5.3 绝对禁止

1. ❌ **禁止写 strength_engine.py**：在 Evidence Combination 规则没有原典授权之前
2. ❌ **禁止用数量统计直接判断强弱**：支持 > 克泄耗 → 身强
3. ❌ **禁止把 L4 Evidence 直接当旺衰判断**：它们只是局部证
4. ❌ **禁止跳过 Combination 直接进入 Judgment**

---

## 六、总结

### 本次设计的核心成果

1. ✅ **建立了 L4 Evidence 完整清单**：8 类（印生身、比劫帮身、官杀克身、食伤泄身、财星耗身、季节状态、环境状态、结构变化）
2. ✅ **逐条做了原典授权审计**：每类 Evidence 都明确了来源、原典依据、授权级别、关键边界
3. ✅ **明确了所有 L4 Evidence 都是 PARTIAL**：最多输出 QUALIFIED，没有一类可以直接 CONFIRMED
4. ✅ **区分了极性类型**：SUPPORT / CONSTRAINT / CONTEXT / MODIFIER，不是简单的支持/制约
5. ✅ **标记了十神 Evidence 的双面性**：比劫（帮身/夺财）、官杀（克身/制比劫/护财）等
6. ✅ **建立了标准 Evidence Derivation 接口**：统一的数据结构和推导流程
7. ✅ **明确了绝对禁止事项**：不写 strength_engine.py、不用数量统计、不跳过 Combination

### 最重要的一句话

> **L4 Evidence 只是局部证，不是旺衰判断。命局中有印、有比劫、有官杀、有食伤、有财，这些都是确定的结构事实；但"这些加起来所以身强/身弱"这一步，需要原典授权的 Evidence Combination 规则。在 Combination 规则没有授权之前，所有 L4 Evidence 最多输出 QUALIFIED，整体旺衰判断保持 UNRESOLVED / NOT_DEFINED。**

这才是"算准 → 辨准"真正应该有的工程纪律。

---

*本设计文档是 P0-2.7.2 L4 Evidence Construction 的成果。通过对 8 类 L4 Evidence（RESOURCE_SUPPORT、PEER_SUPPORT、OFFICER_CONTROL、OUTPUT_DRAIN、WEALTH_DRAIN、SEASONAL_STATE、ENVIRONMENT_STATE、STRUCTURAL_CHANGE）逐条做原典授权审计，明确了每类 Evidence 的来源、原典依据、授权级别、关键边界和数据结构。核心结论：所有 L4 Evidence 都是 PARTIAL，最多输出 QUALIFIED；它们只是局部证，不是旺衰判断；在 Evidence Combination 规则没有原典授权之前，整体旺衰判断保持 UNRESOLVED / NOT_DEFINED。*
