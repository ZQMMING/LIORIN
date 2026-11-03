# 静态代码审计报告

**项目**: D:/TODAY/backend (TONGSHU reasoning pipeline v1.0)
**审计日期**: 2026-08-27
**审计范围**: `src/tongshu/` 全模块 + `data/rules/*.json` 规则库
**审计方式**: 只读静态分析（无运行测试）

---

## 1. 模块引用 / Import 审计

### 1.1 结论：未发现断模块引用

所有 `import` 语句均指向已存在的模块或子模块：

| 导入路径 | 状态 |
|---|---|
| `tongshu.engines.bazi_engine` | ✅ 存在 (`BaziEngine`, `BaziChart`) |
| `tongshu.engines.ziwei_engine` | ✅ 存在 (`ZiweiEngine`, `ZiweiChart`) |
| `tongshu.engines.huangli_engine` | ✅ 存在 (`HuangliEngine`, `HuangliDay`) |
| `tongshu.engines.time_resolver` | ✅ 存在 (shim 重导出自 `engines/time/`) |
| `tongshu.engines.annual_event_evaluator` | ✅ 存在 (`HeluoScorer`, `YiScorer`) |
| `tongshu.engines.blind_bazi_engine` | ✅ 存在 (`BlindBazeEngine`) |
| `tongshu.engines.heluo` | ✅ 存在 (包路径，`heluo_calculate` 等) |
| `tongshu.engines.strength_engine` | ✅ 存在 (`evaluate_strength`, `_hidden_stems`, `D1StrengthResult`) |
| `tongshu.reasoning.event_topic` | ✅ 存在 (`EventTopicEngine`) |
| `tongshu.reasoning.signal_engine` | ✅ 存在 (`SignalEngine`) |
| `tongshu.db.dao` | ✅ 存在 (直接子模块导入，不经 `__init__.py`) |

`pipeline.py:326` 的 `from .db import dao` 属于直接子模块引用，Python 允许，不依赖 `__init__.py` 导出。

---

## 2. 架构违规审计 — EVENT_TOPIC 操作符

### 2.1 结论：规则层正确，未发现违规

EVENT_TOPIC 层专用操作符（`has`, `has_any`, `has_all`, `present`, `absent`）**仅出现于** `applies_to_layers: ["EVENT_TOPIC"]` 的规则中（共 21 条规则使用这些操作符），与 BASELINE / CYCLE_CONTEXT / DAILY_ACTIVATION 规则完全隔离。

**隔离机制确认**：

- `signal_engine.py:33` — `SIGNAL_LAYER_ORDER = ("BASELINE", "CYCLE_CONTEXT", "DAILY_ACTIVATION")`，EVENT_TOPIC 被明确排除在外
- `matcher.py:103-106` — EVENT_TOPIC 操作符列于 `OPS` 元组仅作静态验证用，`_eval_leaf` 对其显式 raise `UnknownOperatorError`
- `event_topic.py:357-387` — `EventTopicEngine.match()` 独立求值，不经过 `RuleMatcher`

规则层和数据层的架构设计一致，未发现跨层操作符混用。

---

## 3. 逻辑 Bug 审计

### [BUG-001] `event_topic.py:632-633` — 年支/日支五行查找错误（严重）

**文件**: `src/tongshu/reasoning/event_topic.py`
**行号**: 632–633
**严重程度**: 🔴 高 (High)
**类别**: 错误计算

**问题描述**:

```python
# 年支五行 vs 日支五行（冲克关系）
year_branch_el = STEM_ELEMENT.get(_HEAVENLY_STEMS[stem_idx % 10], 'unknown')
day_branch_el = STEM_ELEMENT.get(_HEAVENLY_STEMS[day_stem_idx % 10], 'unknown')
```

- `_HEAVENLY_STEMS` 包含的是**天干**（JIA, YI, BING...），不是地支
- `stem_idx` 是流年天干在 `_HEAVENLY_STEMS` 中的索引（0-9）
- `STEM_ELEMENT[_HEAVENLY_STEMS[stem_idx % 10]]` 得到的是**流年天干**的五行，而非流年**地支**的五行
- 正确做法：应使用 `_branch_element(year_branch)` 函数（该文件已有定义）获取地支五行

**影响**: `evaluate_year_event_topic()` 返回的 `marriage_score` 和 `health_score` 中，"年支五行 vs 日支五行冲克" 因子的计算结果始终错误（几乎总是 `'unknown'` 元素，查不到克制关系）。

**建议修复**:

```python
# 年支五行 vs 日支五行（冲克关系）
year_branch_el = _branch_element(year_branch)   # 使用已有的 _branch_element()
day_branch_el = _branch_element(chart.day_pillar.earthly_branch)
if CONTROLS.get(year_branch_el) == day_branch_el or CONTROLS.get(day_branch_el) == year_branch_el:
    health_score += 1.0
    marriage_score += 0.5
```

---

### [BUG-002] `judgment_engine.py:56-59, 65, 82` — 一致的拼写错误 `COMpanion`（低）

**文件**: `src/tongshu/engines/judgment_engine.py`
**行号**: 56–59, 65, 82
**严重程度**: 🟡 低 (Low)
**类别**: 命名一致性

**问题描述**:

常量 `COMpanion`（小写 'p'）在 `_XIJI_MAP`、`_TEN_GOD_ELEMENT` 和比较逻辑中一致使用，不影响运行（内部一致），但与标准命名规范不符（应为 `COMPANION`）。

由于代码库中没有其他地方引用 `COMPANION` 或 `COMPanion`，此问题不造成运行时错误，但影响代码可读性和后续维护。

**建议修复**: 将所有 `COMpanion` 统一改为 `COMPANION`。

---

### [BUG-003] `annual_event_evaluator.py:32` — 脆弱的 `sys.path` 相对路径（低）

**文件**: `src/tongshu/engines/annual_event_evaluator.py`
**行号**: 32
**严重程度**: 🟡 低 (Low)
**类别**: 环境依赖

**问题描述**:

```python
sys.path.insert(0, 'src')
```

使用硬编码相对路径 `'src'` 假设运行目录为 `backend/`。若从其他目录调用（如 `python -m tongshu.engines.annual_event_evaluator`），此路径将失效。

同类问题出现在另外 4 个文件（`services/daily_state_service.py:15`, `audit_validation/gates/g3_safety.py:51`, `v_validation/end_to_end.py:16`, `evaluation/l2_direction.py:23`），均为开发/测试脚本。

**建议修复**: 使用 `Path(__file__).parent.parent` 构建绝对路径，或依赖 `pyproject.toml` 的 `src/` 布局而非 `sys.path` 篡改。

---

## 4. 未实现 / 未定义引用审计

### 4.1 结论：未发现对未实现引擎或字段的悬空引用

**RuleLoader 的 Postgres backend**：
- `_rule_backends.py:130-144` 的 `_PostgresRuleBackend` 显式 `raise NotImplementedError`，但默认 `source="json"`，生产路径不触发。
- `_kb_backends.py` 的 `_PostgresKbBackend` 同理。

**Golden runner 的废弃方法**：
- `golden/runner.py:334` — `raise NotImplementedError("T601 removed synthetic SIR construction.")` 为已知移除的方法，文档注释说明不会被调用。

**iztro (紫微斗数) 依赖**：
- `ziwei_engine.py:107-134` — 当 `iztro` Node 模块不可用时，显式抛出 `ZiweiEngineUnavailableError`（默认行为），不由未定义引用导致。
- 环境变量 `TONGSHU_ALLOW_ZIWEI_STUB=1` 可启用降级 stub。

**EventTopicEngine 与主 pipeline 的集成状态**：
- `FlowYearAssertionProducer`（`assertion/flow_year.py`）独立创建 `EventTopicEngine` 实例（line 78），不经过 `TONGSHUPipeline` 或 `ComputeStage`
- 主 pipeline（`pipeline.py`）的 `run()` 路径**不调用** `EventTopicEngine`， EVENT_TOPIC 规则仅通过 `AssertionEngine` 的独立断言路径求值
- 这是架构设计选择（`assertion/` 是独立于 `pipeline/` 的契约层），不是 bug，但意味着主 pipeline 的人生指南输出不包含 EVENT_TOPIC 信号

---

## 5. 其他观察

### 5.1 `spec/signal_layers.py` 与实际规则体系不完全对齐

`SIGNAL_LAYERS = ("BASELINE", "CYCLE_CONTEXT", "DAILY_ACTIVATION")` 不包含 `EVENT_TOPIC`，但：
- `EventTopicSignal` 是独立于 `Signal` 的数据类，不经过 `Signal.__post_init__` 验证
- 规则中 `applies_to_layers: ["EVENT_TOPIC"]` 由 `EventTopicEngine` 独立处理

这是架构设计意图，但 `spec/signal_layers.py` 注释称 "Three layers MUST be preserved independently"，实际有四个 layer（加 EVENT_TOPIC），文档应同步更新。

### 5.2 `pipeline_stages/` 模块划分清晰

阶段拆分（Compute → Render → Validation → Audit）符合架构文档所述的 C2-C5 迁移计划，未发现跨阶段引用错误。

---

## 6. 汇总

| ID | 文件:行号 | 问题 | 严重程度 |
|---|---|---|---|
| BUG-001 | `reasoning/event_topic.py:632-633` | 年支/日支五行查找用错天干索引 | 🔴 高 |
| BUG-002 | `engines/judgment_engine.py:56-59,65,82` | `COMpanion` 拼写一致错误 | 🟡 低 |
| BUG-003 | `engines/annual_event_evaluator.py:32` | 硬编码 `sys.path.insert(0, 'src')` 脆弱 | 🟡 低 |
| OBS-001 | `spec/signal_layers.py` | `SIGNAL_LAYERS` 缺 EVENT_TOPIC（与实际 4 层不符） | 🟢 观察 |
| OBS-002 | `TONGSHUPipeline` | `EventTopicEngine` 未接入主 pipeline | 🟢 观察 |

**需要优先修复**: BUG-001（影响流年健康/婚姻评分准确性）
