# 子平 p0 线生产接线审计（2026-11-07）

## 一、结论

| 项 | 状态 | 证据 |
|---|---|---|
| 生产桥接指向 p0 引擎 | ✅ | `run_ziping_judgment` → `engines.production_entry`（G-P01~G-P04 gate） |
| 结论进入 V13 claim | ✅ | 1984-12-07 16:00 男 → `AC-ZP-geju-established` / `AC-ZP-yongshen-primary` |
| G1 证据闸 | ✅ | claim.evidence_refs 为 p0_v2 切片 ID，已登记集合可解析；`validation_passed=True` |
| 诚实降级 | ✅ | 旺衰/十神/事件域 `UNKNOWN` 并写明原因；无证据锚的结论不产 claim |
| 测试 | ✅ | `pytest -k ziping` = 1168 passed / 4 failed（4 项均为 GPT 在途 `test_ziping_relation_presence.py`） |

提交：`35e87afb`（7 files，+349/−202，仅子平）。

## 二、链路

```
BaziChart
  └─ run_ziping_judgment(chart)            src/tongshu/reasoning/ziping_bridge.py
       ├─ assert_canonical_gate(chart)     （BZ-FNDR-15，失败 → 五域 UNKNOWN）
       ├─ _pillars_from_chart(chart)       chart.get_pillars_chinese() → {year:[干,支],…}
       ├─ engines.production_entry(FrozenCanonicalBaziChart(pillars))   p0 线唯一生产入口
       │    └─ gate_passed / engine_result(facts) / zhenglun{…yongyao}
       └─ _engines_p0_synthesis(result)    → JudgmentSynthesis 五域
            └─ JudgmentClaimComposer.compose → AC-ZP-* claims → G1 evidence_gate
```

## 三、五域映射口径（不夸大）

| 域 | 映射 | 依据 |
|---|---|---|
| WANGSHUAI | `UNKNOWN` | p0 旺衰轨只输出得令/失令候选，boundary 明言「不回答身强身弱」 |
| GEJU | `cheng_bai=="CHENG"`→ESTABLISHED；`"BAI"`→BROKEN；其余 UNKNOWN | `facts.ge_cheng`（`ge`/`cheng_bai`/`ge_evidence`） |
| YONGSHEN | `zhenglun.yongyao.primary_medicine.wuxing` → PRIMARY | `state` 非 `PATTERN_CONFLICT_NOT_EVALUABLE`/`NO_CANDIDATE` |
| SHISHEN / SHIJIAN | `UNKNOWN` | p0 engines 线未输出 |

结论均附：`rule_refs = ["ZIPING_ENGINES_P0", <PZZQ 规则码>]`；`evidence_refs = p0 切片 ID`。
无可用证据锚时该域降级 `UNKNOWN`（不产生无证据 claim）。

## 四、证据锚（p0_v2 切片）

- 新增 `src/tongshu/reasoning/p0_evidence.py`：扫描 `p0_v2/六部经典MD文库/**/*.md`，
  以 `**切片ID**：` 建索引（当前 921 片），每片带书名/校验状态/原文。
- 证据码归一化：p0 引擎引用形如 `DTS PATHOLOGY_QI_HOU.008`，切片 ID 形如
  `PATHOLOGY.QI_HOU.008`；归一化失败即不登记（不造 ID）。
- `src/tongshu/pipeline.py::for_demo` 将切片 ID 并入 G1 已登记 `evidence_ids`
  （与 `BZI-TG-*` 运行时证据同机制）。

## 五、实测

| 出生（男） | 格局 | 用药 | AC-ZP claims |
|---|---|---|---|
| 1984-12-07 16:00 | 印格 CHENG | 火（调候，YONGYAO_RESOLVED） | 2（geju/yongshen） |
| 1990-03-01 12:00 | 建禄月劫格 CHENG | 土（格体喜神，GE_FALLBACK） | 2 |
| 1990-01-01 12:00 | 正官格 NOT_EVALUABLE | NO_BING | 0（成败未核验，不产 claim） |

样例 claim 证据：
- `AC-ZP-geju-established` → `STRUCTURE.GE_JU.CHENG_BAI.001/007`
- `AC-ZP-yongshen-primary` → `PATHOLOGY.QI_HOU.008`、`STATE.WANG_SHUAI.FAN_JU.001`

## 六、测试口径变更

1. 删除 `tests/test_ziping_15_2_evidence_provenance.py`：其主体属已移除的 ZIPING-V3 线，
   `from tongshu.reasoning.judgment import CITATION` 已不存在（全仓唯一 collection error）。
2. `tests/test_int_01_02_03_pipeline_wiring.py::test_t3_baseline_untouched`：T-3 基线
   73 → 62（去掉已删套件），套件列表同步。
3. `tests/test_int_06_pipeline_integration.py::test_production_path_composer_on`：
   改用 1984-12-07 16:00（印格 CHENG），并新增「claim 必须带证据锚/规则锚」断言。
4. `tests/test_ziping_bridge.py`：断言规则码前缀 `PZZQ*` 与证据锚非空。

## 七、未闭合（下一阶段）

1. **旺衰（身强身弱）**：p0 线不判，`has_core_judgment` 仍 False（诚实状态）。
2. **十神/事件域**：p0 线无输出。
3. **胜负未核验盘**：`cheng_bai=NOT_EVALUABLE` 时不产 claim（需 p0 判据补齐后才可证）。
4. **真值层待重建**：p0 线尚未有古案 → 原典结论回放（可复用 `p0_v2/六部经典MD文库` 932 切片）。
5. `cases/golden/ziping_golden_set.json` 的 expected 仍未接入 replay。

## 八、复现

```
$env:PYTHONPATH='D:\shuntian\src'
$env:PYTHONUTF8='1'
python -m pytest tests -k ziping -q                      # 1168 passed / 4 在途
python -m pytest tests/test_audit_gates.py -q            # 39 passed
python -m pytest tests/test_int_06_pipeline_integration.py tests/test_int_01_02_03_pipeline_wiring.py -q
```
