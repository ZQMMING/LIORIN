# ⚔️ CONFLICT REGISTRY — STEP 1 Audit

**审计日期**: 2026-08-31  
**审计者**: Claude (独立审计方)  
**Commit 基线**: aa35031 (STEP0-FREEZE-20260831-054019)  
**方法**: 调用图取证 + 实代码验证 + 文档声明对照

> 本文件列出 STEP 1 审计中发现的所有**冲突**——文档声明与代码现实不一致、声明与声明不一致、代码与代码不一致。**仅发现,不修复**。

---

## 冲突清单索引

| # | 冲突类型 | 冲突主题 | 严重度 |
|---|---|---|---|
| C-01 | 文档 vs 代码 | P0_ISOLATION_PLAN 文件路径错误 | **P1** |
| C-02 | 文档 vs 代码 | P0_ISOLATION_PLAN 调用点遗漏 4/7 | **P1** |
| C-03 | 文档 vs 代码 | wang_score 仍激活但被声称已隔离 | **P0** |
| C-04 | 文档 vs 代码 | evaluate_strength 7 处调用,文档仅列 3 处 | **P1** |
| C-05 | 文档 vs 代码 | evaluate_strength_features 是死代码,文档声称是隔离层 | **P2** |
| C-06 | 代码 vs 代码 | canonical/state.py 黑名单缺失 `wang_score` | **P0** |
| C-07 | 代码 vs 代码 | strength_engine.py 双 docstring + `from __future__` 失效 | **P2** |
| C-08 | 文档 vs 文档 | T2_GEMINI_VERDICT.md vs T2_STRENGTH_ENGINE_AUDIT_VERDICT.md | **P0** |
| C-09 | 文档 vs 代码 | STEP0_FREEZE_COMPLETE.md 自相矛盾(声称 PASS 实 23 失败) | **P1** |
| C-10 | 文档 vs 代码 | STEP0_FREEZE_BASELINE.md 含未展开 shell 占位符 | **P1** |
| C-11 | 文档 vs 代码 | HERMES_DISPATCH 声称 14/16 M2 通过,实 20/23 失败 | **P1** |
| C-12 | 文档 vs 代码 | ARCHITECTURE_DECISION_RESULT.md:227 ✅ 但模块不存在 | **P2** |
| C-13 | 代码 vs 代码 | canonical/composer.py 与 canonical/state.py 共用包名但无关 | **P2** |
| C-14 | 代码 vs 代码 | 两份 RootConditionEvaluator (v1+v2) 同命名冲突 | **P0** |
| C-15 | 代码 vs 代码 | BRANCH_HIDDEN_STEMS 表分裂(root vs reasoning) | **P0** |
| C-16 | 文档 vs 代码 | strength_engine.py:3-7 header 与 `__all__` 矛盾 | **P2** |
| C-17 | 文档 vs 代码 | `from tongshu.legacy.assertion_v1` 标"已隔离"但 `/admin` 仍 HTTP 可达 | **P0** |
| C-18 | 文档 vs 文档 | ARCHITECTURE V11/V12/V13/1.1 vs canonical/ 不对齐 | **P2** |
| C-19 | 文档 vs 代码 | P0-8.10 系列报告基于 mock dict 模式 (14/16 不实) | **P2** |
| C-20 | 文档 vs 代码 | condition_evaluator.evaluate() 收 Dict[str, Any] 而非 CanonicalState | **P2** |
| C-21 | 文档 vs 代码 | validate_token 桩 + lazy auth_gate | **P1** |
| C-22 | 文档 vs 代码 | Default DSN 含 `postgres:postgres` 字面量 | **P2** |
| C-23 | 文档 vs 代码 | sys.path.insert 多处硬编码绝对路径 | **P1** |
| C-24 | 文档 vs 代码 | _case_cache / _BUCKETS 限流器无限增长 | **P1** |
| C-25 | 文档 vs 代码 | daily_api stub 数据 / 桩 validate_token | **P2** |
| C-26 | 文档 vs 代码 | test_p6c_3c2_permanent_negative return True 模式 | **P1** |
| C-27 | 文档 vs 代码 | M2 asset / condition_evaluator 测试全部硬编码 dict | **P0** |
| C-28 | 文档 vs 代码 | yinyang 测试 6 字符串 assertIn | **P0** |
| C-29 | 文档 vs 代码 | p2_direction_golden 加载 golden 但不读 | **P1** |
| C-30 | 文档 vs 代码 | assertion producers 预制 pillars + chart={} | **P1** |

---

## C-01 — P0_ISOLATION_PLAN 文件路径错误

**冲突源**:
- `docs/audit/P0_ISOLATION_PLAN.md:11-19` 声称 strength_engine.py / annual_event_evaluator.py / judgment_engine.py / health_signals.py 在 `src/tongshu/canonical/`

**代码现实**:
- `src/tongshu/engines/strength_engine.py`
- `src/tongshu/engines/annual_event_evaluator.py`
- `src/tongshu/engines/judgment_engine.py`
- `src/tongshu/reasoning/health_signals.py`

**严重度**: **P1** (按计划执行修复 = 找不到文件)

**可执行性影响**: 计划可执行性 = 0。制定计划前未做基本文件定位验证。

---

## C-02 — P0_ISOLATION_PLAN 调用点遗漏 4/7

**冲突源**:
- `P0_ISOLATION_PLAN.md:11-19` 仅列 3 个调用点: `annual_event_evaluator.py:37`、`judgment_engine.py:41`、`health_signals.py:99`

**代码现实**:
- 实际 7 个 import/call 站点:
  1. `engines/annual_event_evaluator.py:37` (import), `:207` (call)
  2. `engines/judgment_engine.py:41` (type-only)
  3. `reasoning/health_signals.py:19` (import), `:99` (call)
  4. `reasoning/event_topic.py:442` (lazy import), `:445` (call)
  5. `legacy/assertion_v1/engine_adapters.py:42,45` (call via /admin)
  6. `legacy/assertion_v1/environmental_fit.py:39,294` (call)
  7. `legacy/assertion_v1/systems.py:646,651` (call)

**严重度**: **P1**

**可执行性影响**: 即使路径正确,按此计划修复也会遗漏 4 个调用点,其中 `engine_adapters.py:42,45` 是**唯一 HTTP 可达**的活路径。

---

## C-03 — wang_score 声称已隔离,实际仍激活

**冲突源**:
- `docs/T2_GEMINI_VERDICT.md:41` "旧 wang_score 最终授权 🟢 **已隔离**"
- `docs/T2_STRENGTH_ENGINE_AUDIT_VERDICT.md:37,45,56` "wang_score 仅历史记录 — 不参与新判定"

**代码现实**:
- `src/tongshu/engines/strength_engine.py:75` `_WANG_SCORE_THRESHOLD = 2.0` 仍定义
- `src/tongshu/engines/strength_engine.py:353-358` wang_score 计算公式仍激活
- `src/tongshu/engines/strength_engine.py:396` `strong = wang_score >= _WANG_SCORE_THRESHOLD` 仍判定 verdict
- `src/tongshu/engines/strength_engine.py:367,380` 从强/从弱判定仍依赖 `wang_score > 4.0` / `< 1.5`

**严重度**: **P0** (治理防御完全失效)

---

## C-04 — evaluate_strength 7 处调用,文档仅列 3 处

**冲突源**:
- `src/tongshu/engines/strength_engine.py:5` 注释 (原始错误源) 仅列 3 处
- `docs/audit/STEP0_FREEZE_BASELINE.md:22` 同上
- `docs/audit/HERMES_DISPATCH_STEP1_*.md:28` "特别关注 annual_event_evaluator.py, judgment_engine.py, health_signals.py"
- `docs/audit/P0_ISOLATION_PLAN.md:11-19` 仅 3 处

**代码现实**: 7 处调用(见 C-02)

**严重度**: **P1** (三重取证中"调用图取证"未涵盖全部)

---

## C-05 — evaluate_strength_features 是死代码,被宣传为隔离层

**冲突源**:
- `docs/T2_STRENGTH_ENGINE_AUDIT_VERDICT.md:11,14` "D1FeatureResult + evaluate_strength_features() provide the clean layer"
- `src/tongshu/engines/strength_engine.py:5` header 暗示 V4 隔离层

**代码现实**:
- `src/tongshu/engines/strength_engine.py:476` `evaluate_strength_features()` 定义
- `src/tongshu/engines/strength_engine.py:589` `infer_verdict()` 定义
- **生产代码 0 调用**——`grep -rn "evaluate_strength_features\|D1FeatureResult" src/` 仅命中 strength_engine.py 自引用
- **测试代码 0 调用**——grep 无命中
- **唯一调用**: `scripts/p0_3_9_real_integration.py:16, 156` (一次性验证脚本)

**严重度**: **P2** (宣传 vs 实际不一致)

---

## C-06 — canonical/state.py 黑名单缺失 wang_score

**冲突源 (代码 vs 代码)**:
- `src/tongshu/canonical/state.py:437` `validate()` 拒绝 `strength_score`/`root_score`/`wangshuai_score`/`qiangruo_score`
- `src/tongshu/engines/strength_engine.py:353-358` 计算出的字段名是 `wang_score`(而非 `wangshuai_score`)

**严重度**: **P0** (治理守卫完全失效——这是治理规则存在的核心目的)

**含义**: 即使有人在 metadata 中塞 `wang_score`,validate() 不会拒绝。封禁了不存在的字段名,放行了实际字段名。

---

## C-07 — strength_engine.py 双 docstring + `from __future__` 失效

**冲突源 (代码 vs 代码)**:
- `src/tongshu/engines/strength_engine.py:1-7` 第一个字符串字面量(LEGACY 声明)
- `src/tongshu/engines/strength_engine.py:8-32` 第二个字符串字面量(D1 契约规范)
- `src/tongshu/engines/strength_engine.py:2` 实际上 `from __future__ import annotations` 嵌在第一个字符串字面量内部,**不是 import 语句,字符串字面量**

**Python 语义**:
- 第一个字符串字面量是模块 `__doc__`
- 第二个是"死表达式语句"——执行但无效果
- `from __future__ import annotations` **不生效**——Python 模块的 postponed-annotation 在此模块静默失效

**严重度**: **P2** (类型注解可能与运行时不一致)

---

## C-08 — T2_GEMINI_VERDICT.md vs T2_STRENGTH_ENGINE_AUDIT_VERDICT.md

**冲突源 (文档 vs 文档)**:
- `docs/T2_GEMINI_VERDICT.md:41` "旧 wang_score 最终授权 🟢 **已隔离**"
- `docs/T2_REFACTOR_PLAN.md:3` "目标: 禁止 wang_score/verdict 进入生产 Judgment,改用 CanonicalState / Feature Evidence"

**代码现实**: wang_score 未隔离(见 C-03)

**严重度**: **P0** (两份权威文档对同一事实给出矛盾结论)

---

## C-09 — STEP0_FREEZE_COMPLETE.md 自相矛盾

**冲突源**:
- `docs/audit/STEP0_FREEZE_COMPLETE.md:69` "pytest reality ✅ PASS(已记录)"
- `docs/audit/STEP0_FREEZE_COMPLETE.md:31` "结果: 测试失败(需查看具体日志)"

**代码现实**: `pytest-baseline-20260831-054019.log` last line `23 failed, 1772 passed`

**严重度**: **P1** (同文档内矛盾,GATE 表 ✅ PASS 但有 23 失败)

---

## C-10 — STEP0_FREEZE_BASELINE.md 含未展开 shell

**冲突源**:
- `docs/audit/STEP0_FREEZE_BASELINE.md:32-35` 指标表内容是字面字符串: `$(cat dirty-files-manifest.txt | wc -l)`、`$(grep 'passed' pytest-baseline-*.log | tail -1)`
- `docs/audit/STEP0_FREEZE_BASELINE.md:5` "Tag: STEP0-FREEZE-**YYYYMMDD-HHMMSS**" 占位符未替换

**代码现实**: 实际值是 9 dirty / 5 untracked / 23F-1772P / tag `STEP0-FREEZE-20260831-054019`

**严重度**: **P1** ("冻结基线 = 0 数字"的空 artifact)

---

## C-11 — HERMES 调度文档声称 M2 14/16 通过

**冲突源**:
- `docs/audit/HERMES_DISPATCH_STEP1_*.md:72-73` (和 V2) "M2资产验证进度: 14/16 (87.5%)"
- `docs/audit/HERMES_DISPATCH_STEP1_*.md:73` "结构性条件: ...DayYearRelation✅ Root✅"

**代码现实**: pytest baseline **23 例失败**,其中 **20 例是 M2 asset 测试**,包括:
- `tests/test_m2_asset_integration_v2.py` (5F)
- `tests/test_m2_asset_enhanced_integration.py` (6F)
- `tests/test_m2_asset_complete_integration.py` (2F)
- `tests/test_m2_asset_enhanced_final.py` (1F)
- `TestDayYearRelationEvaluator::test_year_keeps_day_true`、`test_day_year_missing`
- `TestM2Asset_FullIntegration` 岁君 cases (2F)

**严重度**: **P1** (调度方对进度的乐观声明与测试实况严重不符)

---

## C-12 — ARCHITECTURE_DECISION_RESULT.md:227 ✅ 但模块不存在

**冲突源**:
- `docs/ARCHITECTURE_DECISION_RESULT.md:227` 裁决 3: "canonical_state + canonical_state_engine" 模块布局 ✅
- `docs/ARCHITECTURE_DECISION_RESULT.md:22,224` 裁决 D: new independent Canonical Calculation Engine ✅

**代码现实**:
- `find src -name "*canonical_state*"` → **无结果**
- `canonical/` 目录有 `state.py`(数据类)、`producer.py`(算法),但无 `canonical_state_engine.py`
- 没有"旺衰计算"的替代引擎——所以所有 4 个 migration 阶段仍 ⏳

**严重度**: **P2**

---

## C-13 — canonical/composer.py 与 canonical/state.py 共用包名但无关

**冲突源 (代码 vs 代码)**:
- `src/tongshu/canonical/composer.py` = `CanonicalComposer` 从 `Signal`/`CrossResult` 构造 `CanonicalContent` (V1 render path),由 `pipeline.py:21` 真实 import
- `src/tongshu/canonical/state.py` = `CanonicalState` dataclass,五经辨证替代方案,**无生产 consumer**
- 两个不同的 "canonical" 含义在同一个 package 下共存;`composer.py` 永未 import `state.py`

**严重度**: **P2** (命名冲突隐患 + 文档化未覆盖)

---

## C-14 — 两份 RootConditionEvaluator (v1+v2) 同命名冲突

**冲突源 (代码 vs 代码)**:
- `src/tongshu/canonical/root_evaluator.py:35` `class RootConditionEvaluator(BaseConditionEvaluator)`
- `src/tongshu/canonical/root_evaluator_v2.py:22` `class RootConditionEvaluator(BaseConditionEvaluator)`

**代码现实**: 两份同名类,均无生产 consumer,但任何 import `RootConditionEvaluator` 的代码会**只解析一个**(Python 缓存机制)。

**严重度**: **P0** (命名冲突)

---

## C-15 — BRANCH_HIDDEN_STEMS 表分裂

**冲突源 (代码 vs 代码)**:
- `src/tongshu/canonical/root_evaluator.py:18-31` 自带一份 `BRANCH_HIDDEN_STEMS`
- `src/tongshu/reasoning/bazi_ten_gods.py` 权威版本

**代码现实**: 两份独立副本,可能漂移。consumer 应使用权威版,但 `root_evaluator.py` 用了本地副本。

**严重度**: **P0** (事实表分裂)

---

## C-16 — strength_engine.py:3-7 header 与 `__all__` 矛盾

**冲突源 (代码 vs 代码)**:
- `src/tongshu/engines/strength_engine.py:3-7` header: "【状态】LEGACY / DEPRECATED_IN_PROGRESS"
- `src/tongshu/engines/strength_engine.py:610-616` `__all__` 仍 export 4 个 public 名字:`D1StrengthResult`、`D1FeatureResult`、`evaluate_strength`、`evaluate_strength_features`、`infer_verdict`

**严重度**: **P2** (声明 DEPRECATED 但代码无 DeprecationWarning / feature flag)

---

## C-17 — legacy 标"已隔离"但 /admin HTTP 可达

**冲突源**:
- `docs/P0_2_LEGACY_STRENGTH_ENGINE_CALL_GRAPH_AUDIT.md:60-73` "legacy/assertion_v1/... ✅ 已隔离,不影响生产路径"

**代码现实**:
- `src/tongshu/admin/router.py:85` `POST /admin/cases/compute`
- `src/tongshu/admin/service.py:73,108` `produce_all_evidence`
- `src/tongshu/legacy/assertion_v1/engine_adapters.py:42,45` `evaluate_strength`
- `src/tongshu/api/app.py:589-590` 直接 `include_router(admin_router)` 无 feature flag

**严重度**: **P0** (唯一 HTTP 可达的活路径,被所有文档忽略)

**含义**: 这是三重取证中"生产入口链"彻底失败的证据。按文档执行 P0 修复,只修了 3 个 ORPHAN,留下真正在跑的。

---

## C-18 — ARCHITECTURE V11/V12/V13/1.1 vs canonical/ 不对齐

**冲突源**:
- `docs/ARCHITECTURE_V11.md`、`V12.md`、`V13_FINAL.md`、`V1.1.md` 均未提及 `canonical/state.py`、`condition_evaluator.py`、`composer.py`
- 仅 `ARCHITECTURE_V12.md:26` 提及 `signal/canonical_signal.py`

**代码现实**: canonical/ 包是 STEP 1 才发现的"未知架构层",与四份 ARCHITECTURE 文档均未对齐。

**严重度**: **P2** (架构文档缺失整个 canonical/ 层)

---

## C-19 — P0-8.10 系列报告基于 mock dict 模式

**冲突源**:
- `p0_8_10/M3_PHASE2_STRICT_FINAL_REPORT_V6.md` 等 12 份报告声称 "14/16 测试通过"
- 基于的测试模式是 mock dict + 字面 evaluator.evaluate(state_dict)

**代码现实**: 这些 mock 测试无法验证生产行为(见 C-27)。

**严重度**: **P2** (测试真实性问题导致报告结论无基础)

---

## C-20 — condition_evaluator.evaluate() 收 Dict[str, Any] 而非 CanonicalState

**冲突源 (代码 vs 代码)**:
- `src/tongshu/canonical/state.py:334` `CanonicalState` 是 dataclass
- `src/tongshu/canonical/condition_evaluator.py:80+` `evaluate(canonical_state: Dict[str, Any])`

**代码现实**: evaluator 收 plain dict,没有任何类型约束保证传入的"Canonical State"是 `CanonicalState` dataclass。

**严重度**: **P2** (类型解耦,治理无法强制)

---

## C-21 — validate_token 桩 + lazy auth_gate

**冲突源**:
- `src/tongshu/services/daily_api.py:77-82` `validate_token()` 是长度检查桩,任何 ≥16 字符字符串通过
- `src/tongshu/api/deps.py:67-73, 220-235` `TONGSHU_AUTH_ENFORCED` 默认 `false`,permissive 模式返回 `UserContext(user_id="anonymous")`
- 注释 "实际应查询数据库验证"

**代码现实**: 任何带 16+ 字符 token 的请求都被认作已认证用户。

**严重度**: **P1** (若 daily_api 被接入公开路由,严重安全事故)

---

## C-22 — Default DSN 含 `postgres:postgres` 字面量

**冲突源**:
- `src/tongshu/db/config.py:15-16` `DEFAULT_DSN = "postgresql://postgres:postgres@127.0.0.1:5432/otcg"` + KB DSN

**代码现实**: 字面 default 凭据,虽仅本地开发用,但仍在源码中。

**严重度**: **P2** (代码 hygiene)

---

## C-23 — sys.path.insert 多处硬编码绝对路径

**冲突源**:
- `src/tongshu/v_validation/end_to_end.py:16` `sys.path.insert(0, str(Path("D:/today/backend/src")))` — **错误路径**(旧目录)
- `src/tongshu/canonical/root_evaluator_v2.py:151` `sys.path.insert(0, "/d/shuntian/backend")` — **绝对路径**,其他机器必破
- `src/tongshu/audit_validation/gates/g3_safety.py:51` `sys.path.insert(0, 'backend/src')` — 相对路径
- `src/tongshu/engines/annual_event_evaluator.py:32` `sys.path.insert(0, 'src')` — 相对路径
- `src/tongshu/services/daily_state_service.py:15` 通过 `__file__` 计算 — 安全但脆弱
- `src/tongshu/reasoning/context_assembler.py:27` `sys.path.insert(0, 'src')` — 相对
- `src/tongshu/evaluation/l2_direction.py:23` 计算 path,注释"no longer needed"

**严重度**: **P1** (end_to_end.py 路径错误会直接 fail)

---

## C-24 — _case_cache / _BUCKETS 限流器无限增长

**冲突源**:
- `src/tongshu/admin/router.py:36` `_case_cache: dict[str, Any] = {}` — 无淘汰
- `src/tongshu/api/deps.py:282-299` `_BUCKETS[name]._requests[key]` — 无淘汰,高基数 key 下放大 DoS
- `src/tongshu/reasoning/event_topic.py:427` `_HEALTH_MOD_CACHE` — 实际 bounded by domain (60×12×2=1440 keys)
- `src/tongshu/engines/heluo/canonical.py:44` `_jie_cache` — 按 year 增长

**严重度**: **P1** (long-running admin process OOM)

---

## C-25 — daily_api stub 数据 / 桩 validate_token

**冲突源**:
- `src/tongshu/services/daily_api.py:35-82` 返回硬编码占位 hexagram (`'火山旅'`) 和 `element_balance` dict

**代码现实**: 占位服务,如被接入公开路由则用户得到假数据。

**严重度**: **P2** (仅当 wired 进 public route 时升级为 P1)

---

## C-26 — test_p6c_3c2_permanent_negative return True 模式

**冲突源**:
- `tests/test_p6c_3c2_permanent_negative.py` 所有测试函数以 `return True` 结尾
- pytest 警告: `PytestReturnNotNoneWarning: Test functions should return None, but ... returned <class 'bool'>.`

**代码现实**: 即使内部 assert 全部失败,函数末尾 return True 让 pytest 报告通过。

**严重度**: **P1** (测试基础设施级真实性问题)

---

## C-27 — M2 asset / condition_evaluator 测试全部硬编码 dict

**冲突源**:
- `tests/test_condition_evaluator.py:29-35` `canonical_state = {"ten_gods_distribution": {"YIN_XING": 1, "QI_SHA": 2}}`
- `tests/test_m2_asset_integration.py:40-44` 同模式

**代码现实**: 测试用字面 dict 评估,`BaziEngine.compute()` 或 `CanonicalStateProducer.produce()` 一旦回归,**全部仍绿**。

**严重度**: **P0** (测试真实性)

---

## C-28 — yinyang 测试 6 字符串 assertIn

**冲突源**:
- `tests/test_strength_engine_yinyang.py:33, 61` `self.assertIn(r.verdict, ("身强", "从强", "从强(假)", "身弱", "从弱", "从弱(假)"))`

**代码现实**: 即使 `evaluate_strength` 把所有命例坍缩成"身强",测试全过。文件 docstring 声称"P2-D1R1 阴阳修正"无护栏。

**严重度**: **P0** (测试语义破坏)

---

## C-29 — p2_direction_golden 加载 golden 但不读

**冲突源**:
- `tests/test_p2_direction_golden.py:25-26` `self.golden_data = json.loads(golden_path.read_text(encoding="utf-8"))`
- 后续 6 个 `test_body_*` 方法无 `self.golden_data` 引用

**代码现实**: 文件名 "Golden" 误导,实际断言 `len(favorable_elements) > 0` 不与任何 golden 期望对齐。

**严重度**: **P1**

---

## C-30 — assertion producers 预制 pillars + chart={}

**冲突源**:
- `tests/test_ziping_assertion.py:24-31` `self.context = {"bazi": [("甲","寅"),...]}; a = p.produce(self.inp, chart={}, context=self.context)`
- `tests/test_assertion_producers.py:33-41` 同模式

**代码现实**: `chart={}` 是空 dict,`BaziEngine.compute()` 从未被调用。

**严重度**: **P1**

---

## 冲突统计

| 严重度 | 数量 |
|---|---|
| **P0** | 7 (C-03, C-06, C-08, C-14, C-15, C-17, C-27, C-28) |
| **P1** | 13 (C-01, C-02, C-04, C-09, C-10, C-11, C-21, C-23, C-24, C-26, C-29, C-30) |
| **P2** | 10 (C-05, C-07, C-12, C-13, C-16, C-18, C-19, C-20, C-22, C-25) |
| **P3 / RESEARCH** | 0 |

**总冲突数**: 30

**说明**: 
- C-03、C-06、C-08、C-14、C-15、C-17、C-27、C-28 都是 P0 级别
- 文档一致性(C-09, C-10, C-11)与代码真实性(C-26, C-27, C-28, C-29, C-30)是 STEP 1 最严峻的两类问题
- 多数 P1 涉及**计划可执行性**(C-01, C-02, C-23)——按现有 docs 修复会修错地方

---

**审计完成时间**: 2026-08-31  
**审计原则**: 只发现不修复,所有冲突均可通过指定文件:行复核