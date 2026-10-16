# 紫微引擎生产链修复报告

**日期**: 2026-09-28  
**范围**: `src/tongshu/engines/ziwei_engine.py`、`src/tongshu/engines/ziwei_adapter.py`、紫微合同测试  
**环境**: Python 3.11.15、Node v24.19.0、iztro 2.6.0

## 1. 修复目标

修复紫微生产入口返回的 `ZiweiChart` 顶层结构缺失问题，使 `ZiweiEngine.compute()`、`ZiweiSolarAdapter.compute()` 与 `full_chart()` 统一提供命身宫、十二宫和规则层所需的宫干/飞化事实。

未新增星曜、四化、流派算法；未修改 Golden、数据库或紫微 Canonical 冻结状态。

## 2. 修复前证据

真实 `iztro` 环境下：

```text
ZiweiEngine.compute():
  source=iztro
  soul_earthly_branch=''
  palaces={}
  palace_data['palaces']=完整宫位

ZiweiSolarAdapter.compute():
  source=iztro
  soul_earthly_branch=''
  palaces={}
  palace_data['palaces']=完整宫位

ZiweiEngine.full_chart():
  source=iztro
  soul_earthly_branch='午'
  palaces=12
```

下游 `evidence_producer.py`、`rules/decadal.py`、`rules/feixing_rule_graph.py`、`rules/qintian/combinations.py` 等直接读取 `chart.palaces`、`chart.palace_stems` 或 `chart.flying_transforms`，因此生产 chart 会出现空消费结果。

## 3. 变更内容

### `src/tongshu/engines/ziwei_engine.py`

- Node `byLunar` 输出新增完整 `palaces`、`fiveElementsClass`、大限干支等字段。
- `_compute_via_iztro()` 将宫位同步写入：
  - `ZiweiChart.palaces`
  - `ZiweiChart.palace_data['palaces']`
- 将命宫/身宫地支写入顶层 `soul_earthly_branch` / `body_earthly_branch`。
- 写入五行局、出生年份和性别。
- `from_dict()` 兼容旧版仅含 `palace_data['palaces']` 的序列化数据，并补齐命身宫、五行局、流运字段。
- 未知主星名称不再被静默丢弃，保留原名称以便诊断；已有语义层仍只处理已登记主星。
- iztro 解析失败保留异常类型和错误信息；只有显式设置 `TONGSHU_ALLOW_ZIWEI_STUB=1` 时才返回 stub-with-error。

### `src/tongshu/engines/ziwei_adapter.py`

- `solar_to_chart()` 将阳历 `bySolar` 结果同步写入顶层：
  - `palaces`
  - `soul_earthly_branch`
  - `body_earthly_branch`
  - `fiveElementsClass`
  - `birth_year`
  - `gender`
- 保留 `palace_data` 兼容字段。
- 保持既有主星 pinyin 映射、辅星中文保留、`source='iztro'` 和时间索引政策。

### `tests/test_ziwei_chart_contract.py`

新增覆盖：

- 旧版嵌套结构 `from_dict()` 兼容和 `to_dict()` 往返。
- `ZiweiEngine.compute()` 顶层 12 宫、命身宫、宫干、飞化合同。
- `full_chart()` 与 `compute()` 结构一致性。
- `ZiweiSolarAdapter.compute()` 顶层结构。
- `ZiweiEvidenceProducer` 对真实宫位的消费。
- 真实 iztro、缺失 iztro fail-closed、显式 stub 三分支。
- 0 时、12 时、23 时和未知主星保留。

## 4. 验证结果

### 紫微定向回归

```text
250 passed, 32 subtests passed in 30.24s
```

覆盖命令集合：

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

### 真实运行结果

```text
source=iztro
ZiweiEngine.compute().palaces=12
ZiweiEngine.compute().palace_stems=12
ZiweiEngine.compute().soul_earthly_branch='午'
ZiweiEngine.compute().body_earthly_branch='辰'
ZiweiSolarAdapter.compute().palaces=12
ZiweiSolarAdapter.compute().palace_stems=12
```

### 环境门控

```text
真实 iztro：source=iztro                 PASS
iztro 缺失 + 未设置 stub：抛 ZiweiEngineUnavailableError PASS
iztro 缺失 + TONGSHU_ALLOW_ZIWEI_STUB=1：source=stub PASS
```

### 模块归属

```text
engine  = D:\shuntian\src\tongshu\engines\ziwei_engine.py
adapter = D:\shuntian\src\tongshu\engines\ziwei_adapter.py
package = D:\shuntian\src\tongshu\engines\ziwei\__init__.py
```

## 5. 非紫微失败与边界

额外执行的跨域 Pipeline 组合测试中有 4 项失败，但均不是本次紫微变更引起：

1. `tests/test_int_01_02_03_pipeline_wiring.py` 收集 `test_ziping_15_2_evidence_provenance.py` 时缺少 `tongshu.reasoning.judgment.CITATION`。
2. `tests/test_int_06_pipeline_integration.py` 的 3 项失败来自 `render_stage.py` 访问不存在的 `CrossDomainResult.status`。
3. 同一 Pipeline 测试日志还显示外部 LLM API 认证失败，随后触发上述 render fallback 错误。

这些问题属于 Ziping/Render/外部认证范围，本次没有修改。

工作区在本次任务开始前已经存在大量未提交、未跟踪和删除状态的非紫微文件；本次没有清理或覆盖这些既有变更。

## 6. 遗留问题

- `bySolar` 与 `byLunar` 的算法交叉验证仍需独立增强；本次只补齐结构合同。
- `palace_data` 与顶层 `palaces` 目前为兼容双写，后续可在 API 冻结后再决定是否移除旧字段。
- 紫微 Canonical 仍为 `BLOCKED`，本次修复不代表算法或流派规则已经治理冻结。
- 根级 `engines/`、历史规则包和审计资料的重复整理不在本次修复范围。

## 7. 变更白名单

本次实际新增/修改的目标文件：

```text
src/tongshu/engines/ziwei_engine.py
src/tongshu/engines/ziwei_adapter.py
tests/test_ziwei_chart_contract.py
docs/audit/ZIWEI_ENGINE_REPAIR_REPORT_20260928.md
```

未修改 Golden、数据库、冻结治理文件、八字、子平、盲派或河洛算法。
