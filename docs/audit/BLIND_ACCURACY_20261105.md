# 盲派引擎准确性审计（2026-11-05）

> 范围：`src/tongshu/engines/blind_bazi_engine.py` + `blind_yingqi.py` + 盲派测试族 + 真值层。
> 原则：只用原典/原著明文断语做真值；Golden v2 为引擎自证，不作真值。
> 命令：`python scripts/blind_truth_replay.py`（13 案全 PASS）、
> `python scripts/blind_event_replay.py`（应期 4 案全 PASS）、
> `pytest tests -k blind --continue-on-collection-errors`（219 passed / 3 skipped）。

## 一、结论

- 盲派此前"Golden 20 案通过"属**自证循环**：`cases/golden/blind_golden_set*.json` 的
  `expected_calculation` 只记录引擎自身 dump 的信号数量，`source` 字段自释「引擎实测」。
- 本轮建立**结构真值层** `cases/truth/blind_truth_cases.json`（13 案，全部带原文断语），
  逐案经 `BaziEngine → BlindBaziEngine` 真跑比对，**13/13 PASS**。
- 建立**应期真值层** `cases/truth/blind_event_cases.json`（4 案，事件级：年 + 领域 + 事件主题 +
  吉凶方向 + 虚岁），经 `blind_yingqi.analyze` 真跑，**4/4 PASS**。
- 修 9 处规则缺陷（D1~D9），修前 11 案中 6 案残差；修后 0 残差。
- 回归：盲派测试族由 **4 failed / 199 passed** 变为 **0 failed / 219 passed / 3 skipped**
  （唯一 error 仍是子平线在途的 `tests/test_ziping_15_2_evidence_provenance.py` CITATION 导入）。

## 二、真值层（结构级，13 案）

| 案例 | 四柱 | 公历 | 期望 | 原文依据 |
|---|---|---|---|---|
| blind-001 | 壬子 辛亥 壬辰 丙午 | 1912-11-12 12:00 男 | wealth=DIRECTED_AND_ESTABLISHED | 案例1：辰库收水=财富聚拢、丙辛合取财、资本市场大鳄 |
| blind-002 | 丁未 癸卯 庚子 丁丑 | 2027-03-22 02:00 女 | official=DAMAGED | 案例2：子水伤官穿未土官库→官根受损 |
| blind-003 | 戊申 己未 庚申 辛巳 | 2028-08-03 10:00 男 | body=LU_UNDER_ATTACK | 案例3：禄被穿害 |
| blind-004 | 甲寅 丙子 己亥 戊辰 | 1974-12-24 08:00 男 | marriage=BROKEN | 案例4：官星投墓 |
| blind-006 | 庚寅 戊寅 甲子 丙寅 | 1890-02-12 04:00 男 | zfj=ZHENG、official=CONTROLLED_AND_CLEAN | 案例6：包局主贵、火局制子水、官至师长 |
| blind-007 | 戊申 己未 癸巳 己未 | 1968-07-22 14:00 男 | official=CONTROLLED_AND_CLEAN | 案例7：巳火合制申金（印带官帽）→财制印，制得干净→大贵 |
| blind-008 | 乙巳 甲申 辛酉 乙未 | 2025-08-20 14:00 男 | official=ROBBED | 案例8：劫财合官→非我所有 |
| blind-009 | 癸丑 乙卯 戊戌 癸亥 | 1913-03-18 22:00 男 | wealth=DIRECTED_AND_ESTABLISHED | 案例9：双癸合戊，财来合我 |
| blind-012 | 丁亥 甲辰 戊辰 甲寅 | 1947-04-19 04:00 男 | zfj=ZHENG | 案例12：木火成势制亥官，大贵 |
| blind-d28 | 己巳 乙亥 壬申 丁未 | 1989-11-08 14:00 男 | zfj=FAN_JU | 9例对齐反证：左去官/右合财意向相反 |
| blind-1983 | 癸亥 壬戌 乙未 壬午 | 1983-11-03 12:00 男 | zfj=FAN_JU | 用户定稿锚点：制不净+未亥暗合追水忌 |
| blind-ch1-2 | 丙子 戊戌 丁丑 丁未 | 1876-11-05 14:00 女 | zfj=FAN_JU | ch1 例②：忌金水+丑合子水追忌 |
| blind-zhu | 戊辰 壬戌 丁丑 丁未 | 1868-10-18 14:00 男 | zfj=ZHENG | 朱元璋造：合官+明克去官同向 |

四柱→公历由 sxtwl 求解（年柱取当年 7/1 年干支，日时按五鼠遁/支中间小时），回放时逐案复核四柱一致（`pillars_match`）。

## 二之二、应期真值层（事件级，4 案）

| 事件 | 四柱 | 公历 | 应期 | 期望 | 原文依据 |
|---|---|---|---|---|---|
| e001 | 癸丑 乙卯 戊戌 癸亥 | 1913-03-18 22:00 男 | 1958 戊戌 | 财富/财富事件/POSITIVE | 案例9：庚戌大运戌土伏吟，双癸合戊激活，资产几何级增长 |
| e002 | 戊申 壬戌 甲子 丙寅 | 1968-10-21 04:00 女 | 1992 壬申 | 婚姻/婚姻事件/POSITIVE | 案例10：夫星申出现拱入夫宫（申子合局） |
| e003 | 同 e002 | — | 1996 丙子 | 婚姻/婚姻事件/NEGATIVE | 案例10：己未运之未运未穿子，夫宫被穿 |
| e004 | 乙未 乙酉 丙戌 己丑 | 1955-09-22 02:00 女 | 1970 庚戌（虚岁 16） | 长辈家宅/长辈家宅事件/NEGATIVE | 案例15：16 岁庚戌年死母（未戌刑、戌穿酉） |

- e001 的应期年有 60 甲子歧义：原书"2008 戊子年"与 1913 年生（95 岁）不可能，而 1958 亦为戊戌年、
  虚岁 45 正落庚戌大运（癸丑阴年男逆行第 5 运）→ 判原书年份为 60 甲子笔误，真值取 1958；`data_issue` 已记录。
- e004 年龄口径：原书"16 岁"是**虚岁**（1970 周岁 15），引擎 `nominal_age` 已对齐（`age` 仍周岁，两者并存）。
- 回放：`python scripts/blind_event_replay.py` 断言 year + domain + direction + event_topic，另核 `nominal_age`。

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

### D8 官域：财制印「合克」整块丢失 + 合制即制净（`_analyze_zuogong` ~:1237 / `_resolve_official_structure`）
- 现象：案例7（戊申 己未 癸巳 己未）原书判「财制印格·大贵」，引擎 `official_state=CONTROLLED_PARTIAL`、
  `财制印` 归因 INEFFECTIVE。
- 根因：①巳申六合五行相克时，关系层先把 `relation` 归为 `ke_yong_ti`，财制印只留「月未丁财制年申庚印」
  的宾位版本；②⑤ 分支主位 detail 不带 `[主位]` 标记，抢注升级逻辑 `_cur_is_main="[主位]" in detail`
  不认主 → 主位版本被宾位 INEFFECTIVE 覆盖。
- 修：⑤ 与镜像分支主位时写 `[主位]`；新增 `ke_yong_ti`(用=财/体=印) 的「合制」识别
  （`BRANCH_LIUHE` 互合 → detail `[合制]印被财合制=财制印成立`），并置 `result.cai_zhi_yin_hezhi`；
  官域 completeness 追加 `_he_zhi_qing = cai_zhi_yin_hezhi`（原书"财星主动制合印星且制得干净"——
  合住即制住，不走"目标支孤立"判据）；`财制印` 纳入制官关键词。
- 修后：案例7 `official_state=CONTROLLED_AND_CLEAN`；案例8 另见 D9。

### D9 官域：ROBBED 被「别处制法」错误撤销（`_resolve_official_structure` ~:4040）
- 现象：修 D8 后案例8（乙巳 甲申 辛酉 乙未，仓库保管员）由 ROBBED 变 CONTROLLED_PARTIAL。
- 根因：`_other_guan_zhi_s16` 只要局中有财制印/食伤制杀等 EFF 就撤销"官被劫财合走"；
  但本盘财制印作用于**主位偏印**，与已被劫走的巳中丙官无关。
- 修：局中确有 `劫财合官` NEGATIVE（官本体被合走，原书"非我所有"）时，ROBBED 优先，
  别处制法不能改判得权。
- 修后：案例8 恢复 ROBBED；真值 13/13、盲派测试族 219 passed。

### D10 应期：六亲星引动只认冲/穿 + 周岁/虚岁混用（`blind_yingqi.py` ~:1037）
- 现象：案例15「16 岁庚戌年死母（未戌刑、戌穿酉）」无任何父母事件输出。
- 根因：①父/母星各只取单个十神（`FATHER_STAR=偏财`、`MOTHER_STAR=正印`，注释却写"正偏财为父"）；
  ②引动机制只有冲/穿，漏**三刑/自刑**；③年龄只有周岁（`flow_year-birth_year`），原书"16 岁"是虚岁。
- 修：`FATHER_STARS=("偏财","正财")`、`MOTHER_STARS=("正印","偏印")`；新增 `_xing_with`（三刑同组/自刑/子卯）
  与 `_kinship_trigger`（冲/穿/刑统一出 mech）；`YingqiResult` 增 `nominal_age`（虚岁）并保留 `age`（周岁）；
  事件主题修正（`parent_star→长辈家宅事件`、`muku_*` 按 domain 映射、`spouse_star` 区分"合身/现身引动"）。
- 修后：1970 庚戌输出父星(穿酉)+母星(刑未) 两条 NEGATIVE 长辈家宅事件，虚岁 16。

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

1. `blind-006` 已补入真值层（四柱自洽，解在 1890-02-12 寅时；包局得权在官域表现为
   `CONTROLLED_AND_CLEAN` + `work_level=LARGE_NOBLE`，"官贵层次"仍无逐级中文枚举，本轮只锚定状态值）。
2. `blind-013`（甲辰 庚午 辛未 戊辰）：辛日辰时应为**壬辰**（丙辛日戊子起），时柱 戊辰 与该日干
   五鼠遁不合 → 原著转录矛盾，不改资产。
3. `blind-014`（乙丑 辛巳 丁亥 辛亥）：1865-05-17 22:00 唯一可解（原书正文自相矛盾说"辛酉日主"）；
   `scripts/blind_pillar_solver.py` 扫描得该解，暂未入真值（应期线索"丙辰年丧父"需另核）。
4. `blind-005`（丁亥 癸丑 己未 癸酉）：丁亥年（1887/1947/2007）的己未日只落 2/4/6/8/10/12 月，
   **丑月无己未日** → 四柱不可共存，不入真值。
5. `blind-012` 原书"大贵"还含官贵层次，本轮只校 `zheng_fan_ju`；官域层次（CONTROLLED_PARTIAL vs 贵格）
   现以 `cai_zhi_yin_hezhi` + completeness 表达，其余贵格分层仍无原文明文锚点。
6. 1980 案例无原典断语 → 仅作回归探针，不进真值层（其婚姻/财域断言仅作结构一致性回归）。
7. `cases/golden/blind_golden_set*.json` 已按裁决改名重录（2026-11-05）：
   旧两文件（v1 未使用、v2 被兼作"验证"）删除，改为 `cases/golden/blind_engine_snapshot.json`
   （`metadata.kind = engine_snapshot`，逐案 `snapshot` 字段=信号数/强度区间/结构字段/正反局），
   测试改为 `tests/test_blind_snapshot.py`（含"快照不得使用 expected_calculation"防回归断言），
   重录器 `scripts/blind_snapshot_record.py`（`--check` 只比对不写回）；`golden_replay.py` 盲派路径同步。
   `book_claim`（原 `human_verified_result`）保留，但只作为书籍章节的一句话标注，不可机读、不作断言来源。
