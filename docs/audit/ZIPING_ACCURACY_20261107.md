# 子平引擎准确度审计（2026-11-07）

## 一、结论

用户 m06938 要求把「离算得对还差三层」全部落地。本轮完成：

| 三层面 | 状态 | 证据 |
|---|---|---|
| ①判据只到候选 | 部分修复（判据侧） | 身强弱六态新增成局/官杀有力两条原典判据（D-01/D-02） |
| ②无真值层 | **已建** | `cases/truth/ziping_truth_cases.json` + `scripts/ziping_truth_replay.py` **7/7 PASS** |
| ③生产链路空转 | **已修** | `ziping_bridge.run_ziping_judgment` 改接 `ziping_v3.runner.run_ziping`，三域真判断（D-03） |

回归：`pytest tests -k "ziping or v3 or strength or daymaster or yongshen or geju or pattern" --ignore=tests/test_ziping_15_2_evidence_provenance.py` → **1287 passed / 7 failed**，其中 5 项为 GPT 子平线在途（`tests/test_ziping_relation_presence.py` 4 项 + `test_ziping_v3_e2e_runner` PATTERN 开关 1 项），2 项为旧仓迁移遗留（`tests/test_edition_registry.py`、`tests/test_m2a_migration.py`），与本轮改动无关。

## 二、真值层（沈孝瞻原文 + 穷通宝鉴双证）

- 资产：`cases/truth/ziping_truth_cases.json`（schema `ziping-truth-cases-v1`）
- 主源：`registries/source/raw/PZZQ_子平真诠_沈孝瞻原文.md`（行号逐案标注）
- 副源：穷通宝鉴调候（`yongshen.py` QTPJ 120 格，逐案引原文）
- 选取纪律：**用神断言只取「沈说 == 调候」双证一致之案**；两说冲突者不入断言，记入 `conflicts`（各带 `data_issue`）。
- 复算：四柱 → 公历由 `scripts/ziping_truth_replay.py` 逐日求解，并以 `BaziEngine` 四柱复核（含立春年界，避免 7/1 近似误判）。

7 条断言案（全部 PASS）：

| 案 | 四柱 | 公历 | 断言 |
|---|---|---|---|
| ziping-001 刘镇华 | 癸未 辛酉 甲申 丙寅 | 1883-10-07 04:00 | 旺衰=BALANCED；用神=火 |
| ziping-003 龙济光 | 丁卯 丙午 丙子 壬辰 | 1867-06-25 08:00 | 用神=水 |
| ziping-005 王士珍 | 辛酉 丙申 庚子 丙戌 | 1861-08-19 20:00 | 用神=火 |
| ziping-007 林森 | 戊辰 甲寅 丁卯 己酉 | 1868-02-11 18:00 | 用神=金 |
| ziping-008 乾隆 | 辛卯 丁酉 庚午 丙子 | 1951-09-27 00:00 | 用神=火 |
| ziping-009 朱家骅 | 癸巳 丁巳 丁卯 丙午 | 1893-05-30 12:00 | 旺衰=STRONG |
| ziping-010 王克敏 | 丙子 壬辰 壬申 乙巳 | 1876-05-04 10:00 | 旺衰=STRONG；用神=木 |

3 条口径冲突（不作对错断言，登记待裁决）：洗冠生（沈土/调候火）、张耀曾（沈金/调候木）、朱家骅（沈水/调候金）。引擎 `basis=QTPJ-TIAOHOU`，即引擎主用神走调候口径；这是设计选择，不是随机错。

## 三、缺陷与修法

### D-01 三合/三会成局不归党（原典级）

- 现象：王克敏 丙子 壬辰 壬申 乙巳，申子辰三合水局成，沈断「日元太旺」；引擎 `derive_party` 只逐字分类天干/藏干，不识别局 → BALANCED。
- 依据：子平真诠/滴天髓均以「三合成局」论党，成局者不按单支论强弱。
- 修：`constants.py` 增 `SANHE_JU`（申子辰水/亥卯未木/寅午戌火/巳酉丑金）与 `SANHUI_JU`（寅卯辰/巳午未/申酉戌/亥子丑）；`reference.detect_ju(fact)` 只认三支齐备（半合不算成局）；`judgment.derive_party_structure` 把局按五行归入党众（比劫局/印局/食伤局/财局/官杀局），输出 `DAY_JU`；`judge_strength` 新增 **STRENGTH-016**：日主之局成且有效根在 → STRONG（不论月令得失）。
- 实测：王克敏 BALANCED → STRONG ✓。

### D-02 官杀虚浮即降旺（原典级）

- 现象：朱家骅 癸巳 丁巳 丁卯 丙午，沈断「日元太旺」；引擎 `STRENGTH-011` 只判「对立存在」不判有力 → WANG_BUT_NOT_STRONG。
- 依据：滴天髓「克需有力」；虚浮之克（癸水坐巳无根）不作降旺；食伤/财耗属「宜泄」，不改变旺衰判定。
- 修：`derive_party_structure` 计算对立五行于四支藏干的**本气/中气**之根（`OPPOSITION_ROOTED`）及「克我之官杀是否有力」（`GUANSHA_EFFECTIVE`）；`judge_strength`：
  - **STRENGTH-017**：得令 + 有效根 + 有助 + 对立存在但官杀虚浮 → STRONG；
  - **STRENGTH-011** 降为「官杀有力」才成立（无根/仅余气之根不降旺）。
- 实测：朱家骅 WANG_BUT_NOT_STRONG → STRONG ✓；刘镇华 BALANCED、龙济光 WANG_BUT_NOT_STRONG 不变。

### D-03 生产链路空转（P0）

- 现象：`ziping_bridge.run_ziping_judgment` 传 `JudgmentFactory.judge_all({}, context)` 空 signals，五域恒 None；`ziping_v3` 全仓零外部 importer。
- 修：`ziping_bridge.py` 改为调用 `ziping_v3.runner.run_ziping(chart, enable_pattern=True)`，并把 旺衰/格局/用神 三域映射为 `JudgmentSynthesis`：
  - 旺衰：六态 → STRONG/MODERATE/WEAK（`WANG_BUT_NOT_STRONG` 归强侧、`SHUAI_BUT_NOT_WEAK` 归弱侧）；
  - 格局：仅 `_FORMED` 记 ESTABLISHED，候选/未裁 fail-closed 为 UNKNOWN；
  - 用神：有主用神 → PRIMARY，reasoning 带 `basis` 与调候原文；
  - 十神/事件：引擎未输出 → UNKNOWN（不伪造）。
- 实测 1990-03-01 12:00 男：`wangshuai=STRONG / geju=ESTABLISHED / yongshen=PRIMARY（火，QTPJ-TIAOHOU）`，`has_core_judgment=True`（此前恒 False）。
- 测试口径修正：`tests/test_ziping_bridge.py::test_deterministic` 原比对 `DomainJudgment` 全字段（含 `created_at` 时间戳），改为比对 (domain, conclusion, reasoning)；结论确定性不变。

## 四、尚未闭合

1. **十神/事件两域仍无引擎输出**（bridge fail-closed 为 UNKNOWN）；需要 V3 补 `SHISHEN`/`SHIJIAN` 判据，否则 `has_complete_judgment` 恒 False。
2. **格局判据仍以候选为主**（BLADE_CANDIDATE 等），仅 LU_FORMED/WEALTH_FORMED/INJURY_FORMED 等为「成立」态；与「原典格局确立」仍有差距。
3. **用神口径冲突未裁决**：沈（格局/扶抑）vs 调候（穷通宝鉴）。引擎现取调候优先；若产品口径要求「子平用神」，需要把 `YongShenEngine.verdict` 改为格局优先或在输出中并列两说。
4. **`cases/golden/ziping_golden_set.json` 仍未接入 replay**（golden_replay 只 hash）；建议后续把 expected 改为真值断言或标注为签名快照（同盲派处理）。
5. **真值覆盖 7 案 + 3 冲突**，可继续从《子平真诠》《滴天髓》补案（谭延闿/蔡元培两案四柱已解出，但用神两说冲突，暂不入选）。

## 五、p0_v2 切片库恢复（2026-11-07）

**现象**：生产代码 `engines/production_entry.py:278` 有 `from p0_v2.jiu_ying import build_jiu_ying`，
`engines/common/slice_loader.py` 以 `p0_v2/六部经典MD文库/` 为 canonical 切片源，但主仓 **p0_v2 目录不存在**
（该目录只存在于旧 worktree `D:\shuntian-ziping-p0`）。后果：
- `jiu_ying_status` 恒 `NOT_EVALUABLE`，`reason="依赖模块缺失: p0_v2"`；
- `slice_loader` 无法加载任何切片（932 条规则对生产不可见）。

**处置**：从旧 worktree 恢复 `p0_v2/`（去掉 `output/`、`case_audit/` 两类运行产物与 `__pycache__`，保留代码 +
`六部经典MD文库` 949 份 MD 切片 + 契约文档）。恢复后实测：
- `slice_loader.count()` = **932**；
- `build_jiu_ying("癸未辛酉甲申丙寅", {...})` 返回 7 键（triggered/type/success/evidence/note/rescue_wx/xiang_note），
  六条判据 id 齐出（JIU_YING.001–.006，.005 含 a~j 子型）。

**口径说明**：`p0_v2/jiu_ying.py` 是探针阶段实现（docstring 自述 .001/.004/.005/.006 需通关事实/相神定位，
标 PENDING），故 `production_entry` 只把它记为 `jiu_ying_legacy_diagnostic`（`LEGACY_UNVERIFIED`），
`facts['jiu_ying']` 仍取 `rescue.assess_rescue_scope` 的结构候选——即：**恢复后救应不再是「模块缺失」，
但仍未升级为「已核验成功」**，与 CODEX_PROGRESS 的三态语义一致。

**回归**：恢复前后 `pytest tests -k ziping --ignore=tests/test_ziping_15_2_evidence_provenance.py`
均为 **1205 passed / 5 failed**（4 项 GPT 在途 relation_presence + 1 项 V3 PATTERN 开关），无新增失败。

## 六、复现

```powershell
$env:PYTHONPATH='D:\shuntian\src'
python scripts\ziping_truth_replay.py --all      # 7/7 PASS + 冲突对照
python -m pytest tests\test_ziping_truth.py tests\test_ziping_bridge.py -q   # 33 passed
python -m pytest tests -k "ziping or v3 or strength or daymaster or yongshen or geju or pattern" `
    --ignore=tests/test_ziping_15_2_evidence_provenance.py -q
```
