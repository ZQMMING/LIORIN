# 盲派引擎准确性审计（2026-11-05）

> 范围：`src/tongshu/engines/blind_bazi_engine.py` + 盲派测试族 + 真值层。
> 原则：只用原典/原著明文断语做真值；Golden v2 为引擎自证，不作真值。
> 命令：`python scripts/blind_truth_replay.py`（11 案全 PASS）、
> `pytest tests -k blind --continue-on-collection-errors`（203 passed / 3 skipped）。

## 一、结论

- 盲派此前"Golden 20 案通过"属**自证循环**：`cases/golden/blind_golden_set*.json` 的
  `expected_calculation` 只记录引擎自身 dump 的信号数量，`source` 字段自释「引擎实测」。
- 本轮建立**真值层** `cases/truth/blind_truth_cases.json`（11 案，全部带原文断语），
  逐案经 `BaziEngine → BlindBaziEngine` 真跑比对，**11/11 PASS**。
- 修 6 处规则缺陷（D1~D6），修前 11 案中 6 案残差；修后 0 残差。
- 回归：盲派测试族由 **4 failed / 199 passed** 变为 **0 failed / 203 passed / 3 skipped**
  （唯一 error 仍是子平线在途的 `tests/test_ziping_15_2_evidence_provenance.py` CITATION 导入）。

## 二、真值层（11 案）

| 案例 | 四柱 | 公历 | 期望 | 原文依据 |
|---|---|---|---|---|
| blind-001 | 壬子 辛亥 壬辰 丙午 | 1912-11-12 12:00 男 | wealth=DIRECTED_AND_ESTABLISHED | 案例1：辰库收水=财富聚拢、丙辛合取财、资本市场大鳄 |
| blind-002 | 丁未 癸卯 庚子 丁丑 | 2027-03-22 02:00 女 | official=DAMAGED | 案例2：子水伤官穿未土官库→官根受损 |
| blind-003 | 戊申 己未 庚申 辛巳 | 2028-08-03 10:00 男 | body=LU_UNDER_ATTACK | 案例3：禄被穿害 |
| blind-004 | 甲寅 丙子 己亥 戊辰 | 1974-12-24 08:00 男 | marriage=BROKEN | 案例4：官星投墓 |
| blind-008 | 乙巳 甲申 辛酉 乙未 | 2025-08-20 14:00 男 | official=ROBBED | 案例8：劫财合官→非我所有 |
| blind-009 | 癸丑 乙卯 戊戌 癸亥 | 1913-03-18 22:00 男 | wealth=DIRECTED_AND_ESTABLISHED | 案例9：双癸合戊，财来合我 |
| blind-012 | 丁亥 甲辰 戊辰 甲寅 | 1947-04-19 04:00 男 | zfj=ZHENG | 案例12：木火成势制亥官，大贵 |
| blind-d28 | 己巳 乙亥 壬申 丁未 | 1989-11-08 14:00 男 | zfj=FAN_JU | 9例对齐反证：左去官/右合财意向相反 |
| blind-1983 | 癸亥 壬戌 乙未 壬午 | 1983-11-03 12:00 男 | zfj=FAN_JU | 用户定稿锚点：制不净+未亥暗合追水忌 |
| blind-ch1-2 | 丙子 戊戌 丁丑 丁未 | 1876-11-05 14:00 女 | zfj=FAN_JU | ch1 例②：忌金水+丑合子水追忌 |
| blind-zhu | 戊辰 壬戌 丁丑 丁未 | 1868-10-18 14:00 男 | zfj=ZHENG | 朱元璋造：合官+明克去官同向 |

四柱→公历由 sxtwl 求解（年柱取当年 7/1 年干支，日时按五鼠遁/支中间小时），回放时逐案复核四柱一致（`pillars_match`）。

## 三、缺陷与修正

### D1 正反局 R1：日支追忌被"李嘉诚豁免"误放行（`_resolve_zheng_fan_ju` ~:2870）
- 现象：1983 癸亥 壬戌 乙未 壬午 判 ZHENG（用户定稿=FAN_JU）。
- 根因：豁免条件只判「日支在本党 + 制不净 ZHI_BU_JING」，未判忌神是否真的在局中成党；
  未亥暗合追来的 WATER 忌仅一字，即被豁免。
- 修：新增 `_ji_dang`（忌神天干≥2 不含日主自身，或地支≥2）→ 成党则豁免失效，
  理由串「R1日支追忌且忌神成党」。李嘉诚 戊辰 己未 庚午 壬午（忌仅壬 1 干、无金水支）仍 ZHENG。

### D2 定势：金水湿势缺"金党"门控（`_resolve_shi_direction` ~:4889）
- 现象：蒋介石 丁亥 甲辰 戊辰 甲寅 定势为 METAL_WATER→FIRE_EARTH，判 FAN_JU；
  原书为木火/火土成势制亥水官星、大贵=ZHENG。
- 根因：湿土（辰丑）被直接算入金水党，全盘无金时仍成立。
- 修：`_jin_party = metal + stem_count["METAL"]`，要求 `mw_party>=3 and metal_water>=1 and _jin_party>=1`。
  修后该盘势为 WOOD_FIRE→EARTH_METAL，ZHENG。

### D3 正反局 R2：合财与合官未区分方向（~:2634）
- 现象：D28 己巳 乙亥 壬申 丁未 判 ZHENG（反证锚点=FAN_JU）。
- 根因：日主合（合财=求财）与天干明克去官（去官=得权）方向相同即放行，
  未分辨「求财 vs 去官」两条不同意向。
- 修：`if day_he_methods and (zhi_guan_eff or zhi_tiangan):` + `if he_has_cai:`（只认合财），
  理由「R2日主做功与日支做功相反: 日主合正财(求财) vs 原局伤官制官(去除正官)」；
  删除已失效的 `zhi_tiangan_eff` 块。朱元璋造（合官+明克去官）仍 ZHENG。

### D4 官域：伤官穿官库未判损官（`officer_damaged` 上游 ~:3919）
- 现象：c2 丁未 癸卯 庚子 丁丑 判 official=CONTROLLED_AND_CLEAN（原书=伤官损官）。
- 根因：`穿制正官 EFFECTIVE`（子穿未=穿官库）被判"去官得权"，未回到"官根受损"这一原书结论。
- 修：工作时表出现 `穿制正官/穿制七杀` 且 EFFECTIVE 且 detail 含「伤官」→ `officer_damaged=True`。
  修后 c2 = DAMAGED（`control_completeness` 仍 CLEAN，因"制尽"与"官根受损"是两个口径，此处按原书取损官）。

### D5 财富：日主合财被判"合绊失性"（~:1108）
- 现象：c9 癸丑 乙卯 戊戌 癸亥 判 SUBSTITUTED_CANDIDATE（原书=双癸合戊、财来合我）。
- 根因：合功统一口径「紧贴+有根气=合绊 INEFFECTIVE」，未区分合官（官被绊走）与合财（财入我手）。
- 修：`_zhi_he_cai = ti_stem == day_master and yong_tg in GROUP_CAI` → EFFECTIVE
  「财来合我=合财入手」；并在财富分支前加 `_zhi_he_cai_eff` 优先于换象当财（真财强于代财）。
  修后 c9 = DIRECTED_AND_ESTABLISHED。

### D6 财富：闭库聚财未计入取财、比劫夺财未让位于闭库（~:3691）
- 现象：c1 壬子 辛亥 壬辰 丙午 判 DIRECTED_WITH_ROBBERY（原书=闭库收财、巨富）。
- 根因：①取财功法只认「财/冲开/冲库」字样，`墓库收物` 被排除；②`比劫制财 NEGATIVE` 一律
  算夺财，但财已入主位库时比劫在外夺不到（原书「闭库=财富聚拢，冲则破库散财」）。
- 修：①`wealth_positive` 纳 `墓库收物`（须 EFFECTIVE 且 detail 含 `[主位]`）；
  ②`_muku_ju_cai` 成立时 `wealth_robbed=False`。
  修后 c1 = DIRECTED_AND_ESTABLISHED。

### D7 婚姻：好婚三式③判据过宽（~:3493）
- 现象：1980 庚申 壬午 丙寅 癸巳（宫 CLASHED_AND_PUNISHED）判 marriage=HARMONIOUS。
- 根因：①`ZHIGONG_KWS` 16 个关键词含「印化官杀/印制食伤/比劫制财/官杀制比劫/食伤泄秀」等
  **并非「配偶星制宫忌神」**的项；②借 `control_completeness=CLEAN`（官杀制尽口径）当「制住宫忌神」代理；
  ③不要求作用落在日支（宫）。
- 修：三项硬门控——(a) `palace_state == "STABLE"`（宫受损则「制之不住，反为坏婚姻」）；
  (b) 有本性别配偶星（男财/女官杀）参与的 EFFECTIVE 条目（解析 detail 内十神标记）；
  (c) 作用点落在日支藏干。修后 1980 婚姻 = BROKEN（与 `zhenfu_risk=DIVORCE` 一致，消除同盘自相矛盾）。

## 四、测试口径修正（非改金凑绿）

- `tests/test_blind_rule_compliance.py::test_06_gong_shen_roles`：旧白名单只放行
  WORKING/TARGET/UNDETERMINED，与 `GongShenRole` 枚举（含 ㊻s88 显式补的 IDLE）自相矛盾
  → 改为「取值必须属于枚举成员」。
- `tests/test_blind_rules/test_rule_graph.py`：`Path("backend/data/rules")` 是旧仓路径（加载 0 条）
  → 改为 `<repo>/data/rules`（140 个规则文件）。
- `tests/test_blind_themes.py::test_wealth_directed_established`：旧值 DIRECTED_AND_ESTABLISHED
  来自 V3.4.2 引擎自证 dump；D5/D6 修后本盘（主位丙=日主之根制财=身制财、非他字比劫夺财）
  为 DIRECTED_PARTIAL（rob.sted=False，工作效能 SMALL 压档）。已改断言并在测试内注明原因。

## 五、待裁决 / 未尽

1. `blind-006`（庚寅 戊寅 甲子 丙寅，陈济棠造）：四柱**自洽**（甲日寅时=丙寅 合五鼠遁），
   实际解在 1890-02-12 寅时（1890 庚寅年戊寅月内 2/12 为甲子日）；扫描器下界 1900 故未解。
   原书断语「包局得权」映射不到现有枚举 → 仍暂不入真值层，待新增官贵层次口径后补入。
2. `blind-013`（甲辰 庚午 辛未 戊辰）：辛日辰时应为**壬辰**（丙辛日戊子起），时柱 戊辰 与该日干
   五鼠遁不合 → 原著转录矛盾，不改资产。
3. `blind-014`（乙丑 辛巳 丁亥 辛亥）：1925/1985 两个乙丑年的辛巳月内**无丁亥日**
   （1925 巳月庚寅起至庚申、1985 甲辰起至乙亥）→ 四柱不可共存，疑转录错字，不改资产。
4. `blind-012` 原书"大贵"还含官贵层次，本轮只校 `zheng_fan_ju`；官域层次（CONTROLLED_PARTIAL vs 贵格）
   仍无原文明文锚点。
5. 1980 案例无原典断语 → 仅作回归探针，不进真值层。
6. `cases/golden/blind_golden_set*.json` 的 `expected_calculation` 应改为「引擎签名快照」并重命名，
   避免继续被当成真值（未改资产，等裁决）。
