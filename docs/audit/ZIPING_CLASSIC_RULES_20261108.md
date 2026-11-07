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

## 六、2026-11-08 裁决：一切基于原典为优先级（用户指令）

用户裁决「一切基于原典为优先级」后，取格口径定为原典透干优先：

- FOUNDATION.MONTH_COMMAND.YUE_LING_GE_JU.001「格之真者，月支之神，透于天干也」
- .005「月令所藏不一，而用神遂有变化」 / .006「假使寅月为提，不透甲而透丙」
- STRUCTURE.GE_JU.CHENG_BAI.002「四季月…取土为格；建禄月劫羊刃亦看月令中人元透干者取格」

落地（engines/common/l0_fact_builder.py）：

1. 新增 ge_stem / ge_element / ge_ten_god / ge_rule_ref 事实；
2. 取格顺序：四季月非土日主取本气土（土日主看人元透干）→ 本气为比劫(禄/刃)时格名由禄刃立 → 否则月支藏干中第一个透干者（排除比劫透），皆不透取本气；
3. shishen_entry / qisha_entry / shangguan_entry 的 is_entry/type 改按取格十神 ge_god；
4. engines/common/ge_jie_layer.py 格局分支选择器 mqi_god 优先读 ge_ten_god。

对账结果（40 随机盘）：取格不一致 12/40 → **8/40**；成败不一致 27/40 → 28/40（口径差异为主）。

回归：pytest tests -k ziping --ignore=tests/test_ziping_15_2_evidence_provenance.py → **1169 passed / 13 failed**。
其中 4 项为 GPT 在途 	ests/test_ziping_relation_presence.py；9 项为 GPT 在途测试中按「本气立格」固化的期望
（	ests/test_ziping_entry_validation.py 7 项、	ests/test_ziping_wealth_sha_templates.py 2 项），
按原典透干口径应改为对应格名（如 庚午丙午甲子己卯 甲日午月本气丁伤官、己土财透 → 原典财格，旧测试断言伤官格）。
