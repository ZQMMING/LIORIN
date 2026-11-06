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

## 六、复现命令

```powershell
$env:PYTHONPATH='D:\shuntian\src'
$env:PYTHONIOENCODING='utf-8'
python -m pytest tests/test_heluo_truth.py tests/test_heluo_guajie_mapping.py tests/test_heluo_canping_truth.py -q   # 17 passed
python -m pytest tests -k "heluo or meihua" --continue-on-collection-errors -q                                      # 527 passed
python scripts/heluo_truth_replay.py                                                                               # 4/4 PASS
```
