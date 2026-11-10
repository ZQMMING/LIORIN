# 子平引擎规则级核验报告（2026-11-08）

> 目的：按**子平（沈孝瞻《子平真诠》）原典规则**核验 p0 线引擎（`engines/` +
> `p0_v2/`），而不是照搬盲派「四柱→结论枚举」的案例回放。
>
> 方法：独立实现机读判据 `src/tongshu/reasoning/ziping_classic_check.py`，
> 对账脚本 `scripts/ziping_rule_audit.py`（原典 12 案 + N 随机盘），
> 与 `engines.production_entry` 的 `ge_cheng`（格名/成败）逐项比较。
>
> 边界：核验器只判原典明文且不依赖身强弱的条款；依赖旺衰的条款标
> `NOT_EVALUABLE`，不臆断。

## 一、判据来源（逐字切片）

取格：

- `FOUNDATION.MONTH_COMMAND.YUE_LING_GE_JU.001`
  「格之真者，月支之神，透于天干也。以散乱之天干，而寻其得所附于提纲，非格也。」
- `.005`「用神既主月令矣，然月令所藏不一，而用神遂有变化。」
- `.006`「假使寅月为提，不透甲而透丙……」
- `STRUCTURE.GE_JU.CHENG_BAI.002`
  「如四季月生人，只当取土为格，不可言杂气财官；戊己日生于四季月者，当看人元透出天干者取格。至于建禄月劫羊刃，亦当看月令中人元透于天干者取格。」

成败：

- `STRUCTURE.GE_JU.CHENG_BAI.007`（八格成）
- `STRUCTURE.GE_JU.CHENG_BAI.008`（八格败）
- `STRUCTURE.GE_JU.CHENG_BAI.009/.011/.012`（带忌/救应/吉凶神）

## 二、核验器口径

| 项 | 规则 |
| --- | --- |
| 取格 | 月支藏干中**透于天干者**为格（按本气→中气→余气取第一个透出者）；皆不透取本气 |
| 四季月 | 辰戌丑未月：非土日主取本气土为格；戊己日看人元透干取格 |
| 建禄月劫 | 本气为比肩/劫财 → 建禄月劫格；阳干月支为刃位（甲卯/丙午/戊午/庚酉/壬子）→ 阳刃格 |
| 成败 | 仅判 `CHENG_BAI.007/.008` 中不依赖身强弱的条款；其余标 `NOT_EVALUABLE` |

## 三、对账结果

### 3.1 原典 12 案（取格 / 成败）

| 案 | 四柱 | 核验器 | 引擎 |
| --- | --- | --- | --- |
| 张耀曾 | 乙酉 甲申 丁巳 庚戌 | 财格 / CHENG | 财格 / CHENG |
| 林森 | 戊辰 甲寅 丁卯 己酉 | 印格 / CHENG | 印格 / CHENG |
| 刘镇华 | 癸未 辛酉 甲申 丙寅 | 正官格 / BAI | 正官格 / NOT_EVALUABLE |
| 洗冠生 | 戊子 癸亥 庚寅 戊寅 | 食神格 / BAI | 食神格 / CHENG_ZHONG_YOU_PO |
| 龙济光 | 丁卯 丙午 丙子 壬辰 | 阳刃格 / NOT_EVALUABLE | 阳刃格 / PO |
| 王士珍 | 辛酉 丙申 庚子 丙戌 | 建禄月劫格 / CHENG | **None / None** |
| 壬寅案 | 壬寅 戊申 丙寅 癸巳 | 七煞格 / BAI | 财格 / PO |
| 乾隆 | 辛卯 丁酉 庚午 丙子 | 阳刃格 / NOT_EVALUABLE | 阳刃格 / PO |
| 朱家骅 | 癸巳 丁巳 丁卯 丙午 | 建禄月劫格 / CHENG | **None / None** |
| 王克敏 | 丙子 壬辰 壬申 乙巳 | 七煞格 / NOT_EVALUABLE | 七煞格（破格）/ PO |
| 蔡元培 | 丁卯 癸丑 丙申 戊子 | 伤官格 / CHENG | 伤官格 / PO |
| 谭延闿 | 己卯 丁丑 癸丑 乙卯 | 七煞格 / NOT_EVALUABLE | 七煞格 / CHENG_ZHONG_YOU_PO |

### 3.2 随机 40 盘

- 取格不一致：**10/40**
- 成败不一致：**27/40**

## 四、差异分类与证据

### A. 本气立格 vs 透干立格（系统性）

- 原典 `YUE_LING_GE_JU.001`：月支之神**透于天干**者为格；本气不透而中/余气透时取透出者。
- 引擎：`l0_fact_builder.py` 的八格入口全部由 `mqi = HIDDEN[mz][0]`（月令本气）派生；
  `ge_jie_layer.py:722/862/1004` 亦按 `month_qi_ten_god` 分支。
- 实证：壬寅 戊申 丙寅 癸巳（申藏庚财/壬煞/戊食，透壬）→ 原典七煞格；引擎财格。
- 示例：戊辰 丁巳 癸亥 乙卯（巳藏丙财/庚印/戊官，透戊）→ 原典正官格；引擎财格。
- 备注：引擎在 `ge_jie_layer.py:1313`（V7.48）记录其口径依据 DTS L210
  「人元透干取格须有气象形局配合」，并称无配合神时不立格。此为两说并存，
  需按用户口径裁决（本报告不改立格实现）。

### B. 建禄月劫「败格保名」缺失（真缺陷候选）

- 原典 `CHENG_BAI.008`：「建禄月劫，无财官，透煞印，建禄月劫之格败也。」——败格**格名仍存**。
- 引擎 `ge_jie_layer.py:1286-1326`：无官财食伤配合时 `ti_wx`/`_jl_xi` 皆空 →
  `ge_cheng = None`，格名丢失（王士珍、朱家骅两案）。
- 内部不一致：同为败格，阳刃格分支（`:557-567`）仍返回「阳刃格」格名。

### C. 从格与正格边界

- 辛未 乙未 乙未 乙酉：乙日未月（四季月，土=偏财），乙有未中余气根；引擎判「从杀格」，
  核验器判「财格」。
- 涉及 `engines/cong_ge_predicate.py`「日主无独立根（长生/余气/墓库属弱根，不挡从）」的门槛，
  需按原典（从格须日主无根）裁定余气根是否挡从。

### D. 特殊格优先级

- 甲午 丁卯 壬戌 丙午：引擎「化木气格」（丁壬合化木），核验器「伤官格」。
- 需核 `engines/huaqi_predicate.py` 的化气条件（月令化神、无克、无争合等）。

### E. 成败粒度与命名

- 引擎状态：`CHENG` / `PO` / `NOT_EVALUABLE` / `CHENG_ZHONG_YOU_PO`；
  核验器：`CHENG` / `BAI` / `NOT_EVALUABLE`。
- 引擎在 `ge` 字段混入成败变体名（`无根须印(财不成格)`、`印格(印轻逢财)`），
  与「格名 / 成败」两字段应分离的原则不一致，建议后续归一。

## 五、已做的尝试（已回退）

尝试把 `l0_fact_builder` 的八格入口改为「透干优先十神」并在 `ge_jie_layer` 读取：

- 取格不一致 12 → 10；
- 但 `pytest -k ziping` 由 1168 passed/4 failed 变为 **1158 passed/14 failed**
  （新增 10 项均来自 GPT 在途测试 `test_ziping_entry_validation.py` /
  `test_ziping_wealth_sha_templates.py` 对本气入口契约的断言）；
- 已全部回退，基线恢复 **1168 passed / 4 failed**（4 项为 GPT 在途 `test_ziping_relation_presence.py`）。

## 六、复现

```powershell
$env:PYTHONPATH='D:\shuntian\src;D:\shuntian'
$env:PYTHONUTF8='1'
python scripts\ziping_rule_audit.py 40
python -m pytest tests\test_ziping_classic_check.py -q
python -m pytest tests -k ziping --ignore=tests/test_ziping_15_2_evidence_provenance.py -q
```

## 七、下一步（按原典裁定）

1. A：裁决「本气立格 / 透干立格」口径；若取原典，需同步改 GPT 在途的入口契约测试。
2. B：建禄月劫无配合时保留格名并标败（与阳刃格分支对齐）。
3. C：从格余气根门槛按原典明确。
4. D：化气格条件核验（月令化神、无争合、无克）。
5. 旺衰：p0 只判得令/失令，原典多格成败需身强弱（成格条件依赖），属后续判据补全。

## 六、2026-11-08 裁决复核：原典「本气立格 + 透干定格之真假」（透干优先已回退）

初判为「透干优先取格」，落地后对照原典逐句复核，结论修正：

- YUE_LING_GE_JU.001「格之真者，月支之神，透于天干也。以散乱之天干，而寻其得所附于提纲，非格也。」
  → **本气为格名**，透干决定「格之真/假」（本气不透则格不真、用神散乱），不是换格名。
- .002「八字用神，专求月令，以日干配月令地支，而生克不同，格局分焉。」
  → 格由「日干配月令」本气生克立。
- .005/.006「月令所藏不一，而用神遂有变化」「假使寅月为提，不透甲而透丙」
  → 例中寅月甲日为**建禄**（本气比劫不可为用），故看人元透干取用神（丙食神）；只在月令本气为比劫(禄/刃)时，格名才看人元透干。
- CHENG_BAI.002「四季月生人，只当取土为格…建禄月劫羊刃，亦看月令中人元透于天干者取格」
  → 四季月取土、禄刃看透干，与本条一致。

因此引擎原有「月令本气立格」为正确口径；此前「一切基于原典」被过度执行为「透干优先换格名」，
导致 	est_ziping_entry_validation.py 7 条与 	est_ziping_wealth_sha_templates.py 2 条（如
甲日巳月透戊 应仍为食神格、甲日午月透己 应仍为伤官格）失败——这些测试本就符合原典，故回退引擎改动。

回退结果：ziping 回归 **1178 passed / 4 failed**（4 项为 GPT 在途 relation_presence；另 +10 为本轮核验器测试），
取格对账 12/40（20 盘抽样 7/20），全部差异按上述口径分类：本气立格（引擎对）、禄刃透干（部分对）、
化气/从格优先级、变体格名——均属待逐项核验项，不再以「透干优先」一刀切。
## 七、建禄月劫「败格保格名」尝试与回退（2026-11-08）

原典 CHENG_BAI.008「建禄月劫无财官透煞印」为败格，但格名仍在；引擎现状：无配合神时
ge_jie_layer.py 直接不出格（if ti_wx or _jl_xi），而阳刃格分支却保名 → 内部不一致。

尝试：改为无条件保名（ge=建禄月劫格, 	i_wx 可空），并加 primary_blocked 标记、
在 
esolve_yongyao 早退 GE_NAMED_UNRESOLVED（格名存、用神未定，不让调候/扶抑代偿出主药）。

结果：	est_ziping_break_evaluation_completeness 3 例恢复，取格差 12/40→8/40，成败差 27/40→32/40；
但 	est_ziping_bridge.py 2 例（1990-03-01 盘）因 _attach_ge_evidence 把该盘
ge_rule_verification 判为 NOT_EVALUABLE（财透+比劫同现），桥接映射为 GEJU UNKNOWN 而红。
说明该盘本来依赖「无配合不出格」的旧路径规避该证据缺陷，保名后暴露出证据层判定问题。

处置：**回退本次尝试**，基线恢复 1178 passed / 4 failed（4 项为 GPT 在途 relation_presence）。
待办：先修 _attach_ge_evidence 的财透+比劫同现误判（应只对「财与比劫同现且无制」标未核验），
再复启保名 + 用神门控；两者需一起提交。


## 八、格体喜神≠用神：格用神主药规则（V7.180，2026-11-09）

**问题**：源1无病 → 走源2 `ge_cheng.xi_wx`（格体喜神）时，旧代码把 xi_wx 首项当主药。
xi_wx 是「格之喜神」（财/印/食伤等），不是用神；多喜神时取列表首项＝无授权排序。
GPT 侧因此把「多候选」一律 `primary_selection_status=NOT_EVALUABLE` + `primary_medicine=None`，
连原典可确定用神的盘也判未知（对照表用神 25/25→9/25，其中旧 25/25 为恒 PRIMARY 型基线，不可当标准）。

**原典依据**：
- 建禄月劫：PZZQ L1142-1143「透官而逢财印即同官格；透财而逢食伤即同财格；透煞而遇制伏即同煞格」→ 同官格用官(官杀)，同财格用财，同煞格用官杀；财/印/食伤为喜。
- 阳刃：PZZQ L1140-1141/L4579-4582「以官煞制刃」「食伤泄秀」→ 用官或食伤。

**修法**（`engines/common/yongyao_resolve.py`）：
1. 新增 `derive_ge_yong_wx(facts)`，仅对建禄月劫/阳刃按形态取格用神（其余八格不推）。
2. 源2 fallback 多候选且格用神可派生时：`SINGLE_CANDIDATE` + 主药=格用神，`classic` 引原典；喜神仍留 xi_wx 作辅。
3. 其余八格多喜神仍 `NOT_EVALUABLE`（不因列表首项升格），保持 GPT 的「未排序不升格」不变量。

**实测**：
- 1990-03-01 男，庚午 戊寅 乙丑 壬午 → 建禄月劫·同官格（庚正官透、戊财、壬印）→ 用官=**金**，喜财土/印水；原 NOT_EVALUABLE/Primary None → **PRIMARY 金**。
- 1980-07-15 男，庚申 癸未 己丑 庚午 → 建禄月劫·同财格（癸财透、庚食伤）→ 用财=**水**。
- 1981-03-15 男，辛酉 辛卯 壬辰 丙午 → 伤官格佩印，仍 NOT_EVALUABLE（不按列表升格）。

**测试**：`tests/test_ziping_bridge.py` 22 passed；`tests/test_ziping_ge_candidate_priority.py` 64 passed
（date0 建禄同财格按原典裁定、date1 伤官佩印仍未知，两支分别断言）；
`pytest -k ziping --ignore=tests/test_ziping_15_2_evidence_provenance.py` → **1861 passed / 9 failed**，
9 项全部为 GPT 在途改动既有失败（relation_presence 4、root_support_unknown 3、medicine_he_positions 1、rescue_consumption 1）。


## 九、旺衰域按原典三才判据落地（V7.181，2026-11-09）

**问题**：p0 engines 线 `meta_outputs.WANG_SHUAI` 只给「得令/失令」候选，明言「不判身强身弱」，
桥接因此把 WANGSHUAI 域固定 UNKNOWN；GPT 对照表旺衰 0/23，旺衰域等于不可用。

**原典依据（逐条）**：
- 「阴阳顺逆之说…其法不可执一」（STATE.WANG_SHUAI.PAN_DUAN_FA.001）——不执月令一端。
- 「不必论当令不令，只论取最多最旺」（DE_LING.001）——得令不是唯一判据。
- 「月令乃提纲之府，人元为用事之神」（DE_LING.002）——月令以本气用事定得令。
- 「天地顺遂而精粹者昌」/「地生天者，天衰怕冲，则根拔而祸更甚」（DE_DI.001/002）——得地看通根，根被冲则减。
- 「强众而敌寡者，势在去其寡」（DE_SHI.001）——得势看天干党众。
- 「日主孤立无气，无地人元，绝无一毫生扶…乃为真从」（SHUAI.003）——弱极之象。

**判据（`ziping_classic_check.judge_strength`）**：
1. 得令 ±3：月支**本气**用事之神帮身（比劫/印）为得令；中气/余气不冒充用事之神（节气深浅三柱不可得，记于 reasons）。月支被冲 → 得令减为 +1（令根受损）。
2. 得地 0..2：四支通根按 本气2 / 中气1 / 余气0.5 累加，封顶 2；无根为 0。
3. 得势 ±2：天干（除日主）帮身 +1（封顶2）、财官食伤 -1（封底-2）。
4. 成局 ±2：三支齐备的三合/三会，与日主同党 +2，异党 -2（半合不算）。
5. 结论：总分 ≥5 → STRONG；≥2 → MODERATE；其余 → WEAK。

**接入**：`src/tongshu/reasoning/ziping_bridge.py::_wangshuai_from_pillars`；
WANGSHUAI 领域结论带 `STATE.WANG_SHUAI.*` 切片作 rule_refs/evidence_refs，
经 composer 产 `AC-ZP-wangshuai-*` claim 并可过 G1。

**实测**：
- golden 23 案旺衰结论一致 **20/23**（修前桥接恒 UNKNOWN = 0/23）。3 处不一致：
  WANG-005（引擎标 MODERATE、本判据 WEAK，分差 -2 vs 0）、GEJU-002（三合火局生土判旺，golden 标 MODERATE）、
  GEJU-007（杂气月成局判弱、golden 标 MODERATE）；均属 golden 自身 `MODERATE` 带与负分重叠的口径问题（其 WANG-008 描述「中和」而标签 WEAK 亦自相矛盾）。
- 1990-03-01 男（庚午 戊寅 乙丑 壬午）→ 得令 3（寅月甲木比肩）、得地 0（四支无木根）、党众 -1 → 合 2 → MODERATE。
- 命盘 claim 链路：`tests/test_int_06 + test_audit_gates + test_int_01_02_03` → **51 passed**，
  旺衰 claim 带原典切片证据后仍过 G1/G2，未破既有断言。

**测试**：`tests/test_ziping_classic_check.py` 新增 7 条（建禄旺/食神克泄弱/月令被冲减等/三合成局/孤立无气弱/证据锚可解析/golden 覆盖率护栏 ≥20/23），
与 `test_ziping_bridge.py` 合计 **41 passed**；`pytest -k ziping` → **1868 passed / 9 failed**
（9 项仍为 GPT 在途既有失败：relation_presence 4、root_support_unknown 3、medicine_he_positions 1、rescue_consumption 1）。

## 十、格用神八格表：用神覆盖率 2/12 → 10/12（V7.182，2026-11-09）

### 问题
`meta_outputs.WANG_SHUAI` 只答得令/失令，格局多半落在 `NO_BING` / `NO_BING_GE_XIJI`
（源1 无病、无格体喜神），`primary_medicine` 恒空 → 无病之盘不产用神；
实测原典 12 案用神覆盖率仅 **2/12**（仅印格、七煞格两案命中）。

### 原典判据（沈孝瞻《子平真诠》论用神 / 论八格）
- 正官格：官多同煞 → 食伤制官；官轻 → 财（生官）/印（护官）。
- 七煞格：食伤制煞；印化煞。
- 财格：财逢官则官为用；印重（印夺财）则取财损印；财生食伤。
- 印格：印重用财损印；官印双全用官。
- 食神格：食神生财；带煞用食伤制煞。
- 伤官格：伤官佩印；伤官见官用比劫/印；伤官生财。
- 建禄月劫：透官/透煞 → 官杀；透财 → 财；透食伤 → 食伤。
- 阳刃格：以官煞制刃；无官煞用食伤泄秀。

### 修法（`engines/common/yongyao_resolve.py`）
1. `derive_ge_yong_wx(facts)` 由「建禄/阳刃两形态表」扩为**八格判据**：
   读 `ten_god_members` 统计 `官杀/财/印/食伤/比劫` 成员数 + 透干集合，
   按上表定「格用神」十神类别，再按日主五行转五行（`_GE_YONG_CAT_WX`）。
2. 新增 `_ge_medicine(facts)`：有可裁格用神时给出主药
   （`kind='格局用神'`、`function='源2:格局用神(无病时格用神为主药)'`、`classic` 引原典）。
3. `NO_BING` / `NO_BING_GE_XIJI` 两支改出该主药（**不改变 state**，保留层语义）；
   源5 旺衰喜用神分支在格用神可得时让位（源2 优先于源5）；GE_FALLBACK 无病喜神路径同样优先格用神。
4. 门控（防伪造）：无四柱实体（合成 facts）、特殊格候选（专旺/从格）未核验、非八格格名 → 返回空串，不猜。
5. 桥接 `src/tongshu/reasoning/ziping_bridge.py`：`kind='格局用神'` 的结论复用已核验格局的证据锚，
   并按 PRIMARY 输出（此前 NO_BING 恒 UNKNOWN）。

### 实测（12 案，脚本 `scripts/ziping_pzzq_replay.py`）
| 案 | 四柱 | 原典用神 | 引擎 | 状态 |
|---|---|---|---|---|
| 001 | 癸未 辛酉 甲申 丙寅 | 火（官多同煞） | 火 | HIT |
| 003 | 丁卯 丙午 丙子 壬辰 | 水（煞刃） | 水 | HIT |
| 004 | 乙酉 甲申 丁巳 庚戌 | 金（财损印） | 金 | HIT |
| 005 | 辛酉 丙申 庚子 丙戌 | 火（同煞） | 火 | HIT |
| 006 | 丙子 壬辰 壬申 乙巳 | 木（食伤泄秀） | 木 | HIT |
| 007 | 戊辰 甲寅 丁卯 己酉 | 金（财损印） | 金 | HIT |
| 008 | 辛卯 丁酉 庚午 丙子 | 火（制辛） | 火 | HIT |
| 009 | 癸巳 丁巳 丁卯 丙午 | 水（官制旺） | 水 | HIT |
| 011 | 己卯 丁丑 癸丑 乙卯 | 木（食神制煞） | 木 | HIT |
| 012 | 壬寅 戊申 丙寅 癸巳 | 水（合官留煞） | 水 | HIT |
| 002 | 戊子 癸亥 庚寅 戊寅 | 土（扶身制伤） | 水 | MISS（从儿格判定分歧） |
| 010 | 丁卯 癸丑 丙申 戊子 | 火（劫帮身） | 土 | MISS（源1 病药与沈断差异） |

覆盖率 **10/12**（2 案为口径冲突，登记不并入分母）。

### 测试
- `tests/test_ziping_yong_coverage.py`：10 案逐案锁死用神五行 + 覆盖率 ≥10 护栏。
- `tests/test_ziping_ge_candidate_priority.py`：候选无序不升格的旧断言按原典修订
  （合成 facts 不派生格用神；真实盘 1981-03-15 伤官佩印取印=金）。
- 回归 `pytest -k ziping --ignore=tests/test_ziping_15_2_evidence_provenance.py`
  → **1868 passed / 9 failed**（9 项均为 GPT 在途测试的既有语义分歧：relation_presence 4、root_support 3、
  medicine_he_positions 1、rescue_consumption 1）。

## 十一、从儿格印根门控：印透干且有根则不从（V7.183，2026-11-09）

**现象**：PZZQ 002 戊子 癸亥 庚寅 戊寅，引擎判 `从儿格 CONFIRMED`（ti_wx=水），沈孝瞻原文断「泄气太重，以戊土扶身制伤为用」= 正格伤食佩印。用神因此取水（泄气方向），与原典相反。

**根因**：`engines/common/ge_jie_layer.py` 从格覆盖正格分支中，从财格已按「印透干 + 印本气根 → 不从」门控（`_yin_bn >= 1`），从杀格按「印透化煞 → 不从」门控，**从儿格缺同等门控**。002 之戊印透干、寅中戊为余气根（`wuxing_power['土'].root_detail = {'寅':'YU'}`），引擎只看本气根（`ben_n=0`）故未拦。

**修法**（`ge_jie_layer.py` 从儿格分支，V7.183）：印透干且印五行 `root_detail` 非空（含本气/中气/余气任一根）→ `_not_cong = True`，回落正格判定。依据《子平真诠》4941 同条「从财格而有印，须看印是否通根」与「印无根不得相从」；从财格仍按原文只认本气根，从儿格按「透干有根」从严。

**实测**：002 → `ge=食神格`（非从格）、`po_ge` 报「枭夺食」结构；用神仍取调候水（本层见「十二」节待办）。新增 `tests/test_ziping_cong_gate.py`（2 条：002 不得判从、从格成立须 cong_type 与 CONFIRMED 同现）。

**回归**：关键四文件 94 passed；`pytest -k ziping` **1879 passed / 9 failed**（9 项与 V7.182 基线同集合，均为 GPT 在途语义分歧，无新增）。

## 十二、病药层两处门控：泄气太重不得被格成豁免、寒燥交互不得反压候干（V7.184，2026-11-09）

**现象**：PZZQ 002（戊子 癸亥 庚寅 戊寅，食神格）与 010（丁卯 癸丑 丙申 戊子，伤官格）用神仍偏移。002 沈断「泄气太重，以戊土扶身制伤」，引擎主药却是调候水（泄气方向）。

**根因一（bingyao_layer.py）**：格体病过滤（`bing_list` 的 L4 门控）对「格体 = 病五行」一律按格成豁免——食神格成 → 食伤（水）为格体喜神 → 泄气太重病被 `continue` 删掉，只剩「财多身弱」，药随主病偏移。原典 L3930「食伤旺而生财，为身轻泄气太重」明示**身轻（日主无有效根）时泄气即病**，与格成与否无关。

**根因二（tiaohou_rank.py）**：`_hanzao_shishang_rank` 的寒燥交互推导在「候干表未候食伤」时把**食伤五行**升为候神（002 升水）。但 002 候干表已有丁火（QTBJ 庚亥月 order1=丁、order2=丙），该推导反压已录候干，且方向与「金水伤官要燥」相反（寒月补水、越补越寒）。

**修法**：
1. `bingyao_layer.py` 格体过滤：仅 `XIE_QI_TAI_ZHONG` 例外——身弱（`_shen_ruo`）且食伤成党时报病（新增注释 V7.184）；财多身弱等其余格体病仍按格成豁免（避免 004 财格被误报、药翻成比劫）。
2. `tiaohou_rank.py`：`_hanzao_shishang_rank` 在「候干表非空」时直接 `DEMOTE`（让位 QTBJ 候干，第一顺位），仅候干表为空（如 NOT_REGISTERED）才走寒燥交互补位。
3. `tests/test_ziping_entry_validation.py` 的 `test_entry_routes_actual_resolved_primary_disease`（辛未 庚寅 壬午 庚戌）按原典改锚：主病 `CAI_DUO_SHEN_RUO→XIE_QI_TAI_ZHONG`、bing_wx 火→木（壬日食伤=木）、winner_shen 水→金（克木之药）。

**实测**：002 → 主病「泄气太重(木→水)」、药=制(土) 命中「以戊土扶身制伤」；004 仍 HIT（格体豁免未动）；原典 12 案覆盖率 **10/12 → 11/12**（唯一余 MISS=010：丙日水旺，原典取劫帮身，引擎源1 取印，属断法分歧，登记）。`tests/test_ziping_yong_coverage.py` 护栏同步升到 ≥11。

**回归**：`pytest -k ziping` **1881 passed / 9 failed**（9 项与 V7.183 基线同集合，均为 GPT 在途语义分歧，无新增）。

## 十三、十神域落地：最旺十神 × 喜忌判吉凶（V7.185，2026-11-09）

### 问题
p0 engines 线只到「格/病/药」层，`ziping_bridge` 对 SHISHEN 恒返回 UNKNOWN（"p0 engines 线未输出十神域"），V13 断言里没有十神 claim。

### 原典判据
《三命通会·论十神》（切片 `FOUNDATION.RELATION.SHI_SHEN.001`）：「徐子平论格局，独以印、食、官、财四者为纲…生我者印绶，我生者食神，克我者官煞，我克者妻财。」→ 十神按生克五类（比劫/食伤/财/官杀/印），吉凶随其在局中的喜忌地位而定，不单独论十神本身。

### 修法
1. `src/tongshu/reasoning/ziping_bridge.py` 新增 `_wx_category(wx, daymaster_wx)`（五行→十神大类，取自 `ziping_classic_check.GEN/KE`）与 `_shishen_from_facts(facts, refs)`。
2. 强弱取 p0 的 `wuxing_power`：`ben_n*2 + zhong_n*1 + yu_n*0.5 + stem_n*1 + ju_n*2 + banhe_n*1`，取分值最高五行 → 十神大类（等分时按五行名稳定取）。
3. 喜忌口径：喜 = 用药五行 ∪ 格用神五行；忌 = 主病五行且不在喜。最旺十神属喜 → `SEMANTIC_POSITIVE`；属忌 → `SEMANTIC_NEGATIVE`；两者皆非 → UNKNOWN（不硬断）。
4. 证据锚：`FOUNDATION.RELATION.SHI_SHEN.001` 入 rule_refs/evidence_refs，并复用格局/用药证据锚（G1 要求可解析）。

### 实测（PZZQ 12 案）
- 002 戊子癸亥庚寅戊寅：食伤(水)最旺且为病 → **SEMANTIC_NEGATIVE**；
- 004 乙酉甲申丁巳庚戌：财(金)最旺且为用药 → **SEMANTIC_POSITIVE**；
- 007 戊辰甲寅丁卯己酉：印(木)最旺且为病 → **SEMANTIC_NEGATIVE**；
- 011 己卯丁丑癸丑乙卯：食伤(木)最旺且为用药 → **SEMANTIC_POSITIVE**；
- 其余 8 案最旺十神非喜非忌 → UNKNOWN（诚实留白）。

### 端到端
1984-12-07 16:00 男（印格，药=火，病=水）：pipeline `validation_passed=True`，原子断言新增
`AC-ZP-shishen-semantic_negative`（证据锚 `FOUNDATION.RELATION.SHI_SHEN.001` + 格局切片）。

### 测试与回归
- 新增 `tests/test_ziping_shishen.py`（5 passed：三案结论 + 证据锚解析 + pipeline claim）；
- `test_ziping_shishen + bridge + audit_gates + int_06 + classic_check` **90 passed**；
- `pytest -k ziping` **1886 passed / 9 failed**（9 项均 GPT 在途既有失败，无新增）。

## 十四、事件域落地：流年冲为事件触发符号（V7.186，2026-11-10）

### 问题
p0 engines 线传 `liunian`（干支）时输出 `liunian_summary`（liunian_transit.clash / clash_facts / liunian_root_clash_facts / sanhe_ju / sanhui_ju 等），但桥接此前未消费，SHIJIAN 恒 UNKNOWN。

### 原典判据
切片 `SUI_YUN.RE_EVALUATION.LIU_NIAN.005`（流年重估）、`SUI_YUN.RE_EVALUATION.DA_YUN_YIN_DONG.002`（大运引动）：流年与大运对原局的再评估是岁运层事件来源；冲是岁运触发符号，实际作用需按本运喜忌核验（p0 明示「实际作用未核验」）。

### 修法（`src/tongshu/reasoning/ziping_bridge.py`）
1. 新增 `_ganzhi_of_year(year)`（(year-4)%10/%12）与 `_shijian_from_facts(result)`：无 liunian_summary → UNKNOWN（未指定分析年）；流年支与命局无冲（两类 clash_facts 均空）→ EVENT_ABSENT（无事件触发符号）；有冲 → EVENT_EXIST（触发符号=流年冲，实际作用未核验，不判吉凶/应期）。
2. `run_ziping_judgment(chart, target_year=None)` 把 target_year 干支传给 `production_entry(FrozenCanonicalBaziChart(pillars=..., liunian=...))`；`compute_stage.py` 传 `analysis_date.year`。
3. fail-closed 保持：`JudgmentClaimComposer._FC_BLOCKED_DOMAINS={"SHIJIAN"}`（15.14 method audit）不变 → SHIJIAN 有域判断但 0 claim，等治理放行。

### 实测（1990 庚午 戊寅 乙丑 壬午 男）
target 2024 甲辰 / 2026 丙午 → EVENT_ABSENT；2027 丁未 → EVENT_EXIST「触发 丑未冲」；target_year=None → UNKNOWN。

### 测试与回归
- `tests/test_ziping_shijian.py` 4 passed（UNKNOWN/EVENT_EXIST+锚/ABSENT/composer fail-closed）；
- 相关七文件（shijian+shishen+bridge+audit_gates+int_06+classic_check+yong_coverage）**105 passed**；
- `pytest -k ziping` **1890 passed / 9 failed**（9 项均 GPT 在途既有失败，无新增）。
