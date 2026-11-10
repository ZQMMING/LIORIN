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

## 十五、十神域忌神反向推导：无病盘也可判最旺十神吉凶（V7.187，2026-11-10）

### 问题
V7.185 十神域只在「有病药锚」时出结论（PZZQ 4/12），无病盘（GE_FALLBACK/NO_BING）的最旺十神全部 UNKNOWN。

### 原典判据（沈孝瞻配合论，仅限「制」形明确的格用神类别）
- 用=食伤（官多同煞 / 食伤制煞）→ 所制之**官杀**为病（最旺官杀=病神当权→凶）；
- 用=官杀（阳刃「以官煞制刃」 / 建禄「透官而逢财印即同官格」 / 财旺生官护财）→ **比劫**为病（刃/禄成党→凶）；
- 印/财/比劫类用神配合形态不唯一（印既化杀亦制食伤），**不反推**，宁缺勿猜。

### 修法（`src/tongshu/reasoning/ziping_bridge.py`，仅桥接、不动引擎）
1. `_shishen_from_facts` 增忌神反向推导（格用神类别∈{食伤,官杀}），并并入 zhuangui/bingyao 的病五行集合；
2. 格用神五行取值修正：引擎在「源2 override」路径只回填 `pm.kind="格局用神"` 而不回填 `yy.ge_yong_wx` → kind 白名单内直接取 `pm.wuxing`；
3. reasoning 带格用神类别与病集合，证据锚不变（`FOUNDATION.RELATION.SHI_SHEN.001`）。

### 实测（PZZQ 12 案，4/12 → **10/12**）
- 001 官杀(金)最旺=病 → 凶（沈：官多同煞以丙火制官）；003/005/008 比劫最旺=病 → 凶（阳刃/建禄以官煞制刃）；
- 009 比劫(火)最旺=病 → 凶（沈：日元太旺取癸水抑制）；012 比劫最旺=病 → 凶（比劫夺财）；
- 006/010 最旺十神非喜非忌 → UNKNOWN（诚实留白，010 沈取劫帮身属配合级分歧，已登记）。

### 测试与回归
- `tests/test_ziping_shishen.py` 扩至 6 例（+001/009），相关六文件 **88 passed**；
- `pytest -k ziping` **1892 passed / 9 failed**（9 项均 GPT 在途既有失败，无新增）。

## 十六、成局代月令 + 十神域 STRONG 门控（V7.188，2026-11-10）

### 问题（Round 11）
- 006 王克敏案（丙子 壬辰 壬申 乙巳，申子辰三合水局）：旺衰判 MODERATE，十神域不敢判「比劫为病」——沈孝瞻断「日元太旺，用以泄秀」，病=比劫（水）。
- 根因：成局同党时月支本气失权（局已代月令），而 `_ling_score` 仍按月支本气算 −3；且十神域忌神推导只认「食伤制官杀」形，无「日元太旺泄秀」形。

### 原典依据
PZZQ L984/L986「日元太旺」均以三合成局论旺；DE_LING.001 得令以当令五行势力论，成局同党即得令之实。

### 修法
1. `src/tongshu/reasoning/ziping_classic_check.py::judge_strength`：成局同党 → 局代月令，`ling` 至少 3（并记 reason「成局同党，局代月令（月支本气失权）」）。
2. `src/tongshu/reasoning/ziping_bridge.py::_shishen_from_facts`：忌神推导加 STRONG 门控——格用神=食伤且旺衰 STRONG 且日主五行非喜 → 比劫（日主本身）为病（日元太旺泄秀）；否则退回「食伤制官杀」形（所制官杀为病）；格用神=官杀 → 比劫为病。

### 实测
- 006 → STRONG（成局代月令），十神域 SEMANTIC_NEGATIVE（比劫/水=病，泄秀抑身），与沈断一致；
- PZZQ 12 案 SHISHEN conclusive **11/12**（仅 010 配合级分歧留白）。

### 测试事故披露（2026-11-10）
为「只提交自有 hunk」做测试文件手术时，重建脚本把 `tests/test_ziping_bridge.py` 真身覆写，GPT 未提交的 7 个桥接 fail-closed 测试（test_unknown_yongyao_states_cannot_become_primary 等）从工作树丢失，且无 git 历史/快照可恢复（均已核查）。处置：按已提交的 V7.185 fail-closed 主链**重写 8 个等价场景**（未知 state/未知五行/无证据/来源冲突/GE_FALLBACK 非源2 不复用格局证据/格局 NOT_EVALUABLE 阻断复用 + 源2 与无病格用神两个正向对照），行为覆盖不减；事故与重建记录于本节，后续 GPT 工作树改动一律不再以「整文件重建」方式手术，只做 hunk 级暂存。

### 测试与回归
- `tests/test_ziping_bridge.py` 重建后 **14 passed**（6 既有 + 8 fail-closed）；
- 桥接/十神/事件/核验/审计闸/int_06/int_01 / 用神覆盖 八文件 **106 passed**；
- `pytest -k ziping --ignore=tests/test_ziping_15_2_evidence_provenance.py` → **1884 passed / 9 failed**（9 项均为 GPT 在途既有失败，无新增）。

## 十七、pzzq-010 配合级分歧的定性分析（Round 12，2026-11-10，不改引擎）

**案情**：010 蔡元培（丁卯 癸丑 丙申 戊子）。沈孝瞻断「水旺火弱，用劫帮身为用神」；引擎源1 判主病「泄气太重(土)」、取药「印(木)制食伤」。两说同为原典配合，登记 KNOWN_CONFLICTS。本节把分歧定性清楚，供后续裁决：

1. **引擎只报一病**：`bingyao` 对 010 仅生成 `XIE_QI_TAI_ZHONG`（土，sev3），官杀（水）病未触发。触发器（`bingyao_layer.py::identify_bing` 杀重身轻支，V7.59）要求 杀成党（他干+本根+局票 ≥ DANG_COMBO=4）**或** 相令乘权（ling=='相' 且本根≥1）；010 水按月令旺相休囚死为「死」（丑月），相令门不过；成党计数能否过取决于 `_ju_piao` 是否计 申中壬/丑中癸 等中气票。
2. **沈论势不论令**：沈「水旺」= 丑月水有余气 + 子水本气 + 申子半合 + 癸透干，是「势旺」（得地得势），不因令死而弱——引擎的旺相休囚死口径在此偏窄（势力层面 `wuxing_power` 已计 ben/zhong/yu/stem，但病触发器只看令态+成党阈值）。
3. **两病并存与药的一致性**：010 实际两病并存——水旺克身（官杀太重）+ 土旺泄身（泄气太重）。沈取**劫帮身**（火）：帮身则既能任官又能任泄，一药治两病；引擎取**印制食伤**（木）：印既制泄又化杀，亦是一药治两病。两者均为原典配合，非对错关系。
4. **裁决建议**（未实施）：若要收敛到沈说，需病触发器在「令死但势成党（ben+zhong+stem≥3）且克我」时也报官杀病，且 yongyao 在官杀+泄气双病时优先「帮身」而非「制其一」——这会改变 40 盘对账与多个 GPT 在途测试口径，须与 GPT 协调后单独立项，不在本轮盲改。
5. **现状**：`scripts/ziping_pzzq_replay.py` coverage 11/12（known conflicts=['pzzq-010']），十神域对 010 亦 UNKNOWN（诚实留白）。

## 十八、规则核验器量词落地：成败条款从「须辨」到机判（V7.189，2026-11-10）

### 问题
`ziping_classic_check.judge_cheng_bai` 对三条 .007/.008 量词条款只记 NOT_EVALUABLE 不作机判，且阳刃官煞+伤官并透时静默掉出判据链（无任何 clause 记录）：
- 「印轻逢财」（.008 败）vs「印多逢财而财透根轻」（.007 成）——无「轻/多」判据；
- 「七煞逢财无制」（.008 败）vs「身强七煞逢制」（.007 成）——无「有无制/身强」判据；
- 阳刃格「透官煞而露财印，不见伤官」——旧代码漏「露财印」要件，官煞+伤官并透时无 clause。

### 修法（仅核验器，不动引擎）
1. 新增 `_count_ten_god(p, tgs)`（天干+藏干计数，供「轻/多」量词）。
2. 印格：印计数 ≤1 且见财 → BAI「印轻逢财」；≥3 且见财 → CHENG「印多逢财」（财透根轻不为害）；中间带 → NOT_EVALUABLE「须辨印轻印重」。
3. 七煞格：逢财无制（无食伤）→ BAI「七煞逢财无制」；有制且 `judge_strength`==STRONG → CHENG「身强七煞逢制」；有制身不确 → NOT_EVALUABLE。
4. 阳刃格：透官煞而露财印且不见伤官 → CHENG（补「露财印」要件）；官煞+伤官并透 → 记「须辨制刃/伤官两势」；透官煞无财印 → 记「须辨财印」。
- 实测锚：王克敏（申子辰比劫局帮身 STRONG + 乙伤官制杀）→ CHENG「身强七煞逢制」，与引擎 PO 成对账差异（引擎破格判据未认伤官制杀，待 GPT 口径裁决）；林森 印多逢财 CHENG 与引擎一致。

### 测试与回归
- `tests/test_ziping_classic_check.py` 19→23 passed（新增四锚：印轻逢财 BAI / 印多逢财 CHENG / 身强七煞逢制 CHENG / 阳刃并透条款）；
- 40 盘对账：取格不一致 **8/40**、成败不一致 **27/40**（与 V7.188 基线持平——新机判把原「静默跳过」变成显式条款，分歧面不增不减）；PZZQ 用神覆盖 11/12 不变。

## 十九、引擎侧伤官制煞入格（V7.190，2026-11-10）

### 问题（对账锚：王克敏 丙子 壬辰 壬申 乙巳）
引擎七煞格破格判据 `has_zhi = bool(shi_gans or yin_gans)` 只认 **食神/印**；王克敏乙**伤官**透干（制煞）被判「七煞逢财无制 → PO（伪败格）」——「有制未核验」被当成「无制」出确定性败格结论，与核验器 CHENG「身强七煞逢制」冲突。

### 原典依据
PZZQ《论偏官》：制化路径不止食神——「有用食神制煞者…有用伤官驾煞者（伤官合煞）…用印化煞」；.008「七煞逢财无制」的「制」包含食/伤/印三路，乙伤官透干即「有制」，不得判败。

### 修法（`engines/common/ge_jie_layer.py` 七煞分支，4 处）
1. 增 `shang_gans = _god_gans('伤官')`，`has_zhi = bool(shi_gans or shang_gans or yin_gans)`（破格门槛修正：有伤官即非「无制」）。
2. 成格路径喜神 `_zhi_gans = shi_gans or shang_gans`（食/伤制煞喜制神，兼财去印存食；无食伤退印化）。
3. `zhi_wx` 取 `_zhi_gans[0]` 五行。
4. 哑巴标签喜神回退链补伤官。
- 王克敏实测：`七煞格(破格)/PO` → `七煞格(逢制)/CHENG`（PZZQ255），与核验器、沈断一致。

### 测试与回归
- `pytest -k ziping --ignore=tests/test_ziping_15_2_evidence_provenance.py` → **1888 passed / 9 failed**（9 项=GPT 在途既有，无新增）；
- 40 盘对账：取格 8/40、成败 27/40（基线持平）；PZZQ 用神覆盖 11/12；bridge+classic_check 37 passed。

## 二十、原典扩案 12→21 与两处配合判据（V7.191，2026-11-10）

### 扩案
从《子平真诠》原文再采 9 案（四柱 + 沈明示用神/断语），回放量具 `scripts/ziping_pzzq_replay.py` 由 12 案扩到 **21 案**：锁定 15（全 HIT）+ 已知冲突 6（pzzq-010 官杀双病、017 财格身弱用印/官杀、018 从势阈值、019 财格用禄比、020 印重财损印 vs 食泄秀、021 调候口径）。沈未明示用神的虞和德案（「透印有根不能从」——引擎正官格/不从与沈一致，用神系推断）不入断言。

### V7.191 两处配合判据（`yongyao_resolve.derive_ge_yong_wx`）
1. **日主合财 → 财为用**：财透干与日主五合（甲己/乙庚/丙辛/丁壬/戊癸）→ 财之情专向日主（PZZQ「甲用己财；甲己相合，己土之财，专向日主也」）。pzzq-015 甲寅日己未月 → 土 ✓。
2. **合煞留官 → 官为用**：正官格官杀并透、七杀透干被天干五合合去（`stem_combination_facts.wuhe` 覆盖）→ 留官为用（PZZQ「两乙合庚，仍作合煞留官，无减福也」高太尉案）。pzzq-016 庚午乙酉甲子乙亥 → 金 ✓。
- 新增模块级 `STEM_HE_F` 天干五合伙伴表。

### 测试与回归
- `tests/test_ziping_yong_coverage.py` 10→14 锚 + 护栏 ≥15 → **15 passed**；
- 全量 `pytest -k ziping --ignore=tests/test_ziping_15_2_evidence_provenance.py` → **1888 passed / 9 failed**（9 项=GPT 在途既有，无新增）；40 盘对账 取格 8/40、成败 27/40 持平。

## 二十一、V7.192 事件域：太岁冲运接线（宁缺勿猜口径）

**日期**: 2026-11-10　**范围**: `src/tongshu/reasoning/ziping_bridge.py` / `tests/test_ziping_shijian.py`

- 大运数据源：`engines` 层 `luck_pillars`（干支拼音）→ 桥层 `_PINYIN_STEM/_PINYIN_BRANCH` 映射中文干支，`_dayun_from_chart(chart)` 返回（大运列表, 起运岁 start_age）；`_current_dayun(dayun, start_age, target_year, birth_year)` 按 `idx=int((age-start_age)//10)` 取当前运，越界回退 `None`（宁缺勿猜，不臆测运限）。
- 触发判据扩展：`_shijian_from_facts(result, current_dayun)` 在「流年支冲命局四支」之外新增「流年支冲当前大运支」（CHONG 六冲表），证据对记为 `X Y(流年冲大运)` 与命局冲对并列；有冲对 → `EVENT_EXIST`（措辞保持「冲为事件触发符号，实际作用 p0 明示未核验（不判吉凶/应期）」）；无冲 → `EVENT_ABSENT`，措辞从「命局四支」扩为「命局四支及当前大运」。
- 消歧实测：1984 甲子 丙子 乙亥 甲申 男（起运约 9.69 岁，第 1 运丁丑）——2003 癸未：未不冲命局（子子亥申）但冲大运丑 → **仅运冲触发** EVENT_EXIST ✓；2001 辛巳：命局与大运均无冲 → EVENT_ABSENT 且措辞含「当前大运」✓。
- 测试：`test_shijian_taisui_chong_yun`（自建 1984 盘，断言触发对/锚点/未核验措辞）+ `test_shijian_absent_mentions_dayun`；六套件 104 passed，全量 ziping 1894 passed / 9 failed（GPT 在途既有），PZZQ 15/16（KNOWN_CONFLICTS 6 案不变）。
- 口径声明：太岁冲运只提供**触发符号**，应期/吉凶仍属解层（fail-closed 未实现不输出）；`current_dayun` 缺失（无 luck_pillars/越界）时行为与 V7.186 完全一致（纯命局冲）。

## 二十二、V7.193 SHIJIAN claim 治理放行（15.14 method audit PASS + 锚点勘误）

**日期**: 2026-11-10　**范围**: `ziping_bridge.py` / `judgment_claim_composer.py` / INT-05 测试契约更新

### 1. 锚点勘误（D6 依据链纠偏）

V7.186 时选的锚 `SUI_YUN.RE_EVALUATION.LIU_NIAN.005`（滴天髓「何为好」——运年**同气相助**）与 `SUI_YUN.RE_EVALUATION.DA_YUN_YIN_DONG.002`（滴天髓官杀**混杂病机**被岁运引动）**不承载「冲=触发符号」规则**，属证据链错配。对照《必补项登记》COV 治理（p0_v2/00_元数据/G1-A_Ontology/必补项登记_Coverage_Closure_Registry.md）的 D6 纪律，换锚为三命通会真承载切片：

- `SUI_YUN.RE_EVALUATION.SUI_YUN_BING_LIN.001`（SMTH 论太岁 行954）：「日干支冲克太岁曰征，**运干支伤冲太岁亦曰征**，太岁干支冲日干支亦曰征，其年则凶」——同句承载「流年冲命局」与「太岁冲运」两条触发路径；
- `SUI_YUN.RE_EVALUATION.FAN_YIN_FU_YIN.001`（SMTH 总论岁运 行968）：「行运以生月为运元，最怕行运与太岁冲克……岁运与日相对谓之返吟，岁运压日谓之伏吟，二者不利六亲」。

两锚均已在 G1（`p0_evidence.slice_ids()` 921 切片集）注册、校验状态=已校验。旧锚注销。

### 2. Method audit 结论：PASS（域级封闭解除）

15.14 audit FAIL 的判据是「production 上 0 事件方法链」。现状逐条核验：

| 项 | 状态 |
|---|---|
| 方法链入生产 | ✅ `run_ziping_judgment` → `_shijian_from_facts`（V7.186 流年冲命局 + V7.192 太岁冲运），提交 0679443b |
| 触发事实来源 | ✅ engines 层 transit 冲撞事实（非臆造）：1984 盘 2003 癸未仅运冲触发（未不冲命局子子亥申）实测 ✓ |
| 证据锚真实承载 | ✅ V7.193 换锚后两锚原文直接含「冲=征/不利」规则（见上） |
| claim 文本免责 | ✅ 恒含「冲为事件触发符号，实际作用 p0 明示未核验（不判吉凶/应期）」 |
| 结论级 fail-closed | ✅ UNKNOWN/EVENT_ABSENT/NOT_EXECUTED/FAILED → 0 claim 不变（EVENT_ABSENT=「无触发符号」≠「无事件」，伪判定防线保留） |
| provenance | p0 切片不在 `data/evidence` 语料树 → marker=None（与 GEJU/YONGSHEN 等全部 p0 域一致，非 SHIJIAN 特有） |

→ `judgment_claim_composer._FC_BLOCKED_DOMAINS` 清空 SHIJIAN（域级门解除）；结论级黑名单原样保留。

### 3. 测试契约更新（最小改动，保留 GPT 断言结构）

- `tests/test_int_05_judgment_claim_composer.py`：`test_s4_shijian_domain_always_blocked` → `test_s4_shijian_event_exist_released_after_method_audit`（EVENT_EXIST→1 claim+未核验断言）；末尾真实合成测试 4→5 claims。
- `tests/test_ziping_shijian.py`：锚断言参数化 `_SHIJIAN_ANCHORS`；`test_composer_keeps_shijian_fail_closed` → `test_composer_claim_matrix_after_release`（EVENT_EXIST 1 claim / EVENT_ABSENT 0 claim 双锁定）。
- 回归：10 套件 129 passed；全量 ziping **1894 passed / 9 failed**（GPT 在途既有，无新增）。

### 4. 与 COV 治理的衔接

- COV-001（岁运层命例型切片=0，D5 无承载）：本域 claim 只报触发符号不报吉凶，不受命例型缺口影响；岁运**吉凶/应期**解层在 D5 证据补齐前维持 fail-closed 不输出。
- COV-004（SMTH 行957 命例未切）/ COV-013②（小运×大运冲刑）：引擎均不消费，无缺口行为。

## 二十三、COV 引擎侧执行：NO_EVIDENCE 显式登记 + COV-019 实测纠偏（V7.194，2026-11-10）

**背景**：GPT 线《必补项登记_Coverage_Closure_Registry.md》（COV-001~029）总则：「宁缺勿滥/宁漏勿错」不得作为覆盖缺口结案理由；引擎必需且底本无确定答案的主题必须显式登记 NO_EVIDENCE，缺省行为 fail-closed——报「无原文依据」，不输出结论。本节执行引擎侧三项（用户 m10560「执行」指令）。

### 1. COV-013①② 显式 NO_EVIDENCE 登记（引擎侧缺省行为落盘）

- 新登记模块 `src/tongshu/reasoning/ziping_no_evidence.py`：机器可读 `NO_EVIDENCE_TOPICS` 表（COV-013-1 大运改变原局喜用神性质 / COV-013-2 小运与大运相冲相刑主灾，各含 verdict/evidence/default_behavior/guard 四字段）+ fail-closed 钩子 `assert_topic_not_concluded(topic_id)`（未登记→KeyError；NO_EVIDENCE→NotImplementedError 不输出结论；verdict 变更→RuntimeError 须走裁决）。
- 缺省行为（当前即成立，登记使其显式化）：
  - COV-013-1：`current_dayun` 仅流向事件域触发符号（`_shijian_from_facts`：流年冲命局 + 流年冲大运）；不参与任何喜忌/旺衰/用神重定——岁运篇底本检索零命中（登记表证据栏）。
  - COV-013-2：引擎不计算小运（ziping 线零计算路径）；小运起法两说另见 COV-006 待裁决。
- 结构守卫测试 `tests/test_ziping_no_evidence.py`（4 测试）：登记表完整性、钩子 fail-closed 三分支、**current_dayun 白名单**（`inspect` 扫 ziping_bridge：签名含 current_dayun 的函数仅限 `_shijian_from_facts`/`_engines_p0_synthesis`/`run_ziping_judgment`，且综合层内出现次数锁定 2=签名+转交事件域，新增大运参与喜忌路径即测试报警）、无小运计算标识符/函数。`ziping_bridge.py` `_current_dayun`/`_shijian_from_facts` 文档串加 COV 指针注释（V7.194）。
- 回归：no_evidence+shijian+bridge+yong_coverage 4 套件 39 passed。

### 2. COV-019 实测纠偏（登记描述与 live 线不符，证据链存档）

- 登记表 COV-019 称「引擎 L0 `combination_facts.anhe` 键在但恒 []（relations_builder L127 注释『排盘引擎无此域』）」。**实测（2026-11-10）该描述不适用于 live 生产线**：
  - live 线 `engines/common/l0_fact_builder.py:651-661` **已实现 anhe**：PZZQ 明文窄口径——只认卯申（卯藏乙/申藏庚本气=乙庚合，锚 PZZQ 900/1354/3228），仅相邻成立，且带暗合解冲裁决（PZ-0046 卯被申合→卯酉冲解）；引建于 2026-11-03 提交 `970edc8a`（P0 接线），早于登记表创建（11-10）。
  - `engines/common/relations_builder.py:127` 注释「BANHE/ANHUI/SELF 排盘引擎无此域」指 relations **类型层**兜底（且 ANHUI 暗会类型实际存在于 :254-269，与 anhe 暗合是两回事），非「anhe 键恒空」。
  - 「恒空」描述对应 `ziping-p0/`（2026-11-03 冻结副本 `ziping-p0/engines/common/l0_fact_builder.py:118` 仅初始化无实现），生产 bridge 走 live `engines.production_entry`，不受冻结副本影响。
- 处置：registry 系 GPT 线未跟踪文件，按铁律不代改；建议 COV-019 状态改「已补（窄口径）」——live 线按原典明文窄口径实现卯申暗合+解冲，其余支对无原典明文 fail-closed 不产出暗合，即「显式登记+fail-closed」选项在引擎层的落地形态。指针见 `ziping_no_evidence.py` 模块注释。

### 3. 边界

- 本节全部为引擎侧显式化登记与守卫，**不新增任何断语行为**；COV-013 两主题维持无结论输出，COV-006/COV-028 待裁决项不动。
- 提交范围：`src/tongshu/reasoning/ziping_no_evidence.py`（新）、`tests/test_ziping_no_evidence.py`（新）、`src/tongshu/reasoning/ziping_bridge.py`（注释）、本节文档。

### 4. COV-014/027/029 同类登记补齐（V7.195，引擎侧缺省行为类全收口）

- COV-014（从格破格后格局域喜神重定）：登记 `COV-014-CONG`——CONG_GE_001 只到「既从矣，当论所从之神」，破格后喜神未言 → 从格 PO 结论不得臆造/重定格局域喜神（八格破格救应喜神另有 PZZQ 成败救应章明文，不在本条）。从格入口走 `facts['special']`（special_pattern.py 属 GPT 热区，与 pzzq-018 同轨协调），协调落地前登记生效。
- COV-027（赋文专篇缺篇）：登记 `COV-027-FU`——六部底本无太微赋/病药赋/取用神赋独立专篇（事实排除已定）→ 引擎遇名目不得默认按赋文处理；实测 ziping 判定线（src/tongshu/reasoning + engines/common）三名目零锚点占用，守卫测试锁定。
- COV-029（缺省行为三件套）：登记 `COV-029-DELING`（①得时口径冲突——以 DE_LING.005 为准，judge_strength 已按此实现且「相气」零命中，§二十二已核验）/ `COV-029-JIXIONG`（②PZZQ 无吉凶寿夭专论——yongyao_resolve.py:15 明示「只裁决用药方向, 不判吉凶寿夭」，天然 fail-closed）/ `COV-029-SAME8ZI`（③同八字异寿夭——不可执行，报不可判）。守卫：寿夭字样仅允许 yongyao 免责声明 1 处；classic_check 无相气口径。
- 登记表现在 7 条目（COV-013-1/2、COV-014-CONG、COV-027-FU、COV-029-①②③），fail-closed 钩子三分支测试全覆盖；no_evidence 套件 8 测试 + shijian/bridge 邻接套件 27 passed。
- registry 状态建议（GPT 线同步）：COV-013①②/014/027/029 状态 待补（引擎侧）→ 已补（引擎侧登记+守卫）；COV-019 → 已补（窄口径，附 §二十三.2 证据链）。

## 二十四、COV-006 小运起法裁决落码：醉醒子法（V7.196，2026-11-10）

**裁决**：用户 m10713 问「子平引擎有小运算法吗？」（ziping 线 grep 零计算路径+V7.194 守卫锁定）→ 材料三选项（A 醉醒子法/B 古法/C 维持 fail-closed）→ 用户 m10735 选 **A=醉醒子法**。

### 1. 取法锚与算法规格

- 锚：`SUI_YUN.RE_EVALUATION.YUN_XIAN.002`（三命通会 行940 醉醒子：「男女小运皆由时生而行之，逆顺亦以年定…堕地即行乙丑，二岁丙寅，一位一年，周而复始…童限未交大运，专用此法」）+ `YUN_XIAN.006`（神峰通考「大运折除成岁，小运逆顺由时」，独立佐证）。落选：古法 `YUN_XIAN.001`（起点依据「解者谓」推演、单一承载、与渊海变体 `YUN_XIAN.004` 正面冲突）、渊海变体 `YUN_XIAN.004`。
- 算法规格：堕地（虚岁1）行**时柱次一位**，一位一年，60 甲子周而复始；**逆顺以年命阴阳定**（阳年甲丙戊庚壬顺行、阴年逆行，男女同法）——从切片已校验语义注释「逆顺以年命阴阳定」。原文「阴命阳年逆行亦然」存在文本疑义（若「年定」=年干阴阳，该例应为「阴命阴年」）；本项目取年干阴阳读法（切片注释口径）。禄命线旧注释 `bazi_engine.py:302`「男顺女逆」为另一种读法，该线已弃用醉醒子，不受影响。
- 虚岁口径：堕地=虚岁1（与盲派 nominal_age、禄命线 2026-10-21 用户核验口径一致）。

### 2. 落码（ziping 线，排盘事实层）

- `ziping_bridge.py`：`_XIAOYUN_ANCHORS`/`_YANG_STEMS`/`_xiaoyun_from_chart(chart)`（返回 `(时柱干支, forward)` 或 `(None, None)` 不猜）+ `_current_xiaoyun(hour, forward, birth_year, target_year)`（虚岁→干支）。
- **消费边界（COV-013② fail-closed 维持）**：小运=排盘事实层时间线；不参与喜忌/旺衰重定、不独立出吉凶断语、不作为事件域触发符号——小运吉凶属「与大运及柱中用神日主较量」框架（YUN_XIAN.002/003/005 旁参语义），未立项不消费。
- `ziping_no_evidence.py`：COV-013-2 default_behavior/guard 更新（起法已裁决落码；「冲刑主灾」断语仍零命中 NO_EVIDENCE）+ 新增 `DECIDED_TOPICS["COV-006"]` 裁决存档（锚/落选方案及理由/规格/消费边界/engine_site）。
- `tests/test_ziping_no_evidence.py`：`test_no_xiaoyun_computation` → `test_xiaoyun_zuixingzi_algorithm`（原文样例：阳年甲子时 1岁乙丑/2岁丙寅/3岁丁卯；阴年逆行 1岁乙丑/2岁甲子/3岁癸亥；周而复始：壬戌时 1岁癸亥/2岁甲子；年阴阳定方向；六分支不猜）+ `test_cov006_decision_recorded`。守卫升级：xiaoyun 标识符仅限 `{_xiaoyun_from_chart, _current_xiaoyun}`，`_engines_p0_synthesis`/`_shijian_from_facts`/`run_ziping_judgment` 禁消费。
- smoke 实测：阳年甲子时 ('甲子',True) 1岁乙丑/2岁丙寅/3岁丁卯 ✓；阴年逆行 ✓；wrap ✓；`_ganzhi_of_year(1984)=甲子` ✓（编辑事故恢复核验）。

### 3. 跨线现状登记（禄命线不动，差异留痕）

禄命线（bazi 排盘/luming）已有用户落定口径，本节**不改**：

- `engines/bazi_engine.py:2096-2100`：2026-10-21 **用户定夺取古法**——男 1岁丙寅顺行/女 1岁壬申逆行，1岁=起点本身，虚岁 seq0+step*(age-1)（用户核验过旧式错位一年）；醉醒子「由时生而行之」为备查未采用。
- `engines/bazi_engine_spec.py:1268-1304`：2026-09-14 裁决一=五行精纪卷33 古法（宋代四方一致，SOURCE_VERIFIED）。
- `luming/engine.py:1177-1179`：2026-10-21 统一用古法 xiao_yun_pillars（修复厄会②运层/流年层卯/丑错位）。

**差异表**：禄命线=古法（起点丙寅/壬申、性别定方向、1岁=起点本身）；子平线=醉醒子（起点时柱次位、年干阴阳定方向、1岁=次位）。同一排盘事实两线答案不同——底本并录两说未裁断（切片备注「SMTH并录两说，未裁断」）+ 两线用户分别裁决（2026-10-21 古法 / 2026-11-10 醉醒子）。如需平台统一为一法，属独立裁决立项（涉及禄命线厄会②/发祸三重件等消费面重验），不在本节。

### 4. 边界与提交

- 本节全部为子平线引擎侧（`src/tongshu/reasoning/` + `tests/test_ziping_no_evidence.py` + 本文档）；不触 bazi_engine/luming/bazi_engine_spec。
- COV-013② 结论输出维持 0；小运无吉凶断语；「冲刑主灾」维持 NO_EVIDENCE。
- registry 状态建议（GPT 线同步）：COV-006 → 已裁决（醉醒子法，子平线；禄命线古法维持，见 §二十四.3）。

## 二十五、40 盘对账差异全量分类修复：成败 27→2、取格 8→1（V7.197–V7.199，2026-11-10）

**背景**：V7.188 起 40 盘对账（`scripts/ziping_rule_audit.py`，seed=20261107）成败差 27/40、取格差 8/40 只记数未分类。本轮全量取证分类（探针 `scripts/_probe_cb_r17.py`/`_probe_cb_r17b.py`/`_probe_cb_r17c.py`，输出 `_audit_r17_full.txt`/`_probe_r17b.txt`/`_probe_r17c.txt`），逐条对 PZZQ 原文/切片定根因：**配合级（口径差异，登记）vs 引擎/核验器真缺口（直接修）**，修完跑真值对照。

### 1. 对账口径修正（audit 脚本，2026-11-10）

- `CB_EQUIV` 败格族等价：核验器 BAI ≡ 引擎 PO/CHENG_ZHONG_YOU_PO（PZZQ L1149「败者犯格之忌也」，格名仍存，同一判定族）；CHENG≡CHENG；NE≡NE。
- `ge_base()`：格名剥离括号后缀（印格(官印双全)≡印格）。
- 特格族分流：化/从/专旺等核验器无判据的格名（`SPECIAL_GE_PREFIXES`）单独计数，不算取格/成败差。

### 2. 引擎修复（`engines/common/ge_jie_layer.py`，V7.197 六处 + V7.198 五处 + V7.199 一处）

1. **食神格生财露煞**（V7.197，缺口A）：`wealth_and_sha_templates(*, sha_tou=False, cai_tou=False)` 支持双神透 gate；食神落盘前正交块 `if _ss_cai_seen and _qs_def_xi: _ss_po += wealth_and_sha_templates(sha_tou=True)`（生财露煞与喜神分支正交；提纲太旺/就煞印路径不豁免败句）。口径：PZZQ L1132 徐注「四柱见财，为食神生财…若四柱透煞…忌财党煞」+ L1146 败句 + L1154「露煞则财转而生煞」——成/败句的「财」都是**见**（含藏干；早前把 PZ-0118 枭夺食语境「无财为救应」的财透干口径误挪用，已纠正）。`_ss_cai_seen`=透财 or 藏干扫（`_ss_seen_god`）；就煞印条件同步改 `not _ss_cai_seen`（财藏亦算有财）。
2. **正官四路径删地支刑冲毒模板**（V7.197，缺口C）：po_ge 中的 `{'type':'地支','branch_cond':'刑冲'}` 模板要求 `sanxing_survive` 键，而 `resolved`（l0_fact_builder L771-783）永不生产该键 → po_ge_evaluation_complete 恒 false → 正官格破格要件齐备也落 NOT_EVALUABLE。删除四处（原 L787/809/831/851）；依据 DTS「刑与穿兮动不动」（刑穿冲动静未授权→不升级破格）+ 冲已由冲月令破格精确覆盖。
3. **冲月令破格收窄四生月令**（V7.197）：`apply_he_po_ge` 加门 `mz∈{寅,申,巳,亥}`——PZZQ L2023-2026 徐注「子午卯酉之冲，有成有败…忌者冲而去之为成，喜者逢冲为败」随局而定不擅断；L2028「四墓不忌刑冲」；L2686「寅申巳亥四生之地为重，气尚微弱，逢冲则坏」+ DTS L2687「生方怕动库宜开」。四专（子午卯酉）随局不判=宁缺勿猜；DT-0380（卯酉冲破亥卯未印局）登记未实现。
4. **禄劫「透/逢」分口径**（V7.197，缺口D）：新增 `_god_gans_seen`（透干+全支藏干）。PZZQ L1142「建禄月劫，**透**官而**逢**财印，即同官格；**透**财而**逢**食伤，即同财格；**透**煞而**遇**制伏，即同煞格」——命名人元（官/财/煞）须透干；配合神「逢/遇」=见（藏干亦算）。三配合路径补齐；po_ge 缺失模板条件改双透（`_yin_tou`）。
5. **伤官见官破格收口**（V7.197，缺口B连修）：见官模板加 `gate='tou'`（PZZQ L4269「己官两透」/L1783「天干透丁」——「见官」=透官；存在性口径使金水例外形同虚设）+ 财印通关豁免 `_sg_tongguan`（财印见，DTS L260 原注「大率伤官有财，皆可见官，伤官无财，皆不可见官」+ PZZQ L4267「伤官生财，财生官，官星不但无碍」）。蔡元培丁卯癸丑丙申戊子（己伤→庚财藏申→癸官透）PO→CHENG。
6. **阳刃并透两势**（V7.198）：官煞+伤官并透 → 印透→NE（L1245「若得重印以去食作，则阳刃格成矣」——重印量化未定宁缺勿猜，穆同知造 L4598「须视四柱之配合如何，未可一定」同旨）/ 印不透→PO（伤食制官煞格破）。**财印露门误读撤回**：曾按 L1117 成句加「官煞透+财印俱不透→NE」，读 L1140-1141 徐注「以官煞制刃，格局最美…财印并见为吉」+ L1220 石友三（财印不透而成）+ L1223 龙济光亲证后确认**财印是辅弼非成格前提**（成的机制=官煞制刃+不见伤官，L1159 败句徐注「若无官煞，则刃旺而无裁抑之神」），引擎与核验器两侧同撤。
7. **印格旁路修复**（V7.198）：默认印格路径 `_yin_po=[] if _yin_heavy_po else [{'组合','ANY',['正财','偏财']}]` 裸存在性模板**旁路了 V7.53b `_CAI_PO`**（财有根且无比劫救才破格）→ 戊戌庚申癸未己未（财只藏中气无根）伪 PO。改回 `_CAI_PO`。同段**印重双判据对齐**：`_yin_heavy_po` 补 dangling 项（印当令+透≥1=印成党，V7.38 锚 SFTK L7770），与 `_yin_ren_d2` 同式——此前规则串说「印重破格:无」而 po 照破（自相矛盾）。
8. **印轻二径守卫修正**（V7.198）：`_attach_ge_evidence` 对 印轻逢财/印轻逢煞 的守卫含「财+劫同现硬置 NE」（早于 V7.53b 的过时判据，与 `_CAI_PO` 机器可判矛盾——劫透解救 po=[] 仍被 NE 覆盖）。只留数据完备性门 `not _hidden_complete or not _members_complete`。
9. **印轻逢煞 gate 改煞见**（V7.198）：`sha_gans and not yin_gans` → 藏煞扫描 `_sha_rep`（透干优先，无透取支藏七杀）——.007 成句「印轻逢煞」的「逢」=见（戊寅甲子乙卯丙戌 煞辛藏戌，煞生印=财生煞通关机制）。
10. **七煞 fallback 判据**（V7.198+V7.199）：V7.198 先把 fallback（非「财透无制」败句、非「身强逢制」成句）改为无条件 NOT_EVALUABLE（旧「无财透即 CHENG」超判修复）。V7.199 按救应篇明文开**败中有成通道**：`cai_gans and (shi_gans or shang_gans)` → `七煞格(败中有成)`，po=[财tou]，xi=制神——PZZQ L1210/L1212 谭延闿案亲证「食神制煞，而中隔以财，格之败也。喜乙丁隔癸，木不生火，煞坐食地，**为败中有成**…财逢煞而食神制煞以生，有救应，即是败中有成，为贵也」+ 扶抑篇 L993「月令七煞透干，取食神制煞为用」（用神专取食神）。印化路径无救应明文维持 NE（宁缺勿猜）。谭延闿 yong 链路恢复（NE 曾被 `_usable_ge_cheng` 拒绝断用神→pzzq-011 MISS→coverage 15→14）。

### 3. 核验器修复（`src/tongshu/reasoning/ziping_classic_check.py`）

1. **derive_ge 本气立格**（V7.197）：对齐 bac206b8 裁决（撤 PATCH-GE-TOU 透干取格、回退本气立格；核验器旧「透出优先」未对齐）。格名=月令本气（四季月非土日主取土=四季土格；透干只定「格之真假」，YUE_LING_GE_JU.001「格之真者，月支之神，透于天干也」）。取格差 8→0 的主因（其中 3 条本就是括号后缀假差异、2 条特格族、1 条 V7.34 无根口径配合级）。
2. **刃表特例**（V7.198）：`_RENGE={"甲":"卯","丙":"午","戊":"午","庚":"酉","壬":"子"}`——戊午月本气丁=正印仍作阳刃论（V7.83 锚 PZZQ L4505），核验器缺刃表致 己巳庚午戊辰甲寅 取格差。
3. **八格判据透/见分口径**（V7.197-198）：财格「财透七煞」煞须透干（徐注 L1151，藏干毛状元反例 L3487）；正官「伤克」=伤官**透**（食神不克官，L1149）；食神枭透干；七煞「逢财无制」财透干（L1155「财党煞攻身」）+ **删「七煞逢冲」过度延伸条款**（.008 败句无此条，旧条款月支任意刑冲害破都触发）；禄劫镜像引擎透/逢口径+透煞遇制伏成路。
4. **金水伤官例外**（V7.197）：窄口径 `STEM_ELEM[dm]=="金" and mb∈{亥,子}`（徐注 L1156「惟金水伤官，金寒水冷，调候为急，可以见官」——金寒水冷专指冬月金伤官）。丁酉壬子庚午庚辰 BAI→CHENG。
5. **全局四生冲月令条款**（V7.198）：月支∈寅申巳亥+被年/日支六冲+冲伴无六合参与 → BAI，加 `_SIX_GE` 六格门（建禄月劫/阳刃月令=比劫不入格神 ti|xi，镜像引擎 `apply_he_po_ge` 的 `relevant=mwx∈(ti|xi)` 门；半合解冲方案作废——引擎冲解只有六合/三合齐全/会局/survive 四态无半合）。
6. **七煞 CHENG_ZHONG_YOU_PO 状态**（V7.199）：食/伤制神透+财透+非身强（不满足 .007 成句）→ CZP「食神制煞而中隔以财，败中有成(救应)」；印化+财透维持 NE；身强逢制 CHENG 不变。
7. **阳刃全透干口径+并透两势**（V7.198b）：官煞/伤官/财印全改透干（乾隆盘藏癸伤官误触发并透 NE）；并透：印透→NE 重印/印不透→BAI 带伤食制官煞格破；撤「财印不露 NE」（§2.6 同源误读）；CHENG 分支显式 `state="CHENG"`（add() 不置 state 的 bug 被测试抓到）。

### 4. 测试与对账结果

- `tests/test_ziping_classic_check.py`：3 处 derive_ge 断言改本气立格（财格 via=本气/建禄月劫/阳刃 detail）、龙济光拆 煞刃成+石友三并透 两锚、新增 官格伤透 BAI/官格财印成（食神不克官）、谭延闿 CZP 锚；24→41 passed。
- `tests/test_ziping_yong_coverage.py`：新增 `test_qisha_jiuying_baizhongyoucheng_tan_yankai`（谭延闿 七煞格(败中有成)/CHENG_ZHONG_YOU_PO/用神=木 全链路）。
- **40 盘对账终态**（`_audit_r17_v5.txt`）：取格 **1/40**（甲午己巳壬午壬寅 V7.34 无根须印口径，登记配合级）+特格族 2；成败 **2/40**（乙未丁亥丙申辛卯 七煞身强 metric 分歧——核验 judge_strength vs 引擎 dm_tier；丙寅己亥丁卯辛亥 正官「破」的效力——核验器害破 only→NE vs 引擎 CHENG，均登记配合级）+特格族成败 1（从杀 vs 财格，特格族）。**12 案 12/12 全平**（含 谭延闿 CZP≡CZP、王克敏 CHENG、龙济光/乾隆 CHENG 恢复原典亲证）。
- PZZQ 覆盖：`scripts/ziping_pzzq_replay.py` **15/16**（locked 15 全 HIT 含恢复的 pzzq-011 谭延闿「月令七煞透干，取食神制煞为用」；known conflicts 6 案不变）。

### 5. 提交与边界

- 提交 `9a224301`（核验器侧 5 文件：ziping_classic_check.py/ziping_rule_audit.py/test_ziping_classic_check.py/test_ziping_yong_coverage.py/本文档 §二十五，+368/−90）。
- **引擎侧 ge_jie_layer.py 暂不提交**：V7.197-199b 引擎修复与 GPT 在途 fail-closed 求值硬化在 evaluate_po_ge/apply_he_po_ge/_attach_ge_evidence 内深度交缠（本线六格名门依赖 GPT 未提交的 `_month_clash_actions_complete` helper 与 complete 旗标语义），干净拆分会产出未经验证的破损提交，整体提交则混入他线在途工作（V7.188 分线铁律）。留在共用工作树（回归 1899/16 已验证），待 GPT 在途合线或统一接线阶段一并收编。
- 本节未动 GPT 热区（special_pattern/relations_builder/l0_fact_builder/registry）；残余 2+1 项成败差异与 1 项取格差异均为配合级登记，属 pzzq-017/019/018 同族待协调项。

### 6. V7.199b：GPT 在途契约对齐与冲月令门终版（2026-11-10，同日第二轮）

V7.199 落码后全量回归新增 20 失败，逐案取证（探针 `_probe_yr_v7199b.py`）分类为「GPT 未跟踪在途测试契约 vs 我方口径」冲突。裁决原则：GPT 契约与原典一致→引擎对齐契约；GPT 契约无原典锚→登记不改（不得回退原典裁决，不得改 GPT 未跟踪测试文件——V7.188 铁律）。

1. **冲月令门终版（两轮纠错）**：第一版以 `mwx∈(ti_wx|xi_wx)` 为「喜者/忌者」轴破格——被探针推翻：顺刃路径把日主五行置入 xi_wx，阳刃格恒 relevant，龙济光/乾隆 翻 PO。**教训：engine 的 ti|xi 是喜忌轴，不是徐注「喜者/忌者逢冲」的格体轴，不可用作冲月令门**。终版=**六格名门** `_SIX_GE_MONTH_CLASH=('正官格','财格','印格','食神格','七煞格','伤官格')`（月令本气=格神=喜者）：六格被存活相邻冲→破格（L2023-2026+L2686，四生四专同口径）；四墓门先行（L2028 不忌）；阳刃/建禄月劫/特格→不破（.008 无冲条+龙济光 L1223 煞刃格成亲证）。GPT fail-closed 契约（conflicting/omitted/unknown 冲解不得当已评）由 actions_complete False→complete=False 联动满足。
2. **禄劫「透/逢」精确化**：path② 门 `财【透】+食伤见`、path③ 门 `煞【透】+制伏【透】`（遇制伏=功能要求，镜像七煞格 V7.190）、**path④ 泄秀=财官煞【透干】全无+食伤【透】**（1980-04-15 庚申庚辰戊午戊午 契约：庚食神透→泄秀 verified 用神可得；申藏壬财不挡；甲寅×4 食伤不透→NE）；path① 维持 `官【透】+财印见`（甲戌盘裁决）。
3. **CZP 窄化**：加 `煞【透】+印不透`（L991「月令七煞透干」；煞藏申→七煞格 NE；印透→配合级 NE 不擅断）。谭延闿案不受影响。
4. **阳刃伤食并计+成中有败精化**：L1245「带伤食制官煞」=食神+伤官并计（po required 补食神；并透门 sg 扩伤食）；L1220 石友三「无如月干辛金合丙…为成中有败也」+L1222 郭松龄——官煞被合去（五合伙伴在干）→成中有败(CZP)；未被合→带伤食制官煞格破(PO)；印透→须辨重印 NE。
5. **_CAI_PO 透财须藏根**：透财全无藏根=虚财不破印（L1130「财无根气不能用财破印」）。
6. **核验器镜像**：全局冲月令条款扩四专（六格名门）；禄劫 ②③④ 透干口径；阳刃伤食并计+合去精化；CHENG 分支显式 `state="CHENG"`（add() 不置 state 的缺陷由测试抓出）。
7. **契约冲突登记（7 项，GPT 在途未跟踪测试，待合线裁决）**：officer_killer_pair（GPT 期望财存在性即破印伪 hit，无败句锚）、rescue_scope×2（GPT 接受集无 NE，引擎 NE=原典诚实）、resource_wealth×2+visible_wealth（GPT 旧印轻守卫 vs V7.53b 财有根判据）、primary_bing_tie（GPT 期望禄劫配合全透干，引擎 path① 逢=见）。
8. **回归终态**：全量 ziping **16 failed / 1899 passed**（=GPT 基线 9 + 登记冲突 7，0 新增）；40 盘 12案 12/12、取格 1/40、成败 2/40（均配合级登记）；PZZQ replay 15/16。

## 二十六、pzzq-017/019 配合级证据链深采（2026-11-10，Round 21）

**两案原文全采**（`registries/source/raw/PZZQ_子平真诠_沈孝瞻原文.md`）：
- pzzq-017 朱有卿（癸巳 壬戌 乙巳 戊寅，财格）：L486「戊癸合而间乙，惟其不合，故财局可以用印」+ L3351「壬癸虽不通根而进气，伤官暗藏而旺，土燥木枯，非用印不可」（want=水=印）。
- pzzq-019 钜商王某（癸酉 癸亥 戊子 丁巳，财格）：L543「两癸合戊，虽不以合论，而终有合意。为财格用禄比…时逢归禄」+ L3353「盖以劫护印分为财用也」（want=火=戊禄在巳）。
- 关键对照：pzzq-015 甲寅己未甲寅乙亥（单财己透合日主→用财，locked HIT，PZZQ「甲用己财…专向日主也」）与 019 同为「财与日主五合」机制，沈裁不同。

**判据候选（三因子，未见单句明文，不强判）**：①财透数——015 单财专向→用财；019 双财争合（虽不以合论）→禄比分财；②禄刃在支——019 时逢归禄（巳=戊禄）；015 甲寅×2 虽禄×2 但单财专向压倒；③印透可护——019 丁印在时（劫护印分财用）；017 印壬癸进气+伤官暗藏而旺（巳中丙×2）+土燥木枯→非用印不可。
**引擎现状**（探针 2026-11-10）：017 got=金（表官杀，cnt['官杀']>=1 经巳藏庚）；019 got=水（V7.191 日主合财规则，两癸合戊→财为用）；两案 state=GE_FALLBACK 且 ge 层 xi_wx 已各自正确（017 xi=水/019 xi=火）——yong 表 blunt cnt 分支覆盖了 ge 层 shape 级喜神。修法候选：财格分支加「印透不可用（合绊）→禄比」判据链，但 015/019 同机制异裁使单 gate 风险高（可能翻 015 locked HIT），维持配合级登记，待 论财格 全章补采后再判。
**replay 分母修正**：coverage 分母排除 KNOWN_CONFLICTS（pzzq-010 亦在其中）→ 终态 **15/15 全 HIT** + 6 案配合级登记（017/019 注释扩为原文证据链+判据候选）。

## 二十六.1 V7.200 落码尝试与回退（2026-11-10，Round 22）

**尝试**：按 §二十六 三因子证据链先试最窄 gate——「财格+shape=佩印 → 用神=印」（形态表 `_GEJU_XIJI_SHAPE['财格']['佩印']` weak/strong 喜均印首选 + L3345「身弱得印, 用神即在于印」）。实测：pzzq-017 朱有卿→水(印) HIT、pzzq-019 王某→火(印) HIT，**但 pzzq-004 张耀曾（locked HIT）翻 MISS**（got=木印 vs want=金财）。净收益为负，回退。

**关键发现（佩印形态内部判别）**：三案同为 财格+佩印，沈裁两向——
- 张耀曾：**用财**（L495「乙庚相合，通月令之气，虽遥隔而仍合，以庚劈甲引丁为用」——印乙被财庚五合去+甲印被庚劈制 → 印全部被财合/制 → 用财）。
- 朱有卿：**用印**（L486「戊癸合而间乙，惟其**不合**，故财局可以用印」——印癸与财戊之间隔日主乙 → 合不成 → 印可用；L3351 伤官旺+土燥木枯非用印不可）。
- 王某：**用印**（L543/L3353 禄比分财护印，戊禄在巳=印丁之根——「用禄比」与「用印」五行同为火，无矛盾）。

**判别式**：财格佩印 → 印被财合去（或制尽）→ 用财；印不被合去 → 用印。
**机器缺口**：`stem_combination_facts.wuhe` 只录五合干对、不分「紧贴/遥隔/间隔」三态——朱有卿 癸戊 wuhe 被录但原典间乙不合；张耀曾 乙庚遥隔原典仍合（通月令）。遥隔合终裁=PZZQ L480-495「制于势然也…合而不敢合」+L484「各视其格局配合而已」——case-specific 权衡（间隔干是否克其一/是否通月令），无单一机械判据，属配合级。回退后 yongyao_resolve.py 留注释档；017/019 维持 KNOWN_CONFLICTS（replay 15/15 全 HIT 不变）。
**结论**：修复前提=实现「五合间隔/遥隔终裁」判据层（PZZQ L480-495 语义：①间隔干克其一→合不成 ②通月令之气→遥隔仍合 ③否则各视配合）——登记为独立立项（COV 同族），本轮不冒进。

## 二十六.2 V7.201 印重两说收平：pzzq-020 朱家宝（2026-11-10，Round 23）

**冲突**：朱家宝造 庚申 乙酉 癸未 乙卯（癸日主 酉月偏印格），沈徐注 L543「朱造 印格用食」want=木；引擎病药层 primary_bing=YIN_DUO_MAI_ZI（印太重）取 财（火=制）损印——印重两说（财损印 vs 食泄秀）在源1 病药层无食伤边（`yongyao_resolve` 边构建只有 制/化/帮/暖，主药选择 `kind=='制'` 无条件优先）。

**原典判别式（两侧各有亲证，非单翼裁断）**：
- 用食泄翼：PZZQ L1146 成句「身印两旺，用食伤泄」+ L543 朱家宝亲证（财金不透，食乙×2 透+卯本气根）。
- 用财损印翼：pzzq-007 财坐酉本气亲证（丁日主 印木太旺，取财金损印）；L1130「财无根气不能用财破印」（虚财无力）；渊海印绶章「身旺印多，财运无妨」。
- **判别式**：制药（财）透干或本气根在 → 用财损印；财不透且无本气根（仅藏中余=虚财）而食伤透干或本气根在 → 用食泄；两翼皆无力 → 维持原主药（不猜）。

**落码（`engines/common/yongyao_resolve.py` 两处，印病 gate=bw==SHENG_BACK[dm] 收窄）**：
1. 边构建补 **印病食伤泄边**（制/化之后、帮之前）：`add(SHENG[dm], '泄', '食伤泄身之旺(身印两旺用食伤泄)')`——泄气太重之病源即食伤不可再泄，官杀/财/比劫病各有对位边（杀重药=食伤制煞等），仅印病缺。
2. 主药选择加 **透干/本气根裁决**：`zhu`（制）成立且病=印时，若制药 stem_n==0 且 ben_n==0（虚财），而泄边 stem_n>=1 或 ben_n>=1 → 泄升主；否则维持。数据源 `facts['wuxing_power']['wuxing_power'][wx].{stem_n,ben_n}`。

**测试安全性（gate 收窄验证）**：unit 级 yongyao 测试全部用官杀/财病 debate（甲 bw=金≠水印、戊 bw=木≠火印）→ gate off；frozen `ziping-p0/tests/test_yuanjuan_matrix.py:832` 锁 `_bing_yao_map=={财,比劫}` 不受影响（V7.201 不动药表，只加 resolver 边）；1983 盲派锚 癸亥壬戌乙未壬午 制=土有本气根 → 不升泄 → 不变。

**验证**：朱家宝 got=木 kind=泄 ✓ HIT（新入 CASES）；pzzq-007 got=金（调候）✓ 不变；40盘对账 12案 12/12、取格 1/40+特格族 2、成败 2/40+特格族 1 全部基线不变；replay **16/16**（known conflicts 剩 010/018/021）；checker+yz 六套件 107 passed；全量 ziping **16 failed / 1899 passed**（=9 GPT 基线+7 登记冲突，0 新增）；yong_coverage 18 passed（新增 020 锚+判别式护栏，护栏 ≥15→≥16）。

## 二十六.3 V7.203 五合终裁判据层：pzzq-017/019 收平（2026-11-10，Round 24）

**前提回望**：§二十六.1 V7.200「佩印→印」blanket gate 因机器缺「间隔/遥隔终裁」翻 pzzq-004 张耀曾而回退；§二十六 落定的判别式「印是否被财合去」缺机器可判的合之成立条件。本轮从 PZZQ 论十干配合性情章（L476-496）采得三态判据。

**原典三态语义（L476-496 原文逐句）**：
1. **紧贴作合**（span=1）：默认合成立。
2. **间隔（span=2）**：L480-481 原文「隔于有所间也…甲己中间以庚间隔之，则甲岂能越克我之庚而合己？此制于势然也，合而不敢合也，有若无也」——间干克其配偶之一 → **合不成**；徐注 L482「有所间隔，则不以合论，然**间隔非必克制也**」+ 杨增新案 L483-484 甲己间丁（木生火生土=以印化官）——间干不克 → 仍作合论。
3. **遥隔（span=3，年↔时）**：L488-489 原文「隔位太远…不能相合一般…合而不能合也，**半合也，其为祸福得十之二三而已**」；徐注 L490-491「或虽遥隔而仍作合论，**各视其格局配合而已**」——亲证成立条件=**配偶得禄或刃于月令「通月令之气」**：张耀曾 L495「乙庚相合，通月令之气，虽遥隔而仍合」（庚禄在申=月支申）；反证 朱有卿 L486「戊癸合而间乙，惟其不合」（戊墓在戌，禄巳/刃午不在月支，且间乙克戊）。

**落码（`engines/common/yongyao_resolve.py`）**：
1. 模块表 `_LU_ZHI`（十干禄位）/`_REN_ZHI`（阳刃）/`_LU_WX`（禄位五行）+ `_wuhe_span_state(facts,a,b)` 三态函数（adjacent/blocked/remote_he/remote_no/unknown；span 由四柱干位推导；blocked=间干 KE 其一方；remote_he=任一配偶禄或刃==月支）。
2. 财格分支 ①争合修正：与日主五合的财==1 → 专向日主用财（015 locked）；**>1=争合妒合（L545 两壬夹丁）→「虽不以合论，而终有合意」(L541-543) 不走专向**，归禄在时（禄支==时支）则用禄五行（L543「时逢归禄」王某 戊禄巳=火）；争合而禄不在时 → 不猜落后续分支。
3. 财格分支 ②佩印合去终裁（shape=='佩印' 门）：印财五合对存在时按三态裁「印是否被财合去」——adjacent/remote_he → 用财（张耀曾）；blocked/remote_no → 财局可以用印（朱有卿 L486）。

**验证**：四案探针全对——004 张耀曾 got=金 ✓（locked）、015 甲用己财 got=土 ✓（locked）、017 朱有卿 got=水 ✓（was 金）、019 王某 got=火 ✓（was 水）；replay **16/16 → 18/18**（017/019 入 CASES，known conflicts 剩 010/018/021）；40盘对账 12案 12/12、取格 1/40+特格族 2、成败 2/40+特格族 1 全部基线不变；六套件 82 passed（yong_coverage +017/019 锚+`test_wuhe_span_state_three_states` 三态单测，护栏 ≥16→≥18）。
**非通则声明**：遥隔判据以「禄刃通月令」为最小机器化（L495 亲证），「各视其格局配合而已」=原典明文承认非通则；间干不克 span=2 作合论以 L482「间隔非必克制」+杨增新案为锚；登记 §二十六.3 备案。

## 二十六.4 V7.204 扶抑扶边层：pzzq-010 蔡孑民收平（2026-11-10，Round 25）

**案情**：pzzq-010 蔡孑民（丁卯 癸丑 丙申 戊子），沈断 L975「丑中癸水官星透出，子申会局助之，水旺火弱，用劫帮身为用神」——属 PZZQ 扶抑章（L967-968「扶抑日元为用。扶有二，印以生之，劫以助之是也。抑亦有二，官煞以克之，食伤以泄之是也」）。引擎病药层（源1）取制边（历史两态：水旺官杀病→取土制 / 伤官土病→取木制），皆与沈断（帮身）不符，登记配合级。

**原典判据（DTS L215 体用正法，源5 既有注释但生产路径 inert）**：「日主弱, 则提纲有物, 帮身以制其神者, 亦皆为我用; **提纲食伤财官太旺, 则取年月时上印比为喜神**」——身弱且提纲食伤/财/官旺时，印比（扶边）为喜神，病药制边让位。两案亲证：伍朝枢（丁亥 丙午 壬寅 己酉）财官两旺身弱**用印**（L971）；蔡孑民 水旺火弱**用劫**（L975，丁劫透年干）。

**判别式（V7.204 落码）**：①身弱=得令得地双失（日主 wuxing_power `ben_n==0` 且 `ling_state∈(休,囚,死)`，DTS 得令/得地双失口径）；②病∈{官杀 KE_BACK[dm], 食伤 SHENG[dm], 财 KE[dm]}（印病走泄损 V7.201、比劫病走制，均不在此列）；③扶边=印（SHENG_BACK[dm]）/劫（dm）年月时在局，**透干有力者优先**（蔡造丁劫透干 → 用劫），同档印主比辅（DTS L215 喜印主比辅；伍造印劫皆藏支 → 用印）；④扶边不受 `_safe` 帮病剔除约束（L215 该款为身弱取喜神明文规则，印比扶身不因兼生次病而废——蔡造火生土伤官，沈仍用劫）；⑤扶边被天干五合合绊（medicine_blocked）则不升，维持原主不猜（fail-closed）。

**落码（`engines/common/yongyao_resolve.py` 两处）**：①暖边后新增扶边构建（kind='扶'，含 tier 排序 min((tier, 印0/劫1))）；②主药选择处新增扶升主（制/V7.201 泄 之后、uniq[0] 兜底之前；合绊守卫）。

**验证**：五案探针全对——010 got=火 kind=扶 ✓（收平）、002 got=土 kind=制 不变 ✓（泄气病扶边印土与制边同元素，去重保制，行为不变）、007 got=金 不变 ✓（印病不在 scope）、020 got=木 kind=泄 不变 ✓（V7.201 保持）、009 got=水 不变 ✓（身旺扶门 off）；replay **19/19**（010 入断言分母，known conflicts 剩 018/021）；40盘对账 12案 12/12、取格 1/40+特格族 2、成败 2/40+特格族 1 基线不变（audit 比对取格/成败，不涉用神层）；六套件 83 passed（yong_coverage +010 锚，护栏 ≥18→≥19）。
**备注**：引擎 primary bing 诊断（伤官土太重）与沈断（水旺官杀）仍异——本轮收平的是用神层结果（扶边判据对两类病同出印比喜神，DTS L215 对「食伤财官」并列覆盖）；诊断层差异登记备查，不动 GPT-M bingyao_layer。

## 二十六.5 V7.205 调候案收平：佩印×财专向并存用神归印（2026-11-10，Round 26）

- **案情**：pzzq-021 己酉 丙子 戊辰 癸亥（戊日主 子月正财格）。沈徐注 PZZQ L530-531「丙火调候为用，无如戊癸相合，日主之情，向财不向印，癸水虽不能越戊克丙，而日主向用之情不专矣」+L533「用神之情，不向日主…皆非美朕也」。**021 并非调候优先级冲突**（前登记口径有误）：用神=丙火印（佩印+调候双职），戊癸合只是「用神之情不专」之瑕。财格佩印 L3341「孤财不贵，佩印帮身，即印取贵」+L3344 徐注「盖需要佩印，必是身弱…财印相战，不得已而用之」+L3447-3448「财格佩印…其最要之条件即为财印两不相碍」。
- **引擎实况**：ge=财格 CHENG shape=佩印 xi=['火']（格层已正确喜印）；GE_FALLBACK dump：ge_fallback_source=源2:格体喜神(xi_wx)/primary_selection_status=SINGLE_CANDIDATE/candidates=[火]/ge_yong_wx=水——fallback 自身选中火，但发射处 'wuxing': _ge_yong_wx or _w（V7.180）无条件用格神财水盖过喜神火。
- **方案二轮**：①GE_FALLBACK 发射改 _use_gy（仅 NOT_EVALUABLE 或同值时用格神）→ 021 火 ✓ 但 016 高太尉翻 MISS（ge 层 CZP 形态 xi=合煞神 vs ti=官，derive_ge_yong_wx=金 才是正用神）→ **回退发射改动**（恢复原 or _w）。②根修=derive_ge_yong_wx 财格分支：len(_he_dm)==1（财专向）时 gate if shape != '佩印': cat='财'——佩印形态不即裁，落入既有 V7.203 佩印终裁（无印财五合对/未合去→印；合去→财张耀曾 004）。
- **验证**：九案探针全 HIT（021 火/016 金回退生效/004 张耀曾 金 印被合去→用财/015 土 NO_BING 路径 shape≠佩印 不受影响）；replay **20/20**（021 入 CASES，KNOWN_CONFLICTS 收敛至仅 {018}）；六套件 85 passed（+021 锚+test_peiyin_cai_special_toward_still_uses_yin 三案断言 021 火/015 土/004 金，护栏≥20）；audit 40盘基线不变（取格 1/40 甲午己巳壬午壬寅+特格族 2；成败 2/40 乙未丁亥丙申辛卯、丙寅己亥丁卯辛亥+特格族 1）；全量 ziping 回归 16 failed/1905 passed 0 新增。
- **提交**：仅子平 4 文件（yongyao_resolve.py/ziping_pzzq_replay.py/test_ziping_yong_coverage.py/本审计文档）。V7.200 教训（016 翻 MISS）本轮验证前置，未重演。
