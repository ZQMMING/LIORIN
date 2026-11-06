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
| 全族回归 | **527 passed**（`-k "heluo or meihua"`，1 error 为子平线 CITATION，pre-existing） | pytest |

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
python -m pytest tests -k "heluo or meihua" --continue-on-collection-errors -q                                      # 540 passed / 1 pre-existing error
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
- `build_guajie_from_result` 在无四柱时用 `birth_month or 1`，把「未知生月」静默当正月，
  数凶判据的阳月分支因此会把「未知」判成「阳月 → 数凶」。
  → 改为 `birth_month or 0`，`judge_shu_xiong` 对 `<=0` 显式记「生月未知 → 阳月判据跳过」。

纪晓岚实测（甲辰 辛未 丙戌 甲午 男 午时）：命卦泰（卦气正月），生月六月 → 月不合、
年干支甲辰在纳甲 → **半叶**；数凶 `以弱敌强（天22/56）+ 生月6月（阳月）`。
