# PATCH-003 Classical Concept Audit：身旺/身強/身弱/身衰（第一批 · 初稿）

> 日期：2026-09-16 ｜ 状态：AUDIT_DRAFT（待 Human 审批）
> 方法：六部 source 全量关键词扫描（520 条命中）→ 按书×章节聚合 → 语境组归类 → 逐组定 text_layer/grade
> 铁律：**不建立统一概念库，先建立经典语境概念库**；「身弱」只是文字相同不一定是 Concept 相同
> 数据：YHZP 57 / PZZQ 17 / DTS 11 / QTBJ 23 / SMTH 194 / SFTK 218

---

## 一、六部语境矩阵（Concept ID 草案 · 全部 PENDING）

### 1. 渊海子平（YHZP）57 条

| 语境组 | 章节 | 代表原文 | layer/grade | 语义域 | 状态枚举草案 | 允许 Rule |
|---|---|---|---|---|---|---|
| YHZP-身旺弱-总论 | 論月令/子平舉要歌/寸金搜髓論 | 「以日主大要看日加臨於甚度，或身旺或身弱」；「坐官坐印衰旺取」；「身旺財官多富貴」 | ORIGINAL/A | 日主基础状态（判定起点） | 需 strength_state | PENDING |
| YHZP-身旺弱-七杀 | 論偏官/論七殺 | 「喜身旺合殺喜制伏；忌身弱」「身旺有氣爲偏官，身弱無制爲七殺」 | ORIGINAL/A | 七杀喜忌依赖身旺弱 | CONDITION_STATE | PENDING |
| YHZP-身旺弱-財 | 論正財/論偏財 | 「故財要得時…樂於身旺」「身弱兄弟姊妹有奪之則福不全」 | ORIGINAL/A | 财星任受依赖身旺弱 | CONDITION_STATE | PENDING |
| YHZP-身旺弱-食傷 | 論食神/論傷官 | 「喜身旺」「亦要身旺」 | ORIGINAL+ANN | 食伤格局条件 | CONDITION_STATE | PENDING |
| YHZP-身旺弱-格局喜忌 | 喜忌篇/正氣官星/丙十八格/外十八格 | 「四柱殺旺運純身旺爲官清貴」「身旺逢正氣官星…必登科」 | ORIGINAL/A（含注 B/批 C） | 格局成立条件 | CONDITION_STATE | PENDING |
| YHZP-身旺弱-羊刃神煞 | 論羊刃/論日德/論日刃/論魁罡 | 「大要身旺，運行身旺之鄉」 | ORIGINAL/A | 运行喜忌 | CONDITION_STATE | PENDING |
| YHZP-身旺弱-六親 | 論父/論妻妾/婦人/陰命賦 | 「身旺財旺，主得父力」「財多身弱」 | ORIGINAL/A+ANN | 六亲断语 | CONDITION_STATE | PENDING |
| YHZP-身旺弱-从象反例 | 神趣八法·鬼象 | 「而又身旺則不吉」 | ORIGINAL/A | **从格语境：身旺反凶** | CONDITION_STATE | PENDING（特殊） |

### 2. 子平真诠（PZZQ）17 条

| 语境组 | 章节 | 代表原文 | layer/grade | 语义域 | 状态枚举草案 | 允许 Rule |
|---|---|---|---|---|---|---|
| PZZQ-身旺弱-用神格局 | 論用神格局高低（15条） | 「身旺不勞印生，印旺何勞煞助」「身強印旺透煞，孤貧」「身弱逢之，最喜印旺」 | ORIGINAL/A | 格局成败/取运依赖 | CONDITION_STATE | PENDING |
| PZZQ-身旺弱-用神框架 | 論干支 | 「八字用神，專求月令」 | ORIGINAL/A | 用神框架 | — | PENDING |

**特征**：语境高度单一集中——全部在「用神格局」框架内。

### 3. 滴天髓（DTS）11 条

| 语境组 | 章节 | 代表原文 | layer/grade | 语义域 | 状态枚举草案 | 允许 Rule |
|---|---|---|---|---|---|---|
| DTS-身強弱-从儿 | 六親論·順局 | 「從兒不論身強弱，只要吾兒又遇兒」 | **ORIGINAL/A（唯一正文）** | 从格：不论身强弱 | PATTERN_STATE | PENDING |
| DTS-身旺弱-注家 | 通天論（中和/傷官/清濁/震兌坎離）、六親論（夫妻/兄弟/何知章/奮鬱） | 「身弱喜印」「身旺…」等任/刘注 | **ANNOTATION/B** | 注家系统（任铁樵） | CONDITION_STATE | 禁作 ORIGINAL 证据 |

**特征**：正文几乎不出现「身旺/身弱」（仅从儿 1 条）；大量在注家层——**不得把 DTS 注家身旺弱当正文**。

### 4. 穷通宝鉴（QTBJ）23 条

| 语境组 | 章节 | 代表原文 | layer/grade | 语义域 | 状态枚举草案 | 允许 Rule |
|---|---|---|---|---|---|---|
| QTBJ-身旺弱-调候 | 正月甲木…十二月（日干×月令全表）+ 增補月談賦 | 「身旺任才富翁」「身弱財多富不久」「身旺任殺一品」 | **ORIGINAL/A（全）** | 调候结构（日干×月令×具体干支） | CONDITION_STATE | PENDING（绑定月干） |

**特征**：全部 ORIGINAL；身旺身弱只在具体「日干×月令」调候语境出现——**禁止泛化**。

### 5. 三命通会（SMTH）194 条

| 语境组 | 章节 | 代表原文 | layer/grade | 语义域 | 状态枚举草案 | 允许 Rule |
|---|---|---|---|---|---|---|
| SMTH-身旺弱-日时断语 | 六X日Y時斷（约150条） | 「寅月身旺，財帛破散」「身衰煞旺主凶死」「月通身旺人清貴」 | **ORIGINAL/A（全）** | 具体日干×时支×月令的结构断语 | CONDITION_STATE | PENDING（绑定具体干支） |
| SMTH-身旺弱-女命 | 論女命/招嫁不定/娼/產蕩破/女命 | 「日干不宜太旺」「身旺夫絕」 | ORIGINAL/A | 女命六亲断语 | CONDITION_STATE | PENDING |
| SMTH-身旺弱-通论 | 論壽夭/橫夭/福壽兩備/安靜守分 | 「身旺鬼絕雖破命而長年」「身弱而遇煞重」「身坐旺鄉」 | ORIGINAL/A | 格局通论 | CONDITION_STATE | PENDING |

### 6. 神峰通考（SFTK）218 条

| 语境组 | 章节 | 代表原文 | layer/grade | 语义域 | 状态枚举草案 | 允许 Rule |
|---|---|---|---|---|---|---|
| SFTK-身旺弱-病药 | 病藥說/雕枯旺弱四病 | 「財官太旺日主太弱則身主不能任其財官」 | ORIGINAL/A | 旺弱为病（雕枯旺弱四病） | DISEASE_STATE | PENDING |
| SFTK-身旺弱-格局 | 正官/偏官/正財/印綬/陽刃/雜氣/魁罡/日德等格 | 「喜身旺」「身弱則不能任」「身旺遇之方是福」 | ORIGINAL/A（含楠曰 ANN B/歌 QUOTED） | 格局条件 | CONDITION_STATE | PENDING |
| SFTK-身旺弱-歌诀 | 子平舉要/庚日定格/月建歌 | 「財多身弱食神來生殺必為災」 | ORIGINAL/A | 断语歌诀 | CONDITION_STATE | PENDING |
| SFTK-身旺弱-六親 | 刑妻歌/尅子歌/女命歌 | 「月令又逢身旺地青春年少哭孀娥」 | ORIGINAL/A | 六亲断语 | CONDITION_STATE | PENDING |

---

## 二、关键发现（禁止统一概念的实证）

1. **同一「身旺」六部语义各不相同**：
   - YHZP：十神喜忌条件（七杀喜身旺、财任受、运行身旺发福）
   - PZZQ：用神格局成败/取运依赖项
   - DTS：正文几乎不出现（从儿不论身强弱）——身旺弱主体在注家层
   - QTBJ：调候结构（日干×月令组合）中的旺衰基础
   - SMTH：具体日时干支的结构断语
   - SFTK：病药体系（雕枯旺弱四病之「旺/弱」皆可为病）

2. **同书内不同章节语义也可不同**：
   - YHZP 神趣八法·鬼象「身旺則不吉」vs 其余章节「喜身旺」——**从格语境反例**，同一书内须章节隔离
   - PZZQ「身旺不勞印生」（身强印旺反孤贫）vs「身弱最喜印旺」——身旺弱决定印星喜忌方向

3. **text_layer 差异巨大**（影响证据准入）：
   - QTBJ/SMTH：全 ORIGINAL/A（最干净）
   - DTS：11 条中 10 条在注解层——**不得作 ORIGINAL 证据**
   - YHZP：ORIGINAL 为主，注 B/批 C 混合
   - SFTK：ORIGINAL + 楠曰 ANN/B + 歌诀 QUOTED/D 混合

4. **状态枚举统一建议**（跨书语义各自独立，但字段可同名）：
   - 各书 strength_state 值域沿用附录 L 六级（STRONG/SLIGHTLY_STRONG/NEUTRAL/SLIGHTLY_WEAK/WEAK/UNDETERMINED）
   - 但**判定依据**必须按书×章节绑定 source（如 YHZP-论七杀 vs QTBJ-调候）
   - 「从格不论身强弱」（DTS 顺局）→ PATTERN_STATE，与 strength 判定解耦

---

## 三、与 CLASSICAL_RULE_ADMISSION 的衔接

本次审计产出为「概念语境清单」，**尚未进入规则准入**。后续每条 Rule 开发必须：
- 绑定 Concept ID（CONCEPT-<BOOK>-<语境组>-<概念>，如 CONCEPT-YHZP-QISHA-SHENWANG）
- 绑定 source_ids（已钉死）
- text_layer=ORIGINAL 且 grade=A 才可作 A 级证据（DTS 注家层只能作 B）
- 逐条过 CLASSICAL_RULE_ADMISSION 十一门槛

## 四、待办

- [ ] 本矩阵 Human 审批（语境组划分是否认可）
- [ ] 第一批剩余：旺/强区别（六部「旺」「强」用法辨析）、得令/得地/得势（六部出处）
- [ ] 第二批：财/官杀/印/食伤 概念审计
- [ ] 第三批：清浊/真假/成败/病药
- [ ] concept_registry.json 创建（待批准）

## 五、执行记录（2026-09-16）

1. 六部全量扫描：520 条命中（YHZP 57/PZZQ 17/DTS 11/QTBJ 23/SMTH 194/SFTK 218）✅
2. 按书×章节聚合 + 语境组归类 ✅
3. 全量明细落档 docs/PATCH-003_ConceptAuditMatrix_身旺身弱_2026-09-16.md ✅
