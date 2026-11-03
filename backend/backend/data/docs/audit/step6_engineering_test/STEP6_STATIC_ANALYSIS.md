# STEP6_STATIC_ANALYSIS.md — strength_engine.py / wang_score 生产路径静态分析

> 审计日期: 2026-08-31
> 审计者: OpenCode (TASK-006)
> 基线: baseline-v1.4-interim-20260823

---

## 1. evaluate_strength 调用图取证

### 1.1 src/ 生产代码中的直接调用点

| 文件 | 行号 | 代码 | 状态 |
|------|------|------|------|
| `engines/annual_event_evaluator.py` | 37 | `from ...strength_engine import evaluate_strength` | DEPRECATED stub |
| `engines/annual_event_evaluator.py` | 211 | `strength = evaluate_strength(chart)` | 退回 UNRESOLVED |
| `reasoning/health_signals.py` | 19 | `from ...strength_engine import ..., evaluate_strength` | DEPRECATED stub |
| `reasoning/health_signals.py` | 106 | `d1: D1StrengthResult = evaluate_strength(chart)` | 退回 UNRESOLVED |
| `reasoning/event_topic.py` | 443 | `from ...strength_engine import evaluate_strength, _hidden_stems` | DEPRECATED stub |
| `reasoning/event_topic.py` | 446 | `d1 = evaluate_strength(chart)` | 退回 UNRESOLVED |
| `engines/judgment_engine.py` | 41 | `from ...strength_engine import D1StrengthResult` | 仅类型注解，无调用 |

### 1.2 生产入口链追踪

**生产入口**: `api/app.py` → `pipeline.run()` → `ComputeStage.run()`

```
pipeline.py (TONGSHUPipeline)
  └─ compute_stage.run()
       ├─ BaziEngine.compute()           # 干支计算
       ├─ ZiweiEngine.compute()          # 紫微排盘
       ├─ SignalEngine.run()             # 规则匹配
       ├─ CrossAnalyzer.analyze()        # 跨系统分析
       └─ CanonicalComposer.compose()   # SIR 构造
```

**结论**: `annual_event_evaluator.py`、`health_signals.py`、`event_topic.py` **均不在** 生产入口链上。三重取证（调用图 + 生产入口链 + 测试对象）确认：

- 调用图: 以上三个模块在 `src/tongshu/` 非 legacy 路径下零生产调用方
- 生产入口链: `pipeline.py` / `pipeline_stages/compute_stage.py` / `api/app.py` / `services/` 无一引用这些模块
- evaluate_strength() 已退回 UNRESOLVED stub，返回值 verdict=""、所有特征字段为零值

### 1.3 evaluate_strength_features 生产状态

`evaluate_strength_features()` (line 293) 是推荐入口，返回 `D1FeatureResult`（无 verdict）。**同样无生产调用方**——当前 pipeline 路径不依赖 D1 旺衰计算，改用 FiveClassics Corpus Primitive 规则做辨证。

### 1.4 测试路径调用（非生产）

| 测试文件 | 调用方式 |
|----------|----------|
| `tests/test_strength_engine.py` | 直接调用 evaluate_strength() 验证 stub 行为 |
| `tests/test_strength_engine_yinyang.py` | 同上 |
| `tests/test_judgment_engine.py` | 兼容性测试 |
| `tests/test_new_engines.py:153` | 兼容性测试 |
| `tests/test_p2_direction_golden.py` | 兼容性测试 |
| `tests/test_environmental_fit.py` | 注释说明 stub 行为 |

---

## 2. wang_score / _WANG_SCORE_THRESHOLD 生产路径分析

### 2.1 常量状态

```python
# strength_engine.py:76-78
# 【TASK-003】wang_score 阈值判定已移除。
# _WANG_SCORE_THRESHOLD 不再参与任何判定逻辑，仅保留作为 RESEARCH 参考数字。
# _WANG_SCORE_THRESHOLD = 2.0    ← 已注释掉，从未激活
```

### 2.2 wang_score 字段使用分析

| 位置 | 用途 | 生产路径影响 |
|------|------|-------------|
| `D1StrengthResult.wang_score` (line 150) | 数据结构字段 | stub 返回 0.0，无决策影响 |
| `D1FeatureResult.wang_score` (line 288) | 数据结构字段 | 记录用，不参与推断 |
| `evaluate_strength_features()` (lines 375-383) | 计算并记录 | 仅记录，不做阈值比较 |
| `infer_verdict()` (line 406) | 推导结论 | **不依赖 wang_score**，仅用 de_ling/de_di/support/drain |

### 2.3 全仓库 grep 验证

```bash
grep -rn "wang_score\|_WANG_SCORE_THRESHOLD" src/ --include="*.py" | grep -v strength_engine.py
# 结果: 无输出 (零外部引用)
```

**结论**: `_WANG_SCORE_THRESHOLD` 从未在代码中激活；`wang_score` 仅作为 RESEARCH 参考特征存在，**无任何生产路径阈值判定**。

---

## 3. 验收确认

| 验收项 | 状态 | 证据 |
|--------|------|------|
| 无 evaluate_strength 生产调用 | ✅ PASS | 三重取证: annual_event_evaluator/health_signals/event_topic 均零生产调用方 |
| 无 wang_score 阈值在生产路径 | ✅ PASS | _WANG_SCORE_THRESHOLD 已注释；grep 全仓库零外部引用 |
| evaluate_strength_features 隔离 | ✅ PASS | 返回 D1FeatureResult（无 verdict），不在 pipeline 路径中 |

---

## 4. 附录：生产路径调用链完整图

```
api/app.py
  └─ TONGSHUPipeline.run()
       └─ ComputeStage.run()
            ├─ BaziEngine.compute()
            ├─ ZiweiEngine.compute()
            ├─ SignalEngine.run()           ← 规则匹配层
            ├─ CrossAnalyzer.analyze()
            └─ CanonicalComposer.compose()
                  └─ AssertionEngine.run()   ← 断言层
                       ├─ ZiweiAssertionProducer
                       ├─ BlindAssertionProducer
                       ├─ HeluoAssertionProducer
                       ├─ CareerAssertionProducer
                       ├─ WealthAssertionProducer
                       ├─ MarriageAssertionProducer
                       ├─ HealthAssertionProducer
                       └─ MizhuAssertionProducer
                       (无 FlowYearAssertionProducer 注册)

注: annual_event_evaluator / health_signals / event_topic
   均在 legacy/assertion_v1/ 或 testing 路径下，
   生产入口链零引用。
```
