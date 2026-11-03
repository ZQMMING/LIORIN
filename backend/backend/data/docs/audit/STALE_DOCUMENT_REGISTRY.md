# 📜 STALE DOCUMENT REGISTRY — STEP 1 Audit

**审计日期**: 2026-08-31  
**审计者**: Claude (独立审计方)  
**Commit 基线**: aa35031 (STEP0-FREEZE-20260831-054019)  
**方法**: 文档声明 vs 实代码 / 文档 vs 文档 / 文档 vs 当前事实比对

> 本文件列出 STEP 1 审计中发现的所有**过期或不一致文档**。每条记录标明:文档位置、过期陈述、现实状况、严重度。**仅发现,不修复**。

---

## 文档清单索引

| # | 文档 | 主题 | 严重度 |
|---|---|---|---|
| S-01 | `src/tongshu/engines/strength_engine.py:3-7` | in-code docstring 列生产调用,实 7 处 import 全部 ORPHAN/SHADOW | STALE |
| S-02 | `docs/audit/STEP0_FREEZE_BASELINE.md` | 整个文档基于未展开 shell + 过时调用图 | STALE |
| S-03 | `docs/audit/P0_ISOLATION_PLAN.md` | 文件路径全错 + 遗漏 4/7 调用点 | **P1 (计划不可执行)** |
| S-04 | `docs/audit/INDEPENDENT_CODE_AUDIT_REPORT.md` | 文件路径全错 + 行号错位 | STALE |
| S-05 | `docs/T2_GEMINI_VERDICT.md` | "wang_score 已隔离"声明与代码不符 | **P0** |
| S-06 | `docs/T2_STRENGTH_ENGINE_AUDIT_VERDICT.md` | "wang_score 仅历史记录" 与代码不符 | **P0** |
| S-07 | `docs/T2_REFACTOR_PLAN.md` | migration 计划未实施,4 阶段均 ⏳ | STALE |
| S-08 | `docs/audit/STEP0_FREEZE_COMPLETE.md` | 自相矛盾(声称 PASS 同时承认失败) | **P1** |
| S-09 | `docs/audit/HERMES_DISPATCH_STEP1_*.md` (两份) | 声称 M2 14/16 通过,实际 23 失败 | **P1** |
| S-10 | `docs/ARCHITECTURE_V11.md` `V12.md` `V13_FINAL.md` `V1.1.md` | 均未提及 canonical/ 层 | STALE |
| S-11 | `docs/ARCHITECTURE_DECISION_RESULT.md:227` | 裁决 3 ✅ 但 `canonical_state_engine` 模块不存在 | STALE |
| S-12 | `docs/ARCHITECTURE_DECISION_RESULT.md:22,224` | 裁决 D ✅ 但 new Canonical Calculation Engine 未建 | STALE |
| S-13 | `docs/USER_DECISION_20260830.md` | 强度引擎相关决策已过时 | STALE |
| S-14 | `docs/P0_TAKEOVER_AUDIT_20260830.md` | takeover 决策反映旧状态 | STALE |
| S-15 | `docs/PROJECT_STATUS_SNAPSHOT.md` | 自承"FROZEN ≠ PROVEN CORRECT" | acknowledged STALE |
| S-16 | `p0_8_10/M3_PHASE2_*.md` (12 份) | "14/16 测试通过"基于 mock dict 模式 | STALE |
| S-17 | `docs/P0_2_LEGACY_STRENGTH_ENGINE_CALL_GRAPH_AUDIT.md` | "legacy 已隔离不影响生产" 与 /admin HTTP 现实不符 | **P0** |
| S-18 | `docs/P0_2_LEGACY_STRENGTH_ENGINE_MIGRATION_PLAN.md` | 4 阶段均未实施 | STALE |
| S-19 | `docs/P0_2_1_4_JUDGMENT_ENGINE_TRACE.md:230` | "judgment_engine 不是生产污染源" 结论矛盾 | STALE |
| S-20 | `docs/P0_2_1_5_BAZI_ENGINE_TRACE.md:170` | 同上 | STALE |
| S-21 | `tests/test_strength_engine.py:80-88` docstring | 注释自承"构造难以精确控制" | acknowledged |
| S-22 | `tests/test_p2_direction_golden.py:1-8` docstring | "Golden 一致性" 与代码行为不符 | STALE |
| S-23 | `src/tongshu/canonical/producer.py:6` | "迁移方向: ... 改为消费 CanonicalState" 未实施 | STALE |
| S-24 | `src/tongshu/api/app.py:7-8,527` `api/nfc.py:1` `api/tracing.py:37-84` | DEPRECATED 注释 sunset 2027-08-18 | STALE (待 sunset) |
| S-25 | `tests/test_strength_engine.py:5-7` | LEGACY/DEPRECATED_IN_PROGRESS 注释 | STALE |
| S-26 | `tests/conftest.py:16` | `os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")` 默认开 stub | acknowledged |

---

## S-01 — strength_engine.py:3-7 in-code docstring

**文档陈述**:
```python
"""
⚠️ LEGACY ENGINE

【状态】LEGACY / DEPRECATED_IN_PROGRESS
【生产调用】annual_event_evaluator.py:207 | health_signals.py:99 | judgment_engine.py:41(类型)
"""
```

**过期理由**:
- "生产调用"仅列 3 处,实为 7 处(annual_event_evaluator.py:207 / judgment_engine.py:41 类型 / health_signals.py:99 / event_topic.py:445 / engine_adapters.py:42+45 / environmental_fit.py:39+294 / systems.py:646+651)
- "DEPRECATED_IN_PROGRESS" 与 `__all__` 仍 export 4 个 public 名字矛盾
- 无 DeprecationWarning,无 feature flag,无 import gate

**严重度**: STALE (源错误,传播至 docs/audit/STEP0_FREEZE_BASELINE.md 等)

---

## S-02 — STEP0_FREEZE_BASELINE.md 整体过期

**文档陈述**:
- :5 "Tag: STEP0-FREEZE-**YYYYMMDD-HHMMSS**" 占位符未替换
- :22 "生产调用路径: annual_event_evaluator.py:37, judgment_engine.py:41"
- :32-35 指标表含字面 `$(cat ...)` 未展开

**过期理由**:
- 真实 tag 是 `STEP0-FREEZE-20260831-054019` (在 `STEP0_FREEZE_COMPLETE.md:6`)
- 真实生产调用是 7 处(见 S-01)
- 真实 baseline 是 23F/1772P/9 dirty/5 untracked

**严重度**: STALE (整个文档没有可执行的事实)

---

## S-03 — P0_ISOLATION_PLAN.md 不可执行

**文档陈述**:
- :11-19 文件路径声称在 `canonical/`,实际在 `engines/` 和 `reasoning/`
- 调用链图仅列 3 个调用点

**过期理由**:
- `strength_engine.py` → `src/tongshu/engines/strength_engine.py` (不是 canonical/)
- `annual_event_evaluator.py:37` → `src/tongshu/engines/annual_event_evaluator.py`
- `judgment_engine.py:41` → `src/tongshu/engines/judgment_engine.py`
- `health_signals.py:99` → `src/tongshu/reasoning/health_signals.py`

**严重度**: **P1 (计划可执行性 = 0)** — 计划若被执行,无法定位任何文件

---

## S-04 — INDEPENDENT_CODE_AUDIT_REPORT.md 文件路径全错

**文档陈述** (line 24-26):
- `src/tongshu/annual_event_evaluator.py:207`
- `src/tongshu/health_signals.py:99`
- `src/tongshu/judgment_engine.py:41`

**过期理由**: 真实路径是 `src/tongshu/engines/annual_event_evaluator.py:207`、`src/tongshu/reasoning/health_signals.py:99`、`src/tongshu/engines/judgment_engine.py:41`

**严重度**: STALE (证据不可验证)

---

## S-05 — T2_GEMINI_VERDICT.md "wang_score 已隔离"

**文档陈述** (line 41):
> "旧 wang_score 最终授权 🟢 **已隔离**"

**过期理由**:
- `src/tongshu/engines/strength_engine.py:75,396` wang_score 仍激活
- `evaluate_strength_features` 是死代码,生产 0 调用
- `engine_adapters.py:45,57-63` 通过 `/admin` HTTP 仍可达

**严重度**: **P0** (最危险的过期声明)

---

## S-06 — T2_STRENGTH_ENGINE_AUDIT_VERDICT.md "wang_score 仅历史记录"

**文档陈述** (line 37, 45, 56):
> "wang_score 仅历史记录 — 不参与新判定"
> "D1FeatureResult + evaluate_strength_features() provide the clean layer"

**过期理由**:
- wang_score 仍决定 verdict (line 396)
- evaluate_strength_features 是死代码

**严重度**: **P0** (误导决策方)

---

## S-07 — T2_REFACTOR_PLAN.md migration 计划未实施

**文档陈述** (line 3):
> "目标: 禁止 wang_score/verdict 进入生产 Judgment,改用 CanonicalState / Feature Evidence"

**过期理由**:
- 计划 4 阶段均未实施:`ClimateExtractor` / `SupportCounter` / `DrainCounter` / `evaluate_health_signals_from_canonical` / `TenGodDynamicJudge` / `BaziScorer.compute_from_canonical` 全部 ⏳
- 验收标准:`judgment(chart, d1_result: D1StrengthResult)` 签名未改,Stage 4 移到 `legacy/` 未做

**严重度**: STALE (计划 → 现实 = 0% 完成)

---

## S-08 — STEP0_FREEZE_COMPLETE.md 自相矛盾

**文档陈述**:
- :69 GATE 表 "✅ PASS(已记录)"
- :31 "结果: 测试失败(需查看具体日志)"

**过期理由**: `pytest-baseline-20260831-054019.log` last line `23 failed, 1772 passed`

**严重度**: **P1** (同文档内矛盾,GATE 表 ✅ PASS 但有 23 失败)

---

## S-09 — HERMES_DISPATCH_STEP1_*.md 进度乐观

**文档陈述** (两份 dispatch 同 Task ID):
- :72-73 "M2资产验证进度: 14/16 (87.5%)"
- :73 "DayYearRelation✅ Root✅"

**过期理由**:
- pytest 实测 **23 例失败**,其中 **20 例是 M2 asset 测试**
- 失败包括:`TestDayYearRelationEvaluator::test_year_keeps_day_true`、`test_day_year_missing`、`TestM2Asset_FullIntegration` 岁君 cases

**严重度**: **P1** (调度方对进度的乐观声明与测试实况严重不符)

---

## S-10 — ARCHITECTURE V11/V12/V13/1.1 缺失 canonical/

**文档陈述**:
- `docs/ARCHITECTURE_V11.md`、`V12.md`、`V13_FINAL.md`、`V1.1.md` 均未提及 `canonical/state.py`、`condition_evaluator.py`、`composer.py`
- 仅 `V12.md:26` 提及 `signal/canonical_signal.py`

**过期理由**: canonical/ 包是 STEP 1 才发现的"未知架构层",与四份 ARCHITECTURE 文档均未对齐

**严重度**: STALE

---

## S-11 — ARCHITECTURE_DECISION_RESULT.md:227 裁决 3 ✅

**文档陈述** (line 227):
> 裁决 3: "canonical_state + canonical_state_engine" 模块布局 ✅

**过期理由**:
- `find src -name "*canonical_state*"` → **无结果**
- 无 `canonical_state_engine.py`

**严重度**: STALE

---

## S-12 — ARCHITECTURE_DECISION_RESULT.md:22,224 裁决 D ✅

**文档陈述** (line 22, 224):
> 裁决 D: new independent Canonical Calculation Engine; old engine = Legacy Reference ✅

**过期理由**: 无 Canonical Calculation Engine 模块,只有 `canonical/state.py` 数据结构 + `producer.py` 算法

**严重度**: STALE

---

## S-13 — USER_DECISION_20260830.md

**文档陈述**: 强度引擎相关决策(声称冻结 / 待迁移)

**过期理由**: 反映 2026-08-30 状态,wang_score 仍激活

**严重度**: STALE

---

## S-14 — P0_TAKEOVER_AUDIT_20260830.md

**文档陈述**: takeover 决策

**过期理由**: 反映旧状态,P0 隔离计划 S-03 路径错误

**严重度**: STALE

---

## S-15 — PROJECT_STATUS_SNAPSHOT.md 自承 FROZEN ≠ PROVEN

**文档陈述** (line 17, 68):
> "FROZEN ≠ PROVEN CORRECT"

**过期理由**: 文档自承认,标记 ⏳ 但未提供解法

**严重度**: acknowledged STALE

---

## S-16 — p0_8_10/M3_PHASE2_*.md (12 份)

**文档陈述**:
- "14/16 测试通过" (87.5%)

**过期理由**: 基于 mock dict 模式 (`ten_gods_distribution={"YIN_XING": 1}` 等字面),无法验证生产行为

**严重度**: STALE

---

## S-17 — P0_2_LEGACY_STRENGTH_ENGINE_CALL_GRAPH_AUDIT.md "legacy 已隔离"

**文档陈述** (line 60-73):
> "legacy/assertion_v1/... ✅ 已隔离,不影响生产路径"

**过期理由**:
- `POST /admin/cases/compute` (admin/router.py:85) → `admin/service.py:73,108` → `legacy/assertion_v1/engine_adapters.py:42-45` → `strength_engine.py:396`
- `api/app.py:589-590` `include_router(admin_router)` 无 feature flag

**严重度**: **P0** (错误乐观声明,实际 HTTP 可达)

---

## S-18 — P0_2_LEGACY_STRENGTH_ENGINE_MIGRATION_PLAN.md

**文档陈述**: 4 阶段迁移计划(45-188 行)

**过期理由**: 
- Stage 1: `ClimateExtractor` / `SupportCounter` / `DrainCounter` — 0 处实现
- Stage 2: `evaluate_health_signals_from_canonical` — 0 处
- Stage 3: `TenGodDynamicJudge` / `BaziScorer.compute_from_canonical` — 0 处
- Stage 4: judgment_engine 签名迁移 / strength_engine 移至 legacy — 未做

**严重度**: STALE (计划阶段停滞 ⏳)

---

## S-19 — P0_2_1_4_JUDGMENT_ENGINE_TRACE.md:230

**文档陈述**:
> "strength_engine.py 和 judgment_engine.py 都不是生产污染源 ... 只被 Legacy/孤立模块引用"

**过期理由**:
- judgment_engine 实际是 ORPHAN(judgment() 无 src 调用方)
- strength_engine 通过 `/admin` HTTP 是**真正的生产污染源**(见 S-17)
- 结论方向性对 judgment_engine,对 strength_engine 错

**严重度**: STALE (方向部分对,结论部分错)

---

## S-20 — P0_2_1_5_BAZI_ENGINE_TRACE.md:170

**文档陈述**: 同 S-19

**过期理由**: 同 S-19

**严重度**: STALE

---

## S-21 — tests/test_strength_engine.py:80-88 docstring

**文档陈述**:
> "从强格: 只有全局无异党时才允许标注"

**过期理由**: 注释自承"构造难以精确控制",且 `assertIn` 模式使 6 verdict 全过

**严重度**: acknowledged

---

## S-22 — tests/test_p2_direction_golden.py:1-8 docstring

**文档陈述**:
> "判定引擎输出的 favorable/unfavorable 方向需与 Golden 数据集中的历史事件一致"

**过期理由**:
- `self.golden_data = json.loads(...)` 加载后从不读取
- 实际断言 `len(favorable_elements) > 0` 不与 golden 对齐

**严重度**: STALE

---

## S-23 — canonical/producer.py:6 注释

**文档陈述**:
> "迁移方向: health_signals.py / annual_event_evaluator.py 改为消费 CanonicalState"

**过期理由**: 未实施

**严重度**: STALE

---

## S-24 — DEPRECATED routes 标记

**文档陈述**:
- `src/tongshu/api/app.py:7-8, 527` "POST /api/reading — DEPRECATED alias of /v1/daily-guide (Sunset 2027-08-18)"
- `src/tongshu/api/nfc.py:1` 模块标记 DEPRECATED in V1
- `src/tongshu/api/tracing.py:37-84` 跟踪 `_DEPRECATED_COUNTS`

**过期理由**: Sunset 2027-08-18 是未来时间,目前仍在使用

**严重度**: STALE (待 sunset)

---

## S-25 — tests/test_strength_engine.py:5-7 LEGACY 注释

**文档陈述**: "LEGACY ENGINE / DEPRECATED_IN_PROGRESS" — 与 `__all__` 仍 export 矛盾

**过期理由**: 同 S-01

**严重度**: STALE

---

## S-26 — tests/conftest.py:16 默认开 stub

**文档陈述**:
```python
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")
```

**过期理由**: 生产默认 fail-closed 但测试全局开 stub,测试口径与生产不一致

**严重度**: acknowledged

---

## 过期文档统计

| 严重度 | 数量 |
|---|---|
| **P0** | 3 (S-05, S-06, S-17) |
| **P1** | 3 (S-03, S-08, S-09) |
| **STALE / acknowledged** | 20 |

**总过期文档数**: 26

**说明**: 
- **最危险的过期文档**: S-05 / S-06 / S-17——"wang_score 已隔离" / "wang_score 仅历史记录" / "legacy 已隔离" 三份文件同时被生产现实证伪,而这正是 P0 隔离决策的依据
- **计划不可执行**: S-03 (P0_ISOLATION_PLAN) 路径错误,如按计划修复会修错文件
- **自承文档**: S-15 / S-21 / S-26 (FROZEN ≠ PROVEN CORRECT / 难以精确控制 / 默认开 stub) 这三类已自承风险,但未提供解法

---

**审计完成时间**: 2026-08-31  
**审计原则**: 只发现不修复,所有过期声明均可在指定文件:行复核