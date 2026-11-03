# STEP 1 Claude 独立审计 — 当前系统状态快照

**审计日期**: 2026-08-31
**审计方**: Claude (独立审计方)
**Commit 基线**: aa35031 (STEP 0 已冻结)
**Tag**: STEP0-FREEZE-20260831-054019
**方法**: 静态代码分析 + 调用图追溯 + 文档对照 (无任何修改)

---

## 1. P0 隔离计划声明 vs 实际代码状态

### 1.1 P0 隔离计划 (P0_ISOLATION_PLAN.md) 的核心声明

| # | 声明 | 实际状态 | 一致性 |
|---|------|---------|--------|
| 1 | `strength_engine.py` 在 `src/tongshu/canonical/` | **实际在 `src/tongshu/engines/`** | ❌ **WRONG PATH** |
| 2 | 调用链: `strength_engine.py → annual_event_evaluator.py:37 → judgment_engine.py:41 → health_signals.py:99` | judgment_engine.py:41 只是 **import type** (`D1StrengthResult`), 并非函数调用 | ❌ **PARTIAL** |
| 3 | wang_score 必须从 production verdict chain 移除 | **wang_score 仍在 `strength_engine.py:396` 直接决定 `身强/身弱` verdict** | ❌ **CRITICAL** |
| 4 | `_WANG_SCORE_THRESHOLD = 2.0` 判定逻辑必须移除 | **line 75 仍定义, line 396 仍使用** | ❌ **CRITICAL** |
| 5 | `evaluate_strength_features` 作为新 V4 隔离层 | **定义了但 src/ 中 0 处调用, 仅 scripts/p0_3_9_real_integration.py 调用一次** | ❌ **DEAD CODE** |

### 1.2 P0 隔离计划所列文件路径全部错误

**P0 计划说**:
- `strength_engine.py` → canonical/
- `annual_event_evaluator.py:37` → canonical/
- `judgment_engine.py:41` → canonical/
- `health_signals.py:99` → canonical/

**实际位置**:
- `src/tongshu/engines/strength_engine.py`
- `src/tongshu/engines/annual_event_evaluator.py`
- `src/tongshu/engines/judgment_engine.py`
- `src/tongshu/reasoning/health_signals.py`

**含义**: P0 隔离计划本身是基于错误信息制定的。如果按计划执行隔离, 将无法找到任何文件。这表明隔离计划在制定前**未做基本的代码定位验证**。

---

## 2. strength_engine 生产调用路径 (REAL)

### 2.1 直接调用 `evaluate_strength()` 的位置 (7 处)

| # | 文件 | 行号 | 调用目的 | verdict 是否传播 |
|---|------|------|---------|------------------|
| 1 | `src/tongshu/engines/annual_event_evaluator.py` | 37 (import), 207 (call) | BaziScorer.compute() 中获取 verdict 传入灾劫/财运评分 | **YES** (传入 score_disaster/score_wealth) |
| 2 | `src/tongshu/engines/judgment_engine.py` | 41 (import), 371 (参数类型) | `judgment(chart, d1_result)` 接收 verdict 用于病药/喜忌判定 | **YES** (verdict → 喜忌反转 → 用神) |
| 3 | `src/tongshu/reasoning/health_signals.py` | 19 (import), 99 (call) | `evaluate_health_signals()` 中判定体用失衡 | **YES** (身弱+泄耗>生扶×1.3) |
| 4 | `src/tongshu/reasoning/event_topic.py` | 442 (import), 445 (call) | 事件主题识别 | YES |
| 5 | `src/tongshu/legacy/assertion_v1/engine_adapters.py` | 42, 45 | LEGACY 适配器 | YES |
| 6 | `src/tongshu/legacy/assertion_v1/environmental_fit.py` | 39, 294 | LEGACY 环境拟合 | YES |
| 7 | `src/tongshu/legacy/assertion_v1/systems.py` | 646, 651 | LEGACY 系统 | YES |

**注意**: P0 隔离计划只列了 3 个调用点, **实际有 7 个**。

### 2.2 间接通过 `D1StrengthResult` 传播 verdict 的位置

| 文件 | 行号 | 使用方式 | 影响 |
|------|------|---------|------|
| `src/tongshu/engines/judgment_engine.py` | 408 | `verdict_for_bingyao = verdict_raw` (line 411) | 病药层判定 |
| `src/tongshu/engines/judgment_engine.py` | 444 | `verdict = verdict_raw` | 喜忌层判定 |
| `src/tongshu/engines/annual_event_evaluator.py` | 131 | `v = "身强" if "从强" in v else "身弱"` | 十神吉凶动态判断 |
| `src/tongshu/engines/annual_event_evaluator.py` | 159, 180 | `verdict` 参数默认值="身弱" | 流年评分 |
| `src/tongshu/reasoning/health_signals.py` | 144 | `d1.verdict == "身弱"` | 体用失衡判定 |
| `src/tongshu/reasoning/health_signals.py` | 149 | `旺衰={d1.verdict}` | 注解 |

---

## 3. wang_score 在 verdict chain 中的角色

### 3.1 计算来源
**唯一来源**: `src/tongshu/engines/strength_engine.py:75` 定义 `_WANG_SCORE_THRESHOLD = 2.0`
**计算位置**: `src/tongshu/engines/strength_engine.py:353-358`

```python
wang_score = (
    de_ling_weight * 1.5      # 1.5x 得令权重
    + de_di_weighted * 1.0    # 1.0x 通根质量
    + de_shi_effective * 0.8  # 0.8x 透干有效数
    + (support - drain) * 0.3 # 0.3x 生扶泄耗差
)
```

### 3.2 verdict 决定路径 (line 396)

```python
strong = wang_score >= _WANG_SCORE_THRESHOLD
verdict = "身强" if strong else "身弱"
```

**这是 P0 隔离的核心目标 — 至今未实现**。

### 3.3 从格判定中的 wang_score 使用 (line 367-393)
- 从强判定: `wang_score > 4.0` (line 367)
- 从弱判定: `wang_score < 1.5` (line 380)
- 假从强: 阳干 de_di<2 → 退回身强处理 (line 374)
- 假从弱: 阳干有印透 → 退回身弱处理 (line 388)

### 3.4 wang_score 的下游消费者 (无)

经过全 src/ 搜索:
- ✅ **未持久化到 DB/JSON** (data/ 仅一处 schema 引用, 无实例化)
- ✅ **未暴露给 API layer** (api/ 中无 wang_score 引用)
- ✅ **未传递到 admin layer** (admin/ 中无 wang_score 引用)
- ❌ **所有 verdict 都来自 evaluate_strength()** (经 strength_engine.py:396 决定)

---

## 4. V4 隔离层 (evaluate_strength_features) 状态

### 4.1 定义位置
- `src/tongshu/engines/strength_engine.py:449` — `D1FeatureResult` 类
- `src/tongshu/engines/strength_engine.py:476` — `evaluate_strength_features(chart)` 函数
- `src/tongshu/engines/strength_engine.py:589` — `infer_verdict(features)` 函数 (辅助)

### 4.2 实际调用点 (生产代码 0 处)
```
$ grep -rn "evaluate_strength_features\|D1FeatureResult" src/
src/tongshu/engines/strength_engine.py:445  # 定义注释
src/tongshu/engines/strength_engine.py:449  # 类定义
src/tongshu/engines/strength_engine.py:476  # 函数定义
src/tongshu/engines/strength_engine.py:558  # 内部注释
src/tongshu/engines/strength_engine.py:561  # 计算 wang_score
src/tongshu/engines/strength_engine.py:568  # return D1FeatureResult
src/tongshu/engines/strength_engine.py:583  # 赋值 wang_score
src/tongshu/engines/strength_engine.py:589  # infer_verdict 定义
src/tongshu/engines/strength_engine.py:590  # docstring
src/tongshu/engines/strength_engine.py:612  # __all__
src/tongshu/engines/strength_engine.py:614  # __all__
```

**结论**: `evaluate_strength_features` 是**死代码 (dead code)** — 仅在 `scripts/p0_3_9_real_integration.py:16, 156` (一次性验证脚本) 中调用。生产路径 (pipeline, services, api) **完全未集成**。

### 4.3 同时, evaluate_strength() 仍被作为默认函数

`strength_engine.py:610-616` 的 `__all__` 同时导出:
```python
__all__ = [
    "D1StrengthResult",      # 旧 (含 verdict)
    "D1FeatureResult",       # 新 (无 verdict)
    "evaluate_strength",     # 旧 (wang_score 阈值)
    "evaluate_strength_features",  # 新 (无 verdict)
    "infer_verdict",         # 新 (辅助, 也很少用)
]
```

**含义**: 命名约定 (新=features, 旧=standard) 暗示 V4 是过渡方案, 但迁移未完成。

---

## 5. 测试基线状态

### 5.1 Pytest 基线数字
- **总测试数**: 1795
- **通过**: 1772
- **失败**: **23** (详见 BLOCKER_REGISTRY.md)
- **跳过**: 5
- **xfail**: 9
- **xpass**: 10 (意外通过 — 通常是测试条件失效)

### 5.2 测试失败分布

**全部失败集中在两个区域**:

| 测试文件 | 失败数 | 失败模式 |
|---------|-------|---------|
| `tests/test_flow_year_assertion.py` | 3 | FileNotFoundError — 路径依赖 |
| `tests/test_m2_asset_complete_integration.py` | 2 | 集成断言失败 |
| `tests/test_m2_asset_enhanced_*.py` | 11 | TenGodMapper + RootEvaluator + 格局判定 |
| `tests/test_m2_asset_integration_v2.py` | 7 | DayYearRelation + 完整验证 |

### 5.3 测试真实性问题

**严重问题 — return-based 测试**:
`tests/test_p6c_3c2_permanent_negative.py` 中所有测试函数以 `return True` 结尾, 而非 assert。这导致 pytest 警告:
```
PytestReturnNotNoneWarning: Test functions should return None, but ... returned <class 'bool'>.
```
**风险**: 如果 assert 全部失败但函数末尾 return True, 测试仍报告通过。这是测试基础设施层面的真实性问题。

**更严重**: 测试用例日志显示这是**"已知失败但被掩盖"**的状态, pytest 已记录 baseline。

---

## 6. 文档 vs 代码一致性

### 6.1 文档声明的"DEPRECATED 但仍运行"状态

| 文档 | 声明 | 实际 |
|------|------|------|
| `docs/audit/STEP0_FREEZE_BASELINE.md` | "wang_score 阈值: 2.0" + "必须隔离" | 阈值仍生效 |
| `docs/audit/P0_ISOLATION_PLAN.md` | 列出 3 个调用点 | 实际 7 个 |
| `docs/audit/P0_ISOLATION_PLAN.md` | 文件路径在 `canonical/` | 实际在 `engines/` 和 `reasoning/` |
| `docs/ARCHITECTURE_V13_FINAL.md` | 五经辨证为唯一权威 | `evaluate_strength` 仍输出 verdict |

### 6.2 文档自相矛盾

**strength_engine.py 第 5 行的 docstring 自相矛盾**:
```python
【状态】LEGACY / DEPRECATED_IN_PROGRESS
【生产调用】annual_event_evaluator.py:207 | health_signals.py:99 | judgment_engine.py:41(类型)
```
**声明为 DEPRECATED, 但同时列生产调用路径** — 这是"声明与运行状态不一致"的典型。

### 6.3 ARCHITECTURE 文档未反映 reality

**ARCHITECTURE_V13_FINAL.md 等文档未提及**:
- `evaluate_strength` 仍输出 wang_score 阈值 verdict
- `judgment_engine.judgment()` 仍以 `d1_result.verdict` 为输入做病药/喜忌
- `evaluate_strength_features` 定义了但未集成

---

## 7. 结论 (Current Reality)

**P0 隔离的当前状态**:
1. ❌ **核心目标未达成**: `evaluate_strength` 仍是唯一生产调用, wang_score 阈值 verdict 仍生效
2. ❌ **V4 隔离层未集成**: `evaluate_strength_features` 是 dead code, 仅 1 个验证脚本调用
3. ❌ **P0 隔离计划本身有错误**: 文件路径全部错误, 调用点遗漏 4 个
4. ❌ **存在隐式 verdict 传播**: judgment_engine, annual_event_evaluator, health_signals 都依赖 D1StrengthResult.verdict
5. ⚠️ **测试基础设施问题**: `return True` 模式掩盖真实失败
6. ⚠️ **文档与代码不一致**: DEPRECATED 标注但仍生产运行

**P0 隔离需要的真实工作** (尚未开展):
1. 将 `evaluate_strength` 调用点全部替换为 `evaluate_strength_features`
2. 重构 judgment_engine 使其不基于 verdict, 而是基于 classical_states
3. 重构 annual_event_evaluator 使十神吉凶判断不基于 verdict
4. 重构 health_signals 使体用失衡不基于 verdict
5. 更新所有 ARCHITECTURE 文档
6. 修复测试真实性问题 (return-based 测试)

---

## 8. 审计产出物

本快照支撑以下四个产出物:
- `FULL_AUDIT_REPORT.md` — 12 域完整审计报告
- `CONFLICT_REGISTRY.md` — 所有冲突
- `STALE_DOCUMENT_REGISTRY.md` — 过期文档
- `BLOCKER_REGISTRY.md` — P0/P1 阻塞项

**审计方签名**: Claude (独立审计)
**审计时间**: 2026-08-31
**审计原则**: 只发现, 不修复