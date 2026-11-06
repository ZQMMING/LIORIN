# 河洛引擎真值层与解层映射核验（2026-11-06）

> 本文只记录**本轮新增的独立证据**。算层三源互证的既有工作见 `data/heluo/算法原文对照核证表.md`（15.1）与 `docs/audit/HELUO_ENGINE_AUDIT_20260909.md`。

## 一、结论

| 项 | 结果 | 证据 |
|---|---|---|
| 算层真值回放（原典假令 + 三个案例） | **4/4 PASS** | `scripts/heluo_truth_replay.py`，`tests/test_heluo_truth.py` |
| 卦辞映射完整性（64 卦） | **64/64 逐字一致** | `tests/test_heluo_guajie_mapping.py::test_gua_ci_verbatim_for_all_64` |
| 爻辞/小象映射完整性（384 爻） | **384/384 逐字一致，0 缺失** | `tests/test_heluo_guajie_mapping.py::test_yao_ci_verbatim_for_all_384` |
| 原典断语保全（1088 条） | **1088/1088 全部出现在叶/不叶/岁运三栏，0 丢失** | `test_duans_preserved_without_truncation` |
| 精义/释义覆盖（64 卦） | 64/64 齐备 | `test_gua_ci_jingyi_covers_all_64` |
| 卷十参评（金锁银匙歌）起数三例 | **2542 / 2942 / 3347 逐字一致** | `tests/test_heluo_canping_truth.py` |
| 全族回归 | **630 passed**（`-k "heluo or meihua"`，1 error 为子平线 CITATION，pre-existing） | pytest |
| 结构不变式扫描 | **200 盘 0 问题**（先天六爻/元堂/后天爻变/结构卦名/化工/流年/解层九键） | `scripts/heluo_invariant_scan.py`，`tests/test_heluo_invariant_scan.py` |
| 节候卦（二十四节气 × 七十二候） | **72/72 候名按序命中原文，24/24 节候卦由首候派生，八节卦 24/24 与原典首句一致** | `tests/test_heluo_jiehhou_yuanwen.py`，`tests/heluo/test_h11_jiehhou.py` |
| 化工卦（H6） | **12 月支映射与原典「冬至→惊蛰/春分→芒种/夏至→白露/秋分→大雪」四句一致，三层判据（正体·互体·纳音）+ 四季月坤艮土旺均落地，25 tests** | `tests/heluo/test_h6_huagong_yuanwen.py` |

## 二、真值层（`cases/truth/heluo_truth_cases.json`）

真值层与盲派 `blind_truth_cases.json` 同构：每案带 `source` + `verbatim` 原文摘录，
断言只取**原文明示**的字段，不作引擎自证。

| case_id | 案例 | 天数/地数 | 归一 | 先天卦 | 元堂 | 后天卦 | 出处 |
|---|---|---|---|---|---|---|---|
| heluo-001 | 绍兴四年 甲寅 甲戌 己卯 壬申 阳男 | 29 / 48 | 4 / 8 | 风山渐 | （原文明示未含，不纳入断言） | — | 核证表 15.1 #2（逐字最强互证） |
| heluo-002 | 1980 庚申 壬午 丙寅 癸巳 男 | 29 / 32 | 4 / 2 | 风地观 | 六二（index 1） | 水风井 | 核证表 9.1/9.2 |
| heluo-003 | 1983 癸亥 壬戌 乙未 壬午 阴男 | 18 / 44 | 8 / 4 | 风山渐 | 初六（index 0） | 火风鼎 | 核证表 9.1/9.2 |
| heluo-004 | 纪晓岚 甲辰 辛未 丙戌 甲午 男 午时 1724 | 22 / 56 | 2 / 6 | 地天泰 | 六四（index 3） | 天雷无妄 | `canonical.py` GOLDEN_CASES + 核证表 |

回放命令：

```powershell
$env:PYTHONPATH='D:\shuntian\src'
python scripts/heluo_truth_replay.py            # 4/4 PASS，退出码 0
python scripts/heluo_truth_replay.py --filter 1980
python scripts/heluo_truth_replay.py --dump heluo-002
```

## 三、解层映射核验（新增覆盖）

`data/heluo/guajie_data.json` 是本仓的《河洛真数》卦解原典结构化资产（64 卦 × 卦辞 + 卦象/卦气/邵曰 + 6 爻 ci/xiang/yi/duans）。
本轮把「原典文本 → 引擎字段」的映射做成穷举校验，覆盖：

- 64 卦 `gua_ci` 逐字（`load_guajie_data().gua_ci`）
- 384 爻 `ci` + `xiang` 逐字（`query_yao_duan(卦, 爻位)`）
- 1088 条 `duans` 全部保全（loader 用 `_split_duans` 归入 `ye`/`buye`/`suiyun` 三栏，属**分类而非删改**，校验方式为逐条子串命中）
- 64 卦 精义/释义（`guajie_jingyi.json`）齐备

结论：**映射层无丢字、无截断、无改写**。断法本身（叶/不叶、死断诸法、贵贱等）不在本轮断言范围，另见 `guajie.py` 与 H16 独立验证。

## 四、卷十参评（金锁银匙歌）原典起数

`canping.qishu(日支, 时支, 纳音五行, 顺/逆)` 三例与原典数字逐字比对：

| 例 | 条件 | 起数 | 原典 | 结果 |
|---|---|---|---|---|
| 1 | 戌日寅时 乙卯（纳音水）顺 | 2000+500+14+27+1 | 二千五百四十二 = 2542 | ✅ |
| 2 | 戌日寅时 乙卯（水）逆 | 2000+900+14+27+1 | 二千九百四十二 = 2942 | ✅ |
| 3 | 申日申时 戊午（纳音火） | 2000+1300+18+27+2 | 三千三百四十七 = 3347 | ✅ |

诗断库（`data/heluo/canping/raw_shici_jintu_448.json` 等）中三例首句定位也一致：
掌中秋月扇 → p29 丑酉列；玉壺無別物 → p34 辰宾列；道是無形光 → p53 未未列。

## 五、登记的数据问题（未入真值层）

| 案例 | 问题 | 处置 |
|---|---|---|
| 卢某 甲辰 戊辰 丁酉 癸卯 男 | 核证表同时记「天30地40」与「卢某比初六／比→解」，但按同一张表的取数/寄宫/相荡规则推导应为：天30除25余5（中元阳男寄艮→艮）、地40除30余10（遇十不用取1→坎），阳男天卦在上 → **山水蒙**；引擎实测亦为山水蒙（元堂上九）。「比」（上坎下坤）与该表自身规则不合。 | 判为核证表转录可疑（或该案例原始参数不同），**不入真值层**，待回原书影印件复核。 |
| 观 卦头「纳甲是」 | 原文写「乙未、乙巳、乙卯、辛巳、辛卯、辛丑」，按巽外卦应为「辛未、辛巳、辛卯」→ 辛丑 系 辛未 之讹 | 引擎按京房表计算得 6 条正解；原文异文登记在测试 `_NAJIA_TEXT_VARIANTS`，不改原典资产 |
| 损 卦头「纳甲是」 | 原文写「丁巳、丁卯、丁丑、丙**戊**、丙子、丙寅」，戊非地支 → 丙戌 之讹 | 同上（引擎按京房表得 丙戌） |

## 六、复现命令

```powershell
$env:PYTHONPATH='D:\shuntian\src'
$env:PYTHONIOENCODING='utf-8'
python -m pytest tests/test_heluo_truth.py tests/test_heluo_guajie_mapping.py tests/test_heluo_canping_truth.py -q   # 21 passed
python -m pytest tests -k "heluo or meihua" --continue-on-collection-errors -q                                      # 630 passed / 1 pre-existing error
python scripts/heluo_truth_replay.py                                                                               # 4/4 PASS
```

## 七、缺陷 D-006 / D-007（2026-11-06 修复）

### D-006 卦气月与纳甲解析不完整（解层断法入口被污染）

`guajie.py::_parse_gua_header` 两个解析缺陷：

1. **卦气月漏 9 卦**（坤/小畜/贲/复/坎/离/巽/兑/节 → `gua_qi_month=None`）。
   原典写法有三种：`卦气属四月`、`卦气**在**十月`（坤）、`八纯卦世在上**属**十月`（坎）、
   `坤宫三世卦**属**七月`（比/泰/否）。旧正则只认「(卦气|宫)…属X月」，
   对「在X月」「卦…在…属X月」均不匹配。
2. **纳甲只剩内卦三爻**（比/小畜等）。旧解析在「借用」处 `break`，
   而原典部分卦把外卦三爻写进借用句
   （比：「纳甲是乙未乙巳乙卯，借用癸未…**戊申戊戌戊子**」），
   于是 6 条纳甲只取到 3 条 → `judge_ye_buye` 的「纳甲本命」必错。

修复：月份正则容忍「属|在」且允许中间夹「世在上」等修饰；纳甲改为按
`COMPOUND_GUA`（卦名→上下卦）+ 京房纳甲表**计算六爻**（`hexagram_najia()`），
原文解析结果保留为 `najia_borrow` 作交叉校验（64 卦仅观/损 两处原文讹字例外，已登记）。
校验：64/64 卦有卦气月、64/64 卦纳甲恰 6 条且与京房表一致、原文并集覆盖计算值
（`tests/test_heluo_guajie_mapping.py` 新增 4 条断言）。

### D-007 命卦叶/不叶缺失 + 生月未知被当阳月

- 此前只对**流年卦**判 `judge_ye_buye`，命卦本身不判；
  而原典「如生于四月及纳甲本命者，多属富贵人也」正是命卦级断法。
  → `GuaJieResult` 新增 `benming_ye_buye` 并接入 `compose_guajie` / `to_dict`。
- `bbuild_guajie_from_result` 在无四柱时用 `birth_month or 1`，把「未知生月」静默当正月，
  数凶判据的阳月分支因此会把「未知」判成「阳月 → 数凶」。
  → 改为 `birth_month or 0`，`judge_shu_xiong` 对 `<=0` 显式记「生月未知 → 阳月判据跳过」。

纪晓岚实测（甲辰 辛未 丙戌 甲午 男 午时）：命卦泰（卦气正月），生月六月 → 月不合、
年干支甲辰在纳甲 → **半叶**；数凶 `以弱敌强（天22/56）+ 生月6月（阳月）`。

### D-008 得时/失时月窗（叶/不叶第三判据）只识别出 1 卦

- 原典「及时/得时/失时」是叶不叶的第三个判据（如乾「二月已后、八月以前及时」，
  兑「生于秋则及时」，渐「在冬则及时」），旧实现只有一条正则，64 卦里仅 **乾** 能匹配。
- 重写为分句解析：`_parse_de_shi_windows(lines)` 逐行按 `(?!不)及时|(?!不)得时|失时|非时`
  切段，`_analysis_segment` 取标记前从句（「X月已后，Y月以前及时」配对、
  「九、十、十二、一月为失时」顿号枚举左补、不并入含另一断语的前句），
  `_month_tokens` 要求数字后 10 字内有「月」以免把爻位「九五」当月份，
  `_expand_range` 支持 9→1 跨年回绕。
- 结果：**19 卦**解析出月窗（乾/屯/豫/随/复/无妄/大壮/归妹/丰/小过 得时 2-8；
  兑/大有 得时 7-9；渐 得时 10-12；离 得时 4-6；颐 得时 2-7、失时 9-12；
  恒 得时 2-8、失时 9-12；噬嗑/解 失时 9-1 等），无妄原文「九、十、十二、一月」确实漏十一月，
  保留原样不做补写。
- 叶/不叶因此改为「卦气月 / 得时月窗 / 纳甲」三判据；新增
  `tests/test_heluo_guajie_mapping.py::test_de_shi_windows_parsed_from_book_text`、
  `test_ye_buye_uses_de_shi_window`。
- 回归：`pytest tests -k "heluo or meihua"` → **542 passed / 1 error**（error 为子平线
  `test_ziping_15_2_evidence_provenance.py` CITATION，pre-existing）。

### D-009 数格只认 5 格，且「数有余逢阳月」方向与原典相反

- 原典《起例卷之中·数论》共 14 格：天数（不足/得中/太过/孤阳不偶/孤阳自偶/阳数偏少/
  以强伏弱）、地数（至弱/不足/得中/太过/孤阴背阳/孤阴向阳/阴数偏少）、跨二数
  （以弱敌强/安和自宁）。旧 `judge_shu_xiong` 只有「孤阳不偶/孤阴背阳/以弱敌强/
  太过有余/安和」5 格，且把「数有余」一律按「阳月 → 数凶」处理，与原典两处相反：
  以弱敌强「阴月令逢之尚庶几，阳月令逢之必主灭顶之凶」、以强伏弱「值阳月令不妨，
  逢阴月令颇有恃势致凶之象」。
- 重写：新增 `_shu_patterns(tian, di)` 逐格判定并返回**并存数格列表**（`ShuXiongResult`
  新增 `patterns` 字段，`pattern` 保留为主格）+ `_SHU_VERDICT` 14 格原典方针表，
  按月令逐格定凶：以弱敌强阳月凶、以强伏弱阴月凶、阳数偏少阳月孤睽、阴数偏少阴月百事煎、
  天数不足秋冬合时、地数太过十月立冬后不害等。
- 实测：22/56 → 以弱敌强+地数太过（阳月数凶，阴月以弱敌强不记凶）；30/10 → 以强伏弱+
  地数至弱（阳月「不妨」）；25/30 → 安和自宁（不记凶）。
- 新增测试 `test_shu_patterns_cover_yuan_dian_taxonomy`（14 格逐格）、
  `test_shu_xiong_month_direction_follows_book`（阳月/阴月方向）。
- 回归：**544 passed / 1 error**（同上 pre-existing）；`scripts/heluo_truth_replay.py` 4/4。

### D-010 贵命十体③④⑥⑦ 判据窄于原典

- **④得时**：原文「如春震木、夏离火、秋兑金、冬坎水之类。**又如正月得泰卦、九月得剥卦
  之类皆是**」——engine 只实现四季卦，未实现「生月 = 卦气月」。→ 接入
  `load_guajie_data()[name].gua_qi_month`，生月与卦气月相同亦记得时。
- **⑦得体**：原文「戊己土命得坤艮，巳午火命得离，**或土命得离火，火命得震木，有生气
  皆为得体**」——engine 只认同五行卦（木巽/火离/土坤艮），漏「生我之卦」（有生气）。
  → `_DETI_BY_WUMING` 改为「同五行之卦 ∪ 生我五行之卦」派生（土命: 坤艮+离；火命:
  离+震巽；金命: 乾兑+坤艮；水命: 坎+乾兑；木命: 震巽+坎）。
- **⑥顺时**：原文「谓天地二数多寡**与时偕行**」——engine 只有正月/九月两例。
  → `_shunshi_want(mon)` 按半年推广：阳月（1-6 月）宜天多、阴月（7-12 月）宜地多。
- 贱命十体逐条取反同步继承（⑦不得体、⑥数逆时、④不得时均按新判据取反）。
- 实测：泰命六五 寅月（泰卦气正月）→ 得 7 体「乡监侍从」（原 6 体「如通命」）；
  庚金命得剥（艮坤土）→ ⑦得体成立，贱体由 7 降为 6。
- 新增测试 `test_gui_ming_deshi_accepts_gua_qi_month`、
  `test_gui_ming_deti_includes_sheng_wo_trigram`、
  `test_gui_ming_shunshi_generalized_by_half_year`；两条既有 kuozhan 断言按原典修正。
- 回归：**547 passed / 1 error**（pre-existing）。

### D-011 得时月窗只认「及时/失时」字样，漏「福力重/浅」「余月」「春夏福力为重」写法

- 原典同一断语有多种写法：益「二月至八月生者，**福力重**，余月**非时**，福力浅」、
  复「二月至八月生者及时，**余月福力浅**」、丰「二月生至八月为及时，为富贵福力重，
  **余月福力浅**」、巽「在**春夏**长养发生**福力为重**，**秋冬**肃杀击搏**福力轻**」。
  → 旧解析只认「及时/得时/失时/非时」四个标记，上述 4 卦全部漏判。
- 修：①得时标记扩为 `及时|得时|福力(至重|深重|为重|重|深)`，失时扩为
  `失时|非时|福力(轻|浅)`；②「余月/其余月/其他月/余者」失时 = 全年减去得时月；
  ③季节式支持多季并集（巽=春夏得时 / 秋冬失时）。
- **邵曰污染**：无妄邵曰「更喜**春夏得时**，秋冬不利」是泛论文气，若按整段文本解析
  会把得时扩成 1-6 月；修法=逐行解析并跳过 `邵曰` 开头的断语行（大有「若秋生得时」
  同属邵曰，故 大有 月窗改为不参与硬判，登记为邵曰级）。
- 覆盖数：1 卦（旧）→ **20 卦**（新增 益/巽/丰/复/豫/随/解 的失时余月及巽的季节窗）。
- 新增断言：`test_de_shi_windows_parsed_from_book_text` 覆盖 20 卦 + 复/益/巽/无妄
  逐条月集合。回归 **547 passed / 1 error**、真值 4/4。

### D-012 结构不变式无护栏（缺自动扫描）

- 现象：算层有 4 案真值、解层有 64/384 逐字映射，但「先天六爻 = 下三爻+上三爻」「后天 =
  元堂爻变」「结构卦名与上下卦自洽」「元堂阴阳与落爻一致」等结构关系没有自动检查，
  回归只能覆盖写死的案例。
- 修：新增 scripts/heluo_invariant_scan.py（随机 N 盘，种子固定，含男女/三元覆盖）与
  tests/test_heluo_invariant_scan.py（16 固定盘 + 脚本 12 盘跑通），检查项：
  ①先天六爻与上下卦一致（TRIGRAM_LINES 下三 + 上三）；
  ②元堂爻位 0-5 且 yao_nature 与落爻阴阳一致；
  ③后天 lines = 先天 lines 在元堂位翻转，step1_hexagram 由上/下卦查 SIXTY_FOUR_HEXAGRAMS；
  ④结构层六爻与 structure.lines 一致、structure.name 与上下卦一致；
  ⑤化工卦 ∈ 八卦；⑥流年卦数量 ≥30 且上下卦 ∈ 64 卦；
  ⑦解层返回必含 benming/benming_ye_buye/liunian_hexagram/kuozhan 且叶不叶 evidence 非空。
- 结果：**200 盘 0 问题**；固化测试 **17 passed**（全族 564 passed）。

### D-013 死断「过第四爻/连三爻」判据错位

- 现象：judge_si_duan 的「若过了第四爻，遇凶 → 十死八九」原写在
  dayun_line_index == 3（即**第四爻本身**，未过），且只取流年最后一年判词；
  「连三爻不吉」也只认近 3 年流年，而原典说的是**后天行爻**（大运三爻）。
- 原典（河洛真数_起例卷之下.txt 后天详说）：「若行后天，连三爻不吉，必多坎壈。
  若过了第四爻，遇凶，十死八九。」；「如后天之气数行至君爻之位，此为数足，到此必死」；
  「纵到君爻，亦不许行至上极一爻，寿必不久」。
- 修：①新增 dayun_combo（当前及前两段大运：卦 + 爻位 + 该爻 ci/buye/suiyun），
  「连三爻不吉」改按大运三爻判词，「过第四爻遇凶」改 dayun_line_index >= 4 且当前
  大运爻判词凶；②build_guajie_from_result 按 qi_phase.dayun 的 age_start/age_end
  取当前段并回溯两段，阳爻九年/阴爻六年口径不变；③保留流年回退（首段不足 3 段时）。
- 实测（纪晓岚盘）：三岁（四爻）→ 连三爻不吉（流年回退）；七岁（五爻）→ 数足必死；
  十三岁（上极）→ 寿必不久 + 数足必死 + 十死八九。
- 新增 tests/test_heluo_si_duan.py **6 passed**；全族 **569 passed**、真值 4/4。

### D-014 流年卦翻转在 0/1 爻值约定下静默失效

- 现象：timeline_yun._flip_line 用 -out[idx] 翻爻，只适用于 ±1 约定；当上游传入
  0/1 约定（如 guajie.hexagram_to_lines 返回 0=阴）时，-0 == 0 爻不翻、卦名不变，
  不报错（静默失效）。实测「同人九三 阳年段」第 8 岁应得蒙卦，实际仍停在剥卦，正是
  原典演例第 8 步。
- 修：_flip_line 改为按「阳=1，其余视为阴」翻转（out[i] = -1 if out[i] == 1 else 1），
  两种约定都正确。
- **原典演例逐岁核对**（河洛真数_起例卷之上.txt 小象行年卦气三个完整演例，均以同人为
  先天卦）：
  · 同人九三·阳年段：同人 → 革 → 随 → 屯 → 复 → 颐 → 剥 → **蒙** → 蛊（9 岁逐岁一致）；
  · 同人九三·阴年段：无妄 → 随 → 革 → 既济 → 明夷 → 贲 → 艮 → 蛊 → 蒙（9 岁逐岁一致）；
  · 同人六二·阴爻段（不取应、不分阴阳年）：乾 → 履 → 中孚 → 损 → 临 → 师（6 岁逐岁一致）。
- 新增 tests/test_heluo_liunian_examples.py **4 passed**（含翻转约定回归）；全族 **569 passed**。


### D-015 流日卦：独立变爻（误）→ 原典链式累积 + 起爻阴阳位

- 现象：timeline_yun.compute_liuri 每段以月卦为底独立变一位，且起爻取
  (yue_yao_index + 1) % 6；与《河洛真数·起例卷之上·起日卦例》原文演例不符。
  实测 乾为天·初九居位 输出 同人/履/小畜/大有/夬/姤，而原典为 履/中孚/损/临/师。
- 原典（河洛真数_起例卷之上.txt 起日卦例）：「假如正月得乾卦初爻，初一日当在三爻，
  变为履六三，初二日变履九四为中孚六四，初三日变中孚九五为损六五，初四日变损上九
  为临上六，初五日变临初九为师初六，挨次而变，不容紊也。」并「阳日寻阳爻位（初、
  三、五），阴日寻阴爻位（二、四、上）」「每一爻管五日」「六爻俱变毕，则满三十日」。
- 修：①起爻 = 居位爻之后第一个同阴阳位（阳日 初/三/五，阴日 二/四/上，回绕），
  compute_liuri 新增 yang_day 参数（默认 True）；②各段在上段结果上累积变下一位
  （链式），自下而上 2→3→4→5→0→1；③段 dict 增 flip_index/yue_yao_index 供断爻定位；
  ④guajie 流日动爻改取「与上一段（段1则与月卦）的单爻差」，回退 flip_index。
- 验证：乾初九 → 履/中孚/损/临/师/坤（原典前五段逐字一致）；1980 盘 2026-09 月卦
  雷水解·四爻居位 → 泽水困/天水讼/天泽履（第 3 段 11-15 日）与逐爻手算一致。
- 异文：河洛理数 卷二下「另画一乾卦」独立变 + 5 爻×6 日口径，按最早书籍不采用。
- 新增 tests/test_heluo_liuri_example.py **6 passed**；既有
  tests/heluo/test_heluo_jingyi.py::test_liuri_yao_jingyi 期望值按链式修正
  （归妹 → 天泽履·初九）。全族 **597 passed**、真值 4/4。


### D-016 生月未知（0）仍参与叶/不叶判定，凭空得「不叶凶象」

- 现象：build_guajie_from_result 未传四柱时 birth_month=0，judge_ye_buye 仍拿 0
  与卦气月比较，输出「生月0月 ≠ 卦气月11月 → 不叶（凶象…）」；流年叶/不叶
  分支更无生月门控。叶/不叶的必要前提是「生月得时」，生月缺失时结论应为不判。
- 修：YeBuYeResult 增 judged 字段（默认 True）；judge_ye_buye 首段加门控
  「birth_month ∉ 1..12 → ye/buye 皆 False、judged=False、evidence 明写不判」；
  流年/命卦两处叶不叶序列化同步带 judged。
- 验证：judge_ye_buye(乾, 0) → judged=False、无「生月0月 ≠」越界比较；
  judge_ye_buye(乾, 4, 甲子) 仍 judged=True、叶、纳甲命中。
- 新增 tests/test_heluo_ye_buye_unknown_month.py **3 passed**；全族 **597 passed**、
  真值 4/4。


### D-017 元气判定漏「人元气 / 互体 / 伏体 / 相生」

- 现象：yuan_qi.compute_yuan_qi 只把「天元气（年干纳甲）、地元气（年支后天宫）」与
  先天/后天的**正体上下卦**比对，漏原典三层判据——
  ①「纳音为人元气」（干支纳卦：金乾兑 / 水坎 / 火离 / 土坤艮 / 木震巽）；
  ②「正体若无，须看互体，互体又无，推及伏体」；
  ③「水命生人，天干地支俱无元气，而得乾兑之卦，是金能生水，亦可谓得元气」。
  后果：原典明举的「甲子生人得小过，互体有兑亦是纳音」被误判 UNRESOLVED；
  且「二者俱反」的凶象可能被伏体兜底掩盖。
- 修（src/tongshu/engines/heluo/yuan_qi.py）：
  ①补六十甲子纳音表 + nayin_element(年干,年支)，人元气卦按「干支纳卦」映射；
  ②按原典优先级判定：正体/互体有元气 → NORMAL；正体见元气错卦（二者俱反）→
  REVERSE；其后才「推及伏体」，最后「生我之卦亦可谓得元气」→ NORMAL（scope=相生）；
  ③补互卦（二三四爻为下互、三四五爻为上互）与伏体（上下卦各取对宫）计算；
  ④YuanQiResult 增 ren_yuan_element / ren_yuan_qi / scope 字段，frozen_state 序列化
  同步扩到 yuan_qi.ren / ren_element / scope。
- 验证：甲子年得小过 → scope=互体、NORMAL、证据「人元气=兑（互体）」；丙子年（纳音水）
  乾卦 → scope=相生、证据「金生水」；甲子年坤卦 → REVERSE（正体见天元反之坤）；
  纪晓岚 甲辰年 → 正体 NORMAL（天元气乾在正体，元气为主）；纳音九组逐条对
  「干支纳卦」原文（甲子金 / 丙寅火 / 戊辰木 / 庚午土 / 壬申金 / 癸亥水 / 甲辰火 /
  庚申木 / 戊申土）。
- 新增 tests/heluo/test_h7_yuan_qi_parts.py **14 passed**（既有 test_h7_yuan_qi.py 7 passed
  不变）；全族 **597 passed**、真值 4/4、结构扫描 60 盘 0 问题。


### D-018 节候卦 / 六十卦表取自二手网文，与原典 72 候冲突（24 条错 23）

- 现象：jiehou.py 的 `JIEHOU_GUA`（24 条节气→候卦→变卦）与 `SIXTY_GUA`（60 条卦序）
  均来自网络二手表，与仓内 `data/heluo/guajie_raw/河洛真数_起例卷之下.txt`「节候卦爻」
  段冲突：24 条中只有冬至（颐六四）正确，其余 **23 条全错**——
  立春原文为「小过初爻」，旧表作「泰六三」；春分原文「晋四爻」，旧作「夬二」；
  夏至原文「井四爻」，旧作「比四」；秋分原文「大畜四爻」，旧作「丰四」；
  小寒原文「屯初爻」，旧作「井三」……
  旧表的「变卦」列机械上也不自洽（如泰六三翻转应为泽地萃，旧写雷水解）。
  另 `SIXTY_GUA` 含 5 处重复（贲/困/涣/节/损）与讹字「宜」。
- 原典结构（起例卷之下·节候卦爻）：
  ①八节卦：坎初六起冬至→上六惊蛰，震初九起春分→上六芒种，
  离初九起夏至→上九白露，兑初九起秋分→上六大雪；「每卦总管九十日，自下而上，
  每一爻各直十五日」；
  ②七十二候：自「候卦颐四爻起冬至蚯蚓结」至「未济上爻虎始交、蹇五爻荔挺出」，
  每卦总六日、自初而上爻各一日；「生时值节卦者谓之化工，生月值卦者谓之得令」。
- 修（src/tongshu/engines/heluo/jiehhou.py 全文重写，约 470 行）：
  ①`HOU_GUA` = 72 元组（节气索引/候序/卦短名/爻位 0-5/候名），逐条照原文；
  ②`HOU_GUA_BY_JQ` 取候序 1 的 24 条 → `JIEHOU_GUA` 由首候派生，变卦 = 该爻机械翻转
  （原典未载变卦，仅作参考并在证据注明）；
  ③`JIE_GUA` = 24 条四正卦分领（坎/震/离/兑 各 6 爻），`jie_line = jq % 6`；
  ④`BI_GUA_BY_JQ` 节气→当值辟卦（按月建：冬至复、立春泰、夏至姤…）；
  ⑤`SIXTY_GUA` 改为文王序去四正卦（60 条、无重复、无讹字）；
  ⑥`SeasonalHexagram` 增 `jie_gua/jie_line/hou`，`moving_line` 改 0-based（与
  `hexagram_to_lines` 一致），`_yao_label` 出「初六/九二」原典爻名；`QiPhase` 增 `bi_gua`。
- 数据问题（已登记，不修表）：原文「离九二大暑」为刻本讹字（离无九二，按
  初九/六二/九三/九四/六五/上九 排布）；候名「鹰化为始」为月令「鹰化为鸠」之讹
  （测试用异文字典 `_HOU_VARIANTS` 兼容原文）；原文「随三大雨时行」「随五鹰化为始」
  同卦两爻重复出现，按原文照录不擅改。
- 验证：72/72 候名按序命中原文；24 条候卦由首候派生；变卦机械一致；八节卦 24/24
  与首句一致；`get_qi_phase` 二至二分为四正卦（`six_day_seven_method=False`）、
  其余行六日七分。新增 tests/test_heluo_jiehhou_yuanwen.py **8 passed**，
  test_h11_jiehhou.py / test_h16_independent_verification.py / test_full_pipeline.py
  断言按原典更新（**32 passed**）；全族 **605 passed**、真值 4/4、结构扫描 60 盘 0 问题。
- 影响面：`JIEHOU_GUA` 只经 `canonical._compute_seasonal_hexagram` → 证据文本与
  `frozen_state` 存档，无逻辑分支依赖其数值；`SIXTY_GUA` 无任何消费者。

### D-019 化工卦四季映射错位一月，且缺互体/纳音/四季土旺三层判据

- 现象：`hua_gong.py` 的 `SEASON_BRANCH_TO_HUAGONG` 为 亥子丑→坎 / 寅卯辰→震 /
  巳午未→离 / 申酉戌→兑（农历四季分法），与《河洛真数·起例卷之上·化工论》四句
  整体错位一个月；且只有「正体有/反卦有」两档，缺互体与纳甲纳音代用、缺四季月
  坤艮土旺。
- 原典明文：
  - 「坎卦自冬至十一月中以后至惊蛰终止」→ 子丑寅（冬至在子月中，惊蛰为卯月节）
  - 「震卦自春分二月中以后至芒种终止」→ 卯辰巳
  - 「离卦自夏至五月中以后至白露终止」→ 午未申
  - 「兑卦自秋分八月中以后至大雪终止」→ 酉戌亥
  - 「坤艮卦主四季辰戌丑未月，除正节气十二日外，各旺十八日。妇人得此，名儿女星，
    又为贞母节妇」
  - 「正不逢而互体得之；若正互俱无，则取纳甲纳音，终是浅薄，福寿减半」
  - 反卦四条：坎反离（夏至后秋分前）、离反坎（冬至后春分前）、兑反震（春分后夏至前）、
    震反兑（秋分后冬至前）
- 修（`src/tongshu/engines/heluo/hua_gong.py` 重写）：
  ① 映射改 子丑寅→坎 / 卯辰巳→震 / 午未申→离 / 酉戌亥→兑；
  ② 新增 `TU_WANG_BRANCHES=("辰","戌","丑","未")`、`TU_WANG_TRIGRAMS=("坤","艮")`：
     四季月见坤艮即土旺化工（女命追加「儿女星/贞母节妇」注）；
  ③ 新增 `hu_trigrams(upper, lower)`（上互三四五爻、下互二三四爻）→ 正体无而互体有
     则 `scope="互体"`；
  ④ 新增纳音层：`nayin_element(年干,年支)`（60 甲子纳音，与 D-017 共用）→ 纳音五行
     与当令化工同气或生之，则 `scope="纳音"`、`weak=True`，证据注明「终是浅薄，福寿减半」；
  ⑤ `HuaGongResult` 增 `scope/weak/tu_wang` 三字段，证据串带判据来源。
- 接线（`canonical._compute_huagong`）：原实现 `birth_date` 缺省被填成 `YYYY-01-01`
  （子月），四柱月支为未月者被误判成坎月。改为：有真实出生日期时按 `resolve_birth_month_branch`
  取节气月支，否则回退**四柱月支**（`bazi[1][1]`）；同时传入纳音五行与性别。
- 测试更新：`test_h6_hua_gong.py` / `test_h16_independent_verification.py` /
  `test_full_pipeline.py` 断言按新映射逐条改写（旧图上经互体会命中化工者已换图）；
  `test_h2_frozen_state.py::test_huagong` 纪晓岚案由 UNRESOLVED 改 NORMAL（未月四季土旺、
  先天泰卦含坤）；`test_h12_diagnosis.py::test_huagong_assertion_present` 改为按
  `HUAGONG_DIRECTION[state]` 断言，并修 `diagnosis_rule_graph` 中证据派生的化工断言
  方向（原固定落 NEUTRAL，与冻结态补充的同名断言方向矛盾）。
- 验证：新增 `tests/heluo/test_h6_huagong_yuanwen.py` **25 passed**（原典四句逐字命中、
  12 月支参数化、映射精确三分组、土旺女命/男命、互体、纳音同气/相生/不合、
  反卦、证据串）；全族 **630 passed**；真值 4/4；结构扫描 60 盘 0 问题。
