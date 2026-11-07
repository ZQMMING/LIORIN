# PATCH-003A Classical Scope Normalization（古典职责归一化）

> 日期：2026-09-16 ｜ Human 拍板：SIX_CLASSICS_SCOPE_MATRIX = Recall/Scope Draft，**不得作 Rule Routing**
> 本阶段目标：术语簇 + 职责类型 + EXCLUDED_SCOPE + hit_count 与 classical_scope 分离

## 一、Human 裁决落档（禁止推翻）

1. **命中数量 ≠ 经典职责**：SMTH 十神 304 / SFTK 十神 408 不能推出「SFTK 更负责十神」——hit_count 只是 keyword_hit_count，不是 scope_priority
2. **主轴定位逐条须有原文**：engine_role（工程标签）≠ classical_rule（规则证据），如「DTS=辩证状态关系引擎」不能成为 Rule 证据
3. **得势 0/1/2/3 命中不能裁决**：可能存在持勢/黨多/勢眾/勢盛/氣勢/黨勢等原文表达；关键词扫描结果只能作 Recall，不是 Evidence（调候=QTBJ 反例已证）
4. **28 领域必须建术语别名/原文表达簇**：否则 Agent 漏项

## 二、中间层结构（新增，冻结）

```
28 DOMAIN
   ↓
CLASSICAL_TERM_CLUSTER（后世术语 + 六部原文异名/表达簇）
   ↓
SOURCE（source_id）
   ↓
CHAPTER（书×章节）
   ↓
ORIGINAL_TEXT（原文逐字）
   ↓
SEMANTIC_ROLE（YES / NO / CONTEXTUAL / UNKNOWN）
   ↓
VERIFIED_SCOPE（NOT_FOUND / REFERENCE / FACT / CONDITION / JUDGMENT /
                 PRIMARY / SECONDARY / CONTEXTUAL / UNVERIFIED）
```

规则：术语命中不得自动产生语义归类；OCR/关键词命中必须先过 SEMANTIC_ROLE 判定。

## 三、职责类型体系（VERIFIED_SCOPE 值域草案）

| 类型 | 含义 |
|---|---|
| NOT_FOUND | 该经典该领域无原文（须全簇扫描确认） |
| REFERENCE | 仅引述/汇编他书，无本书方法 |
| FACT | 提供事实（如五行生克表），不产判断 |
| CONDITION | 作为其他规则的条件变量（如 PZZQ 身强是格局条件） |
| JUDGMENT | 直接产出贵贱/成败/吉凶判断 |
| PRIMARY | 该经典该领域的主责域（大量原文+明确方法） |
| SECONDARY | 有原文但非主责 |
| CONTEXTUAL | 仅在具体语境中出现，不得泛化 |
| UNVERIFIED | 待逐条原文核验 |

## 四、hit_count 与 classical_scope 分离（schema 冻结）

每格必须并存以下字段，Agent 只消费后两项：

```
domain_id
book_id
hit_count          ← 仅作 Recall 索引，不得作职责依据
source_count       ← 去重 source 数
chapter_count      ← 覆盖章节数
term_cluster_used  ← 本次扫描所用术语簇（可回溯）
verified_scope     ← 语义归类结果（9 类）
scope_priority     ← PRIMARY / SECONDARY / CONTEXTUAL / EXCLUDED
```

## 五、28 领域术语簇初稿（CLASSICAL_TERM_CLUSTER）

> 标注：〔已扫描〕= 六部原文数据已提取；〔待核〕= 簇内词需逐条回原文判定

| 领域 | 后世术语 | 六部原文异名/表达簇（初稿） |
|---|---|---|
| 01 基础五行 | 五行生克 | 五行/生剋/制化/洩氣/泄耗/相生/相尅/相濟/太過/不及〔已扫描〕 |
| 02 十神 | 十神 | 正官/七殺/偏官/正財/偏財/正印/偏印/梟/食神/傷官/比肩/劫財/倒食/正夫/偏夫/夫星/子星〔已扫描〕 |
| 03 月令 | 月令 | 月令/提綱/月支/司令/當權/司權/得令/失令/月提〔已扫描〕 |
| 04 生旺休囚 | 十二长生 | 生旺/休囚/死絕/長生/沐浴/冠帶/臨官/帝旺/墓庫/入墓/死地/絕地/胎/養〔已扫描〕 |
| 05 旺 | 旺 | 身旺/太旺/旺相/旺極/日主旺/主旺/旺之極/旺氣/旺勢/當權得令〔已扫描〕 |
| 06 强 | 强 | 身強/太強/日主強/主強/強旺/強殺/身強殺淺/遇劫為強〔已扫描〕 |
| 07 根气 | 根 | 無根/有根/通根/得根/根氣/根深/根淺/歸祿/坐祿/得祿/以年爲根/根在苗先/根荄/根柢/移根換葉〔已扫描〕 |
| 08 得令 | 得令 | 得令/失令/當權/司令/司權/得時/失時/提綱得令/當權得令/旺中得令〔已扫描〕 |
| 09 得地 | 得地 | 得地/得垣/歸垣/得根/有根/通根/根氣/坐祿/得祿/歸祿/根深/根淺/得局〔已扫描〕 |
| 10 得势 | 得势 | 得勢/失勢/持勢/氣勢/旺勢/勢旺/大勢/情勢/從勢/其勢已成/勢在於X/黨多/勢眾/黨勢〔已扫描〕 |
| 11 党众 | 党众 | 黨/黨多/成黨/一黨/勢眾/眾寡/黨勢/比肩成黨〔待核〕 |
| 12 生扶克泄耗 | 生扶克泄 | 生扶/扶身/幫身/助身/尅泄/洩耗/耗氣/生扶/泄秀/制化〔已扫描〕 |
| 13 气势 | 气势 | 氣勢/旺勢/勢旺/大勢/其勢已成/勢在於X/順其氣勢/情勢〔已扫描〕 |
| 14 格局 | 格局 | 格局/成格/破格/入格/格成/格敗/敗格/有格/無格/格之高低〔已扫描〕 |
| 15 格局成败 | 成败救应 | 成格/敗格/敗局/救應/成局/破局/格之成/格之敗/損益〔已扫描〕 |
| 16 用神 | 用神 | 用神/喜神/忌神/相/輔我用神者/真神/假神/調候用神〔已扫描〕 |
| 17 相神 | 相神 | 相/輔我用神者/用神之相〔已扫描〕 |
| 18 顺逆 | 顺逆 | 順用/逆用/順生/逆生/順之/逆之/順勢/逆勢〔待核〕 |
| 19 清浊 | 清浊 | 清濁/清氣/濁氣/清者/濁者/清奇/混/雜〔已扫描〕 |
| 20 真假 | 真假 | 真假/真神/假神/真化/假化/真從/假從/真者/假者/真機〔已扫描〕 |
| 21 调候 | 调候 | 寒/暖/燥/濕/溫/冷/潤/枯/凍/解凍/餘寒/三伏生寒/寒木向陽/旱田/退氣/進氣〔已扫描〕 |
| 22 病药 | 病药 | 病藥/去病/藥神/有病/病者/藥者/病/藥/從重者論〔已扫描〕 |
| 23 通关 | 通关 | 通關/引通/關通/引化〔待核〕 |
| 24 从化专旺 | 从化 | 從象/化象/專旺/炎上/稼穡/從革/潤下/曲直/從兒/從財/從殺/棄命/歸垣得局〔已扫描〕 |
| 25 干支组合 | 干支关系 | 合局/會局/三合/六合/暗合/刑沖/沖破/相沖/地支/天干/伏吟/反吟〔已扫描〕 |
| 26 六亲 | 六亲 | 六親/父母/夫妻/妻妾/子息/兄弟/尅父/尅母/尅妻/妨夫/刑夫/尅子/夫星/子星〔已扫描〕 |
| 27 神煞 | 神煞 | 神煞/貴人/羊刃/桃花/驛馬/華蓋/魁罡/天德/月德/亡神/空亡〔已扫描〕 |
| 28 命例验证 | 命例 | 此命/一命/命例/驗之/余驗/屢驗/驗〔已扫描〕 |

## 六、第一批语义归类初稿（勢/根/令/旺/強——基于已提取原文）

### 10 得势——六部「勢」表达（关键词命中 ≠ 现代「日主得势」）
| 表达 | 出处 | SEMANTIC_ROLE（初判） |
|---|---|---|
| 「氣不從勢」「五陰從勢無情義」「其性從勢」 | DTS-008-003/004 天干 | CONTEXTUAL——从势/不从势（天干性质），非日主得势 |
| 「其勢已成」「順其氣勢而已矣」 | DTS-025-001/002 順逆 | CONTEXTUAL——气势已成则顺，结构关系 |
| 「勢在於官」「勢在於煞」 | DTS-020-002 官煞論 | CONTEXTUAL——势之所在（官/煞），非日主 |
| 「看其大勢」 | DTS-013-005 八格論 | CONTEXTUAL——大局之势 |
| 「自恃旺勢而行純」 | YHZP-076-105 喜忌篇注 | CONDITION——身旺之势作条件 |
| 「火之勢急」「渾然成勢」 | YHZP-101-006 外十八格 | CONDITION——炎上格成势 |
| 「水勢滔滔」「火勢炎炎」 | YHZP-131-001 寸金搜髓論 | CONDITION——五行之势 |
| 「此制於勢也」 | PZZQ-005-004 論干支 | CONTEXTUAL——制与势的关系 |
| 「全用之勢而斷之」 | PZZQ-007-025 用神格局高低 | CONDITION——用神之势 |
| 「但恐身勢無力」 | YHZP-085-001 論偏財 / SFTK-020-021 | CONDITION——**身势无力**（日主相关！） |
| 「水而其勢已倒敗」「在休囚勢自偏」 | SMTH-023-001 戰關 | CONDITION——势与休囚相关 |
| 「其勢要多方」 | DTS-048-002 君象 | CONTEXTUAL——君之势 |

**初判结论**：六部「勢」是**结构关系/五行之势**概念，日主层面近义表达仅「身勢無力」（YHZP/SFTK）；**现代「日主得势」无直接原文对应**——维持第二批倾向，待全簇核验。

### 07/09 根气/得地——六部「根」表达
| 表达 | 出处 | SEMANTIC_ROLE（初判） |
|---|---|---|
| 「四柱無根，得時爲旺」 | YHZP-138-001 子機賦 | CONDITION——日主无根+得时→旺 |
| 「日主無根」「或有根者不吉」 | YHZP-123-003 從象 | CONDITION——从格根判定 |
| 「不論有根無根，俱要天覆地載」 | DTS-010-003 干支論 | FACT——干支论总原则 |
| 「亦為有根」「陽為有根而陰則…」 | PZZQ-005-002 論干支 | FACT——阴阳根性 |
| 「強殺無根喜財旺」「弱殺有根喜食印」 | SFTK-043-003-06 歲德扶殺 | CONDITION——**根的对象是殺非日主**！ |
| 「日主無根遇地支」 | SFTK-058-010 類象 | CONDITION |
| 「財弱無根」 | SFTK-020-021 | CONDITION——财星无根 |
| 「乙木根荄種得」 | QTBJ-014-001 | CONDITION——调候中根 |
| 「干旺則根深」「根在苗先」 | YHZP-071-005 定眞論 | FACT——根苗理论 |
| 「以年爲根月爲苗」 | SFTK-128-010 定真篇 | FACT——年根月苗 |

**初判结论**：六部「根」的对象多样（日主/殺/財/陰陽），**不得统一按日主根处理**；「得地」同族（得垣/歸垣/坐祿/得祿）对象也须逐条核。

## 七、EXCLUDED_SCOPE 初稿（禁止借补规则）

| 经典 | PRIMARY | CONTEXTUAL（可用但须语境绑定） | EXCLUDED（NOT_PRIMARY，禁泛化） |
|---|---|---|---|
| PZZQ | 月令→用神→格局→成败救应 | 身强/身弱（格局条件） | 调候式逐月寒暖体系 |
| DTS | 旺衰变化/气势/清浊/真假/从化 | 身旺/身弱（注家层 B） | 不得以注家算法当正文；不得当十神基础教材 |
| QTBJ | 日干×月令×四时×寒暖燥湿 | 格局/身强弱 | **不得把逐月调候条件泛化成通用旺衰公式** |
| SMTH | 干支组合/神煞/日时断语/命例 | 格局/旺衰（具体断语） | 日时断语不得抽取为通用判定规范 |
| SFTK | 病→药→去病→救应→验证 | 格局/旺弱（病药框架内） | 不得把病药逻辑当全引擎通用 |
| YHZP | 基础框架/十神/生旺死绝/格局 | 旺衰/得令（喜忌条件） | 非单独旺衰算法引擎 |

规则：Agent 在某经典找不到规则时，**不得自动借另一经典补规则**（V2.22 Public Contract 语义）。

## 八、执行记录（2026-09-16）

1. Human 裁决落档（4 锁定问题）✅
2. 中間層結構 + VERIFIED_SCOPE 值域 + schema 冻结 ✅
3. 28 领域术语簇初稿（勢/根/令/旺/強 已扫描提取）✅
4. 第一批语义归类初稿（勢/根 已落）✅
5. EXCLUDED_SCOPE 初稿 ✅
6. 待办：全簇逐条 SEMANTIC_ROLE → 28×6 VERIFIED_SCOPE 逐格定稿 → PATCH-003B 逐章节 Evidence Verification

---

# PATCH-003A 完整复裁（Human 2026-09-16 二轮，覆盖初稿）

## 一、总裁决
| 项 | 裁决 |
|---|---|
| PATCH-003A 总体架构 | PASS |
| 语义字段继续修订 | REQUIRED（本复裁执行） |
| 003B 逐章节 Evidence Verification | HOLD（暂缓） |
| strength_source 枚举 | HOLD（仅 Registry 候选，不立即 Admission） |
| ruling_schedule 比例模型 | **REJECT**（删除） |
| ruling_schedule 时段模型 | PASS（按原典时间节点记录） |
| 13 字段 | INSUFFICIENT → 16 字段（加 relation_type/source_basis/condition_context） |
| 旺≠强 | PASS（锁定） |
| 得令≠身强 | PASS（锁定+对象化限定） |
| 势≠强 | PASS（锁定；TREND_STATE≠STRENGTH_STATE） |
| 根对象化 | PASS（锁定） |
| 根≠得地 | PASS（锁定，本复裁新增） |
| 时≠令≠得令 | PASS（锁定） |

## 二、修正与新增（相对初稿）

### 2.1 STRENGTH_SOURCE 候选 Registry（不冻结，待证据绑定）
`
STRENGTH_SOURCE（候选）
    SEASONAL_ORDER        ← 得時/得令类
    ROOT                  ← 根类
    SUPPORT               ← 生扶类
    QI_TREND              ← 气势类
    STRUCTURAL_RELATION   ← 结构关系类
    COMBINATION_TRANSFORMATION ← 合化类
    SELF_NATURE           ← 本性类
    UNDETERMINED
`
依据：YHZP-138-001 同时出现「得時俱爲旺論」「四柱無根得時爲旺」「日干無氣遇劫爲強」「身旺印多」「身旺喜逢祿馬」——来源不止四类；「得時」不能简单塞进 MONTH_ORDER。

### 2.2 旺≠强（锁定）
DTS 衰旺論：「旺中有衰者存」「衰中有旺者存」「旺之極者不可損」「衰之極者不可益」——旺内部有衰；「體用皆旺，不分勝負」——旺可为体用关系状态。
硬规则：**FORBIDDEN: prosperity_state==WANG → strength_state=STRONG**

### 2.3 得令≠身强 + 对象化（锁定）
DTS 月令論：「令星，乃命之至要，宜氣象得令者吉，喜神得令者吉」；真假論：「命之真者得令」「假神得局而黨多」。
得令对象 ≠ 只有日主（气象/喜神/真神/用神相关）。
`
GET_ORDER_RELATION
    object       = ?
    month_order  = ?
    relation     = GET_ORDER / NOT_GET_ORDER / UNDETERMINED
`
禁止：daymaster_get_order=true → body_strength=strong

### 2.4 「得時俱爲旺論」定层（PATCH-002 约束继承）
- DTS 原文只有：「旺則宜泄宜傷」「旺中有衰者存…」
- 「得時俱爲旺論，失令便作衰看，雖是至理，亦死法也」=《滴天髓闡微》任氏阐释 → **ANNOTATION/B**，不得升级 DTS 正文

### 2.5 令拆三层（PASS）
`
MONTH_ORDER（月支/提纲）        ← DTS「月令提綱，譬之宅也」
ORDER_RELATION（OBJECT↔月令）   ← GET_ORDER_RELATION
RULING_ELEMENT（令星用事）      ← DTS「人元用事之神，宅之向也」
`
寅月用事原文：立春後七日前戊土用事 / 八日後十四日前丙火用事 / 十五日後甲木用事。

### 2.6 RULING_ELEMENT_SCHEDULE（时段模型，否决比例）
`
RULING_ELEMENT_SCHEDULE
    month_branch / hour_branch
    start_boundary / end_boundary   ← 原典时间节点（第7日前/第8-14日/15日後）
    ruling_element
    source_id / chapter_id / evidence_grade
`
DTS 生時論：「子時前三刻三分壬水用事，後四刻七分癸水用事」——**时支内部也有分段**；TIME_POSITION → RULING_SCHEDULE，非 MONTH_BRANCH→单一主气。

### 2.7 TIME_DOMAIN 拆层
`
TIME_DOMAIN
    BIRTH_TIME / SEASONAL_TIME / MONTH_ORDER
    MONTH_RULING_SCHEDULE / HOUR_BRANCH / HOUR_RULING_SCHEDULE
    GET_TIME_RELATION / TIMING_POSITION
`
依据：YHZP「以日爲主，年爲本，月爲提綱，時爲輔佐」；DTS 生時論。时≠月令≠得令≠令星用事≠得时。

### 2.8 根对象化 + 根≠得地（锁定）
- SFTK：「官星無根，官從何出」「財星無根，財從何生」「弱而有根，則官星雖弱而可致其旺」→ ROOT 对象：DAYMASTER/OFFICIAL/WEALTH/OTHER_TEN_GODS/FIVE_ELEMENTS
- SMTH：「地支至切，黨盛爲強」「宅舍即得地之方」「力輕、力重」「衝起、拱起、刑起、合起」→ 得地=地支承載+黨眾+力量+沖合刑拱+對象，**ROOT≠GET_GROUND**

### 2.9 势不冻结唯一语义
勢 ≥ QI_TREND / STRUCTURAL_TREND / DIRECTION / GROUP_FORCE / PATTERN_TREND
- SMTH：「力勢衝起/拱起/刑起/合起」（地支判断）
- DTS：「其勢沖奔，不可遏也」+ 顺势/从势论述
- TREND_STATE≠STRENGTH_STATE；TREND_STATE 内部枚举暂缓（待六部语义审计完成）

### 2.10 旺必须 OBJECT（新增硬要求）
旺可描述：DAYMASTER / FIVE_ELEMENT / TEN_GOD / QI / PATTERN / USEFUL_GOD / STRUCTURAL_GROUP
SFTK 同段：「印星太旺」「日干太旺」「官星太弱」「財星太弱」「日主太弱」——prosperity_state=WANG 无对象=不完整数据。

## 三、16 字段 schema（冻结）
`
domain_id / term_cluster_id / surface_form
object_type / relation_type / semantic_role / semantic_definition
source_id / chapter_id / text_layer / source_basis / condition_context
verified_scope / scope_priority / excluded_scope / evidence_grade
`
relation_type 值域（候选）：GET_ORDER / ROOTED_IN / SUPPORTED_BY / TREND_TO / PROSPEROUS_IN / COMBINE / OTHER / UNDETERMINED——防 Rule Engine 压成 STATE=TRUE。

## 四、003A-RULE-01~10（Human 拍板锁定）
`
01 hit_count ≠ classical_scope
02 engine_role ≠ classical_rule
03 WANG ≠ STRONG
04 GET_ORDER ≠ STRONG
05 ROOT ≠ GET_GROUND
06 TREND ≠ STRENGTH
07 TIME ≠ MONTH_ORDER ≠ GET_ORDER ≠ RULING_SCHEDULE
08 ROOT/WANG/QI/STRENGTH 必须先确定 OBJECT
09 RULING_SCHEDULE 必须记录时间边界，不得转换为比例权重
10 任何经典缺规则，禁止自动借另一经典补齐
`

## 五、最终数据模型（11 层，中间任何层无证据不得跳层）
`
DOMAIN → TERM_CLUSTER → SURFACE_FORM → OBJECT → RELATION → SEMANTIC_ROLE
→ SOURCE(BOOK+CHAPTER+TEXT_LAYER) → CONDITION_CONTEXT → VERIFIED_SCOPE → RULE → BUSINESS_JUDGMENT
`

## 六、六部职责边界修正（Scope Routing 候选，非规则依据）
- YHZP：玄機賦「四柱無根得時爲旺」「日干無氣遇劫爲強」——可入旺衰 Primary Evidence Candidate，每条绑原章节
- PZZQ：月令/用神/格局关系候选 Primary；「用神專求月令」框架须与格局成败条件一起处理，不得抽一句成全局强弱公式
- DTS：严格区分 ORIGINAL / ORIGINAL+原注 / 闡微任氏三层；「得時俱爲旺論」不得冒充原文
- QTBJ：「八月辛金，當權得令，旺之極矣」+ 水土火甲条件——不得抽成通用 DAYMASTER_STRENGTH
- SMTH：「地支至切，黨盛爲強」——规则必须 chapter/context bound
- SFTK：病药/旺弱/根/救应/实战辨析；引文四层（ORIGINAL/ANNOTATION/QUOTED_SOURCE/UNVERIFIED）继续执行

## 七、最终执行顺序（冻结）
1. 本复裁落档（完成）
2. 完整审「令/旺/強/時/地」五术语簇（现代术语+异称+古代表达+对象+关系+章节上下文）
3. 28×6 VERIFIED_SCOPE
4. PATCH-003B 逐章节 Evidence Verification
