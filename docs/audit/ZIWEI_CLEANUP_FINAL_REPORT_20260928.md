# Shuntian blind/ziwei 清理收尾报告

**执行时间**: 2026-09-28  
**分支**: `maintenance/blind-ziwei-migration-20260928`  
**上游 commit**: `bb9f3040`

## 本轮执行动作

执行用户确认的清理收尾动作，不提交、不覆盖业务资产，只做“明确可重建且非业务”的缓存/构建产物清理，并把本轮依赖恢复和验证结果写进报告。

## 清理结果

已删除：

- 项目范围 `__pycache__`
- 项目范围 `*.pyc` / `*.pyo`
- `.pytest_cache/`
- `frontend-case/node_modules`
- `src/node_modules`
- `src/tongshu.egg-info`
- `node_modules/node_modules`
- `node_modules/iztro/node_modules`

已保留（本轮不能删除）：

- `src/tongshu/**`
- `tests/**`、`cases/golden/**`
- `data/rules_index/**`、`backend/data/**`
- provenance/audit 文档
- `archive/**`
- `blind/**`、`blind_engine/**`、`engines/**`、`scripts/legacy/**`、`blind_seg/**` 等证据镜像/历史副本
- 当前 `node_modules/` 整体（含真实运行的 iztro/lunar-typescript/i18next 路径）

## 依赖修复动作

本次发现并修复了一个运行依赖缺失问题：

- 误删 `node_modules/iztro/node_modules/lunar-typescript/dist`、`node_modules/lunar-typescript/dist`、`node_modules/i18next/dist`
- 已从 `E:\迁移合并\ziwei_engine\node_modules` 同版本副本中恢复：
  - `node_modules/lunar-typescript/dist`
  - `node_modules/iztro/node_modules/lunar-typescript/dist`
  - `node_modules/i18next/dist`

当前环境确认可用：

```text
iztro present: yes
lunar-typescript present: yes
project __pycache__: 0
project pyc/pyo: 0
```

## 回归结果

### 紫微核心+规则+钦天门

```text
tests/test_ziwei_chart_contract.py
tests/test_ziwei_engine.py
tests/spec/test_vertical_slice_ziwei.py
tests/test_ziwei_phase_a0_extended.py
tests/test_ziwei_chart_cross_validate.py
tests/test_ziwei_method_profile.py
tests/test_ziwei_palace_resolution.py
tests/test_ziwei_rule_graph.py
tests/test_ziwei_sanhe_judgments_p10.py
tests/test_ziwei_qintian_p07.py
```

结果：**250 passed, 32 subtests passed**  
环境：真实 iztro、非 stub

### Bazi/河洛

```text
tests/test_b02_late_zi_golden.py
tests/test_canonical_bazi_contract.py
tests/test_heluo_context.py
tests/test_heluo_canonical.py
```

结果：**43 passed**

### Blind

```text
tests/test_blind_integration_bazi.py
tests/test_blind_golden.py
tests/test_blind_negative.py
tests/test_blind_rule_compliance.py
tests/test_blind_signal_regression.py
blind_tests/test_blind_rules
```

结果：**148 passed, 7 subtests passed, 3 failed**  
失败为既有契约错位：

- `TestRuleGraph.test_load_and_match`：规则样本路径/字段契约不满足
- `TestRuleGraph.test_get_rule`：未加载导致取不到规则
- `TestRuleGraph.test_zuo_gong_method_matching`：`MatchContext` 接口不匹配

本轮未改测试期望、未改 blind 引擎语义。

## 生产入口断言

```text
ziwei_engine     = D:\shuntian\src\tongshu\engines\ziwei_engine.py
ziwei_adapter    = D:\shuntian\src\tongshu\engines\ziwei_adapter.py
bazi_engine      = D:\shuntian\src\tongshu\engines\bazi_engine.py
ziping_v3        = D:\shuntian\src\tongshu\reasoning\ziping_v3\engine.py
heluo_adapter    = D:\shuntian\src\tongshu\engines\heluo_adapter.py
```

全部来自 `D:\shuntian\src\tongshu`。

## 本轮真实运行断言

```text
ZiweiEngine(...).full_chart((1984,10,15),10,'male')
=> source=iztro
=> palaces=12
=> soul_earthly_branch='午'
=> body_earthly_branch='辰'
```

## 快照落盘

已写入本轮可回看审计快照：

```text
docs/audit/ZIWEI_CLEANUP_FINAL_STATUS_20260928.txt
docs/audit/ZIWEI_CLEANUP_FINAL_LOG_20260928.txt
docs/audit/ZIWEI_CLEANUP_FINAL_DIFF_STAT_20260928.txt
```

## 本轮未做

- 不提交本次清理
- 不合并或覆盖 E 侧代码
- 不删除根级 `blind/`、`blind_engine/`、`engines/`、`rules/`、证据镜像、脚本和历史目录
- 不修改 Golden、数据库、冻结规则、API 和部署入口
