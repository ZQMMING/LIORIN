# 子平引擎交接评估（2026-11-07）

> 结论：子平线由 GPT 接管，本文件是交接材料。以下结论均为实测/取证所得，命令可复现。
> 我方不再改动 `src/tongshu/reasoning/ziping_v3/`、`src/tongshu/reasoning/ziping_bridge.py`、
> `engines/common/`、`src/tongshu/reasoning/judgment.py` 等子平热区，避免与 GPT 未提交改动冲突。

## 一、资产与规模

| 位置 | 规模 | 角色 |
|---|---|---|
| `src/tongshu/reasoning/ziping_v3/` | 19 个 py + data，538 KB | 子平 v3 编排引擎（facts_adapter / engine / judgment / judgment_ext / interpretation / interpretation_v2 / pattern / pattern_routes / pipeline / reference / rules_loader / runner / search_gate / special / temporal_bridge / types / yongshen / arch_gate） |
| `src/tongshu/reasoning/ziping_bridge.py` | 101 行 | 生产接线层，被 `src/tongshu/pipeline_stages/compute_stage.py:234` 消费 |
| `engines/yuhai_ziping/` | 76 文件 268 KB | 玉海子平规则/证据框架 |
| `engines/ziping_zhenquan/` | 41 文件 132 KB | 子平真诠规则框架 |
| `tests/test_ziping_*.py` | 56 个 | 子平族测试 |

## 二、测试基线（工作树，含 GPT 未提交改动）

`pytest tests -k "ziping" --continue-on-collection-errors -q` → **1196 passed / 5 failed / 1 error**。

- **collection error**：`tests/test_ziping_15_2_evidence_provenance.py:18`
  `from tongshu.reasoning.judgment import CITATION, _Citations` →
  `ImportError: cannot import name 'CITATION'`。
  在干净 HEAD worktree（`git worktree add` 到 HEAD）复跑同样报错 → **pre-existing**，非本次改动引入。
- **4 failed**：`tests/test_ziping_relation_presence.py`（**未跟踪文件**，GPT 正在编写）。
  把该文件拷到干净 HEAD 代码上跑会挂另外 4 条（同一断言的反向）→ 相关行为正在被调整，
  属在途工作，不宜按缺陷追（`engines/common/daymaster_power_queries.py` 处于 M 状态）。
- **1 failed**：`tests/test_ziping_v3_e2e_runner.py::test_unimplemented_fail_closed`
  断言 `PATTERN` 已实现，实测 `PATTERN=UNDETERMINED / RULE_MISSING`。
  根因是 `ziping_v3/runner.py:56` 的 `enable_pattern: bool = False`，注释写明
  「[2026-10-01 用户裁决] 格局(PATTERN)输出开关默认 False…主仓暂不输出格局」；
  TRUE / XIANG / DISEASE / YONG-PATTERN 级联 UNDETERMINED。**测试口径过期，与裁决冲突**；
  干净 HEAD 上同样红。

## 三、P0：生产辨层空转（必读）

生产链路：

```
compute_stage.py:234  run_ziping_judgment(bazi_chart)
  → ziping_bridge.py:85  build_context(chart)
  → ziping_bridge.py:87  JudgmentFactory.judge_all(signals_by_domain={}, context)
```

`signals_by_domain` 是**空 dict**（该写法自 `d3cd7fba` 起即如此）。实测（1980-06-22 10:00 男）：

```
JudgmentSynthesis: wangshuai=None geju=None yongshen=None shishen=None shijian=None
has_complete_judgment=False  has_core_judgment=False
```

后果：生产上子平辨层不产出任何判断，`JudgmentClaimComposer.compose(_synth)` 无 claim 可组合；
pipeline 里子平"辨"只剩 Chain-A 断言驱动。

另一个事实：`ziping_v3` 在 `src/`、`engines/`、`scripts/` 中**无任何外部 importer**
（仅模块互引 + `arch_gate.py` 注释提及）。真正能跑 17 个域（ROOT/PARTY/STRENGTH/CLIMATE/QING/
PATTERN/TRUE/YONG-PATTERN/YONG-CLIMATE/YONG-DISEASE/YONG-BRIDGE/XIJI/TEMPORAL…）的实现
目前只被测试驱动，未进入生产。

口径不一致：`ziping_bridge.py:70` docstring 写「真实生产路径必须 `assert_canonical_gate(require_factory=True)`」，
而 `:84` 实际传 `require_factory=False`。

## 四、P1：25 案金标对正确性零约束

`cases/golden/ziping_golden_set.json`：25 案，期望字段含
`wangshuai.conclusion / score / get_ling_score / geju.ge_type / yongshen.yongshen_type`。

- `scripts/golden_replay.py:148-166` 的 ziping 分支只把 `run_ziping_judgment` 输出 hash 后
  与 `cases/baselines/golden_replay_baseline.json` 比对，**从不读 expected_calculation**；
- 全仓 `expected_calculation` 仅 `tests/test_blind_snapshot.py` 读取，
  **没有测试拿这 25 案的金标断言子平输出**；
- `python scripts/golden_replay.py --engine ziping --check` →
  `2008d32871b512b3 → f01f9b2d0b79c0b3 CHANGED`。最可能是
  `fc684205 ZIPING-REVERT: 回退错误的定量评分算法到原始空壳状态`（2026-09-11）导致，
  属 EXPECTED_CHANGE，但 baseline 未按 §21 重录。
- 期望值形态（如 `score=7 = 3+2+2`）是引擎自建评分口径，非原典可推值 → 存在自证风险。

建议二选一：按原典重建为真值层（参照 `cases/truth/blind_truth_cases.json` + replay + pytest 的既有模式），
或改名 `ziping_engine_snapshot.json` 并注明「不是真值」。

## 五、P2：治理面

`src/tongshu/reasoning/ziping_v3/arch_gate.py:20`
`RULES_DIR = REPO / "backend" / "data" / "rules"` —— 该目录**不存在**；
真实规则在 `data/rules`（140 个文件）。因此「CI 级 FORBIDDEN 算子扫描」实际扫 0 个 YAML，
且没有测试引用 `arch_gate`。

## 六、复现命令

```powershell
$env:PYTHONPATH='D:\shuntian\src'
python -m pytest tests -k "ziping" --continue-on-collection-errors -q
python -c "from tongshu.engines.bazi_engine import BaziEngine; from tongshu.reasoning.ziping_bridge import run_ziping_judgment; print(run_ziping_judgment(BaziEngine().compute((1980,6,22,10))).to_dict())"
python scripts/golden_replay.py --engine ziping --check
```
