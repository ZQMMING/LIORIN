# 🔍 STEP 1 FULL AUDIT REPORT — 12 Domain Independent Audit

**审计日期**: 2026-08-31  
**审计者**: Claude (独立审计方,与 Hermes 非上下级)  
**Commit 基线**: aa35031 (STEP0-FREEZE-20260831-054019)  
**作用域**: `D:\shuntian\backend\src\tongshu\` + `tests\` + `docs\`  
**输出位置**: `docs/audit/`

---

## 0. 总裁决

### 0.1 立项裁决（基于实代码验证,非文档声明）

**问题真实状态 (跟 STEP0 与 P0_ISOLATION_PLAN 的描述不一致)**:

| 文档声明 | 实代码验证 | 评级 |
|---|---|---|
| `wang_score` 仍在生产判定链 | ❌ **不成立**——`pipeline.py`/`compute_stage.py`/`render_stage.py`/`validation_stage.py` 均无 `strength_engine` import;用户面向的 `/api/reading` `/v1/daily-guide` 路径已完全脱离 wang_score | **DECLARATION STALE** |
| `evaluate_strength` 仍在主链运行 | ❌ **不成立**——7 处调用全部 ORPHAN 或 shadow (admin) | **DECLARATION STALE** |
| 急需 P0 隔离 strength_engine | ⚠️ **部分有效**——wang_score 阈值判定仍在 strength_engine.py:396-397 活跃;但消费方已断 | **PARTIAL STALE** |
| CanonicalState/五经辨证替代 | ❌ **未落地**——`CanonicalState` 类型在,`Condition Evaluator` 类型在,但 pipeline 无任何调用 | **NOT IMPLEMENTED** |

### 0.2 实际威胁排序

| Rank | 威胁 | 性质 | 真实路径 |
|---|---|---|---|
| 1 | CanonicalState / 五经辨证链路**完全未连通**到 ComputeStage / RenderStage | 架构未完成,非"已存在风险" | producer.py 定义但无 consumer |
| 2 | wang_score 阈值逻辑仍在 strength_engine.py:396-397 存活 | 已声明 LEGACY 但代码活跃 | 函数 export,7 处 import(全部 ORPHAN) |
| 3 | M2 asset / condition_evaluator 测试全部用硬编码 dict | 测试绿但生产可能塌 | tests/test_m2_asset_*.py, test_condition_evaluator.py |
| 4 | yinyang 测试用 6 字符串 assertIn | 阴阳从格逻辑回归无护栏 | tests/test_strength_engine_yinyang.py:33,61 |
| 5 | PowerComparisonEvaluator 纯计数比较无原典授权 | 生产未消费但一旦连通即可激活 | canonical/condition_evaluator.py:144-210 |
| 6 | 两份 RootConditionEvaluator (v1+v2) 同时存在且互不知 | 命名冲突 + 全部死代码 | canonical/root_evaluator.py:35 + _v2.py:22 |
| 7 | DayYearRelationEvaluator 已合入(DYE-1: 正确);其余 evaluator 多处 UNRESOLVED 坍塌 | 已在 canonical/evaluators/__init__.py 导出 | condition_evaluator.py:114-138, 295-306 |
| 8 | /admin 路由用 legacy engine_adapters.produce_all_evidence → evaluate_strength | shadow 链路,观测端点 | api/app.py:589-590 → admin/service.py:73 |
| 9 | pipeline.py:244-250 后置覆盖 rendered_text | audit 记录的是改写后的 final_text | pipeline.py:241-250 |
| 10 | docs 中"生产调用 annual_event_evaluator.py:207 / health_signals.py:99 / judgment_engine.py:41" | STALE:三处调用均 ORPHAN | strength_engine.py:3-7 header |

---

## 1. Domain 1 — Runtime Call Graph / Production Wiring

### D1.1 — strength_engine 调用图取证

**结论**: `evaluate_strength` 在面向用户的 API 链路上 **0 处活跃调用**。全部 7 处 import 中:
- 5 处 ORPHAN (`reasoning/health_signals.py:99`、`reasoning/event_topic.py:445`、`engines/judgment_engine.py:41` 类型 only、`legacy/assertion_v1/environmental_fit.py:294`、`legacy/assertion_v1/systems.py:651`)
- 1 处 MAIN() CLI (`engines/annual_event_evaluator.py:207`——只在本文件 `main()` 跑 `.tmp_cases/fate_bench/data/hkjfma_qa.json` 时)
- 1 处 SHADOW (`legacy/assertion_v1/engine_adapters.py:42` → `/admin` 路由 → `admin/service.py:73` → `produce_all_evidence()`)

**`/api/reading`、`/v1/daily-guide`、`/api/today` 路径 0 调用**——已 grep `src/tongshu/api/`、`src/tongshu/pipeline.py`、`src/tongshu/pipeline_stages/*.py`,确认全部无 `evaluate_strength` / `strength_engine` / `wang_score` / `D1StrengthResult`。

### D1.2 — Pipeline 阶段接线

```
pipeline.run() [pipeline.py:154-298]
  → ComputeStage.run() [compute_stage.py:94]
      → BaziEngine.compute()     ✓
      → ZiweiEngine.compute()     ✓
      → SignalEngine.build()      ✓
      → CrossAnalyzer.analyze()   ✓
      → mapping_registry.apply_to_claims()  ✓
      → CanonicalComposer.compose() ✓
      → validate_canonical()      ✓
  → RenderStage.run() [render_stage.py]
  → ValidationStage.run() [validation_stage.py:51]
  → AuditComposer.compose_and_write() [audit_composer.py]
  → template_fallback.render()  ⚠️ 覆盖 rendered_text
  → dao.record_*() [pipeline.py:300-428]
```

### D1.3 — 严重度

| ID | 发现 | 严重度 | 文件:行 |
|---|---|---|---|
| D1-A | `evaluate_strength` 仍导出 + wang_score 阈值判定活跃 | **P2 (残留,无消费者)** | strength_engine.py:75,223,396-397,613 |
| D1-B | `/admin` shadow 链路用 legacy engine_adapters | P2 (工程观测非面向用户) | admin/service.py:73 → legacy/assertion_v1/engine_adapters.py:42-65 |
| D1-C | strength_engine.py:3-7 header 自陈"生产调用 X/Y/Z",实为 ORPHAN | **STALE** | strength_engine.py:3-7 |
| D1-D | event_topic.py:445 lazy import 与 health_signals.py:99 是死代码,但占用 import graph | P3 | reasoning/event_topic.py:442-445; reasoning/health_signals.py:19,99 |
| D1-E | judgment() 函数无调用方,P2JudgmentResult 死代码 | P3 | engines/judgment_engine.py:371-616 |

### D1.4 — 反驳风险

> Q: 既然 wang_score 没有消费者,为何还要标 P0?
> A: wang_score 阈值判定函数本身是活跃代码,任何 import `evaluate_strength` 的代码(包括测试、未来误连的链路)都立刻获得"身强/身弱"标签。`legacy/assertion_v1/engine_adapters.py:42-65` 仍通过 `/admin` 在生产激活,且把 verdict 写进 `ZP_WANGSHUAI_VERDICT` evidence。这是 P2 而非 P0:用户路径已断,但 shadow 路径仍存。

> Q: `/admin` 是内部端点,有风险吗?
> A: `api/app.py:589-590` 直接 `include_router(admin_router)`,无鉴权筛选,无 feature flag。如果 admin_router 暴露到公网,/admin 路径可直接触发 verdict 链。

---

## 2. Domain 2 — Canonical State & Evidence Container

### D2.1 — CanonicalState 容器自检

| 字段 | 状态 | 备注 |
|---|---|---|
| 整体 `overall_state` 默认 `UNRESOLVED` | ✅ | state.py:367 |
| `validate()` 拒绝 `strength_score`/`root_score`/`wangshuai_score`/`qiangruo_score` | ✅ | state.py:437-444 |
| 内部 record (`Fact`/`Relation`/`Provenance`/`ClassicalState`/`Qualifier`/`UnresolvedReason`) 全 frozen | ✅ | state.py:119,147,177,217,266,304 |
| 容器本身 `@dataclass(frozen=True)` | ❌ | **S-1**:state.py:334 — 注释承诺"只读容器"但 Python 不强制 |

### D2.2 — CanonicalStateProducer 实状

- 类定义存在 (`canonical/producer.py:35-346`)
- `produce(chart)` 方法完整:生成四柱 facts / 藏干 facts / 五行阴阳 facts / 十神 facts / 通根 relations / 生克 relations / 刑冲合害 relations
- **生产代码 0 调用方**——`grep -r "CanonicalStateProducer\|producer.produce" src/tongshu/` 仅命中 producer.py 自引用

### D2.3 — 严重度

| ID | 发现 | 严重度 | 文件:行 |
|---|---|---|---|
| D2-A | CanonicalState 类型在,生产链路 0 引用 | **P1** | state.py:334; producer.py:35 |
| D2-B | `CanonicalState` 非 frozen,违反 header docstring "只读容器" | P3 | state.py:334 |
| D2-C | `producer.py` header 注释"迁移方向: health_signals.py / annual_event_evaluator.py 改为消费 CanonicalState"——未实施 | STALE | canonical/producer.py:6 |

### D2.4 — 反驳风险

> Q: `CanonicalState` 未消费是否真的 P1?
> A: 是。整个 CanonicalState / 五经辨证架构作为"替代 wang_score 的方案"已声明,但与 `compute_stage.py:138-148` (SignalEngine + CrossAnalyzer) 路径**完全平行**,互不连通。AGENTS.md §2 描述的"辨证中间状态容器"是空骨架。

---

## 3. Domain 3 — Architecture / Five-Classics Path

### D3.1 — 五经辨证落地现状

| 模块 | 状态 |
|---|---|
| `canonical/state.py` | 类型 + validate() ✓ |
| `canonical/producer.py` | 类型 + 算法 ✓ |
| `canonical/composer.py` | SIR 构造(运行于 pipeline,数据源是 BaziChart + Signals)✓ |
| `canonical/condition_evaluator.py` | 类型 + 多 Evaluator |
| `canonical/root_evaluator.py` (v1) + `_v2.py` | 死代码,同命名冲突 |
| `canonical/tengod_mapper.py` | 死代码,简化处理 |
| `canonical/negation_evaluator.py` | 类型已注册到 `evaluators/__init__.py` |
| `canonical/day_year_evaluator.py` | 类型已注册到 `evaluators/__init__.py` |
| `canonical/canonical_validator.py` | 在 ComputeStage.run():193 实际被调用 |
| **`ComputeStage` / `RenderStage` / `Pipeline.run()` 消费 Condition Evaluator** | ❌ **0 处** |

### D3.2 — 严重度

| ID | 发现 | 严重度 | 文件:行 |
|---|---|---|---|
| D3-A | 五经辨证链路未接入生产管线 | **P1 (架构未完成)** | pipeline.py:209, compute_stage.py:94 |
| D3-B | 两份 RootConditionEvaluator 同命名 v1 + v2 同时存在,无消费者 | **P1** | canonical/root_evaluator.py:35; canonical/root_evaluator_v2.py:22 |
| D3-C | TenGodToStemMapper 无消费者,但内部多次"简化处理"产生 False 假信号 | P2 | canonical/tengod_mapper.py:212-215, 238-242 |

### D3.3 — 反驳风险

> Q: "评估器未接入"是否等于"未实现"?
> A: 类型、单元测试、evaluators/__init__.py 导出均存在,但**没有 production glue code**——没有"在 ComputeStage 后调用 condition_evaluator,在 RenderStage 前读 verdict"的代码。这是 STEP 1 应独立审计的"半成品"。

---

## 4. Domain 4 — Governance Compliance

### D4.1 — 治理契约 vs 实际执行

| 治理原则 | 文档来源 | 实际执行 | 评级 |
|---|---|---|---|
| 禁止 wang_score/root_score 进生产 verdict | AUDIT_GUIDE.md §4.3 | wang_score 在 strength_engine.py:75,353-358,396-397 仍计算;阈值判定仍生效 | ❌ 违反 (但消费者已断) |
| 禁止"五行计分→强弱" | AUDIT_GUIDE.md §4.3 | strength_engine.py:285-358 仍按五行加权打分 | ❌ 违反 (同上) |
| 五经辨证替代 wang_score | ARCHITECTURE_V13_FINAL.md + producer.py:6 | 未实施 | ❌ 未实施 |
| FROZEN ≠ PROVEN CORRECT | AUDIT_GUIDE.md §3.2 | 文档自承认 | ✅ 文档自承认 |
| Evidence ≠ Condition ≠ Judgment ≠ Conclusion | AUDIT_GUIDE.md §4.4 | 评估器内"UNRESOLVED 坍塌"违反 | ⚠️ 部分违反 (CE-1, CE-4, NE-1) |
| Assertion 不能反推 State | AUDIT_GUIDE.md §4.3 | 未观察到反推 | ✅ |
| 生产代码不能 mock/简化处理 | AUDIT_GUIDE.md §4.3 + AGENTS.md §5 | `tengod_mapper.py:215` "这里简化处理,返回第一个" | ❌ 违反 |
| 评估器不能因命中就授权 | AUDIT_GUIDE.md §4.3 | `PresenceConditionEvaluator` 直接字符串比对;`RootConditionEvaluator` v1 v2 都返回布尔而非三元 | ❌ 违反 |

### D4.2 — 严重度

| ID | 发现 | 严重度 | 文件:行 |
|---|---|---|---|
| D4-A | wang_score 阈值判定在 strength_engine.py 仍激活 | **P2 (残留但已断)** | strength_engine.py:75, 396-397 |
| D4-B | 工程权重(本气1.0/中气0.5/余气0.3/偏印0.6/相冲1.2/阈值2.0)无原典 | **P2** | strength_engine.py:52,56,61,75 |
| D4-C | PowerComparisonEvaluator 纯计数比较授权 verdict | **P2 (待落地会激活)** | condition_evaluator.py:144-210 |
| D4-D | PresenceConditionEvaluator 日干混名 + 字符串直接比对 | P2 | condition_evaluator.py:213-254 |
| D4-E | TenGodToStemMapper "简化处理,返回第一个" | P2 | tengod_mapper.py:213-215 |
| D4-F | root_evaluator v1 比较 ten_god 字符串与 stem 字符串 | P2 | root_evaluator.py:78-80 |
| D4-G | root_evaluator v2 + mapper mapping 失败 → False(等同于未授权给 FALSE) | P2 | root_evaluator_v2.py:77-115 + tengod_mapper.py:238-242 |
| D4-H | TenGodConditionEvaluator 缺失键 → FALSE 而非 UNRESOLVED | P2 | condition_evaluator.py:116-122 |
| D4-I | CompositeConditionEvaluator OR 任一 TRUE 即返回 TRUE(抑制 UNRESOLVED) | P2 | condition_evaluator.py:295-306 |
| D4-J | NegationConditionEvaluator count=0 → TRUE(混名"无"与"零") | P2 | negation_evaluator.py:59-67 |
| D4-K | DayYearRelationEvaluator UNRESOLVED 传播正确 | ✅ | day_year_evaluator.py:81-96, 172-176 |
| D4-L | CanonicalState.validate() 禁止 strength_score/root_score/wangshuai_score/qiangruo_score | ✅ | state.py:437-444 |

---

## 5. Domain 5 — Validation Layer (Gates / Layer1-3)

### D5.1 — 验证层接线

- `validation_stage.py:51-100` 完整跑 L1 (Claim 覆盖) + L2 (文本相似度) + L3 (蕴含) + 4 Gates (G1-G4)
- `audit/gates.py` 提供 G1/G2/G3/G4 + run_gates() 函数
- `pipeline.py:241` 调 `self.validation_stage.run(...)`

### D5.2 — Fail-closed 行为

```python
# validation_stage.py:67-74
if not self._enable_validation or rendered_obj is None:
    return ValidationStageResult(
        layer1=None, layer2=None, layer3=None,
        gates=(), passed=False,  # fail-closed
    )
```
✅ 设计正确:不通过 → 整体不通过

### D5.3 — 后置覆盖 (审计盲点)

```python
# pipeline.py:244-250
if not validation_passed and self._enable_validation:
    fallback = self.template_fallback.render(theme, cross_result.status)
    if fallback:
        rendered_text = fallback
        source = "template_fallback"
```
✅ 行为:不通过 → 降级到 template_fallback
⚠️ 审计记录: `audit_composer.py:122-126` 写入的是降级后的 final_text,**原始 LLM 文本丢失**

### D5.4 — DAO 边界粒度坍塌

```python
# pipeline.py:333-334
db_status = "ok" if validation.passed else "fallback"
db_source = "llm" if source == "llm_renderer" else "template"
```
⚠️ `compute_only` / `template_fallback` / `llm_renderer` / `computed` 四类坍缩到 `llm | template`,`ok | fallback | error` 三类。

### D5.5 — 严重度

| ID | 发现 | 严重度 | 文件:行 |
|---|---|---|---|
| D5-A | 验证层 fail-closed 设计正确 | ✅ | validation_stage.py:67-74 |
| D5-B | audit 记录降级后文本,原始 LLM 文本丢失 | P3 (审计追溯性) | pipeline.py:241-250 → audit_composer.py:122-126 |
| D5-C | DAO 边界粒度坍塌 (compute_only/template_fallback → template; hard-fail 与 validation-fail 不可区分) | P3 (粒度损失) | pipeline.py:333-334 |

---

## 6. Domain 6 — Process / Role / Anti-self-audit

### D6.1 — 流程合规性

| 流程规则 | 文件 | 现状 |
|---|---|---|
| Implementer ≠ Auditor | AGENTS.md §1 | ✅ Claude(独立审计)与 Hermes(调度)分离 |
| 红线: 禁止 git add -A | AGENTS.md §5 | ⚠️ 本审计未涉及 commit,无法验证 |
| 红线: 禁止为变绿改测试 | AGENTS.md §5 | ⚠️ baseline 日志显示测试失败,需审查者独立核查 |
| 红线: 禁止改 Golden 期望值 | AGENTS.md §5 + §3 | ⚠️ 13 失败案例未修(冻结保留) |
| 提交链: OpenCode → Claude 复审 → Hermes → User | AGENTS.md §1 | 本审计是 Claude 独立审计,符合 |
| 三重取证(调用图/生产入口链/测试对象核对) | AGENTS.md §2 | ✅ 本审计已按此法完成 |

### D6.2 — 严重度

| ID | 发现 | 严重度 | 文件:行 |
|---|---|---|---|
| D6-A | STEP 0 已冻结 baseline 测试失败,但失败原因未公开 | P2 | pytest-baseline-20260831-054019.log |
| D6-B | self-audit 风险: Hermes 设计 + Hermes 写代码 + Hermes 宣布 PASS 的旧模式 | ✅ 已切到 Claude 独立 | (历史) |

---

## 7. Domain 7 — Test Authenticity

### D7.1 — 测试真实性矩阵

| 测试文件 | REAL | PERMISSIVE | HARDCODED | MOCK |
|---|---|---|---|---|
| `test_strength_engine.py` | ✅ 6 个 case | – | – | – |
| `test_strength_engine_yinyang.py` | ✅ 用真实 Bazi 计算 | **P0** assertIn 6 verdict | – | – |
| `test_judgment_engine.py` | ✅ 真实 Bazi | **P1** 守卫 if "身强" in verdict | – | – |
| `test_p2_direction_golden.py` | ✅ 真实 Bazi | **P1** 守卫 + assertIn + 加载 golden 但不读 | – | – |
| `test_environmental_fit.py` | ✅ 真实 Bazi | – | – | – |
| `test_new_engines.py:147-166` | ✅ 真实 Bazi | – | – | – |
| `test_m2_asset_*.py` (8 文件,~120 case) | – | – | **P0** 硬编码 dict | – |
| `test_condition_evaluator.py` (18 case) | – | – | **P0** 硬编码 dict | – |
| `test_ziping_assertion.py` | – | P2 (上限断言) | **P1** chart={} + 字面 bazi | – |
| `test_assertion_producers.py` | – | P2 (上限断言) | **P1** 同上 | – |
| `test_heluo_context.py:19-27` | – | – | P2 MockBazi + 预制 pillars | 部分 |
| `test_k2g_golden.py` | – | – | P3 仅 shape | – |
| `test_audit_gates.py` | – | – | P3 合成 SIR dict | – |
| `test_b02_late_zi_golden.py` | ✅ 真实 BaziAdapter | – | – | – |
| `test_blind_yingqi.py` | ✅ 真实 engine | – | – | – |
| `test_rule_engine.py` | ✅ 真实 engine | – | – | – |
| `test_bazi_engine.py` | ✅ 真实 dataclass | – | – | – |
| `test_huangli_engine.py` | ✅ | – | – | – |
| `test_api.py:157` test_v1_today_calendar_real_not_mock | ✅ | – | – | – |
| `test_conftest.py:16` | – | – | – | MOCK (env-gated,文档化) |
| `test_db/test_b09_r2_migration_chain.py` | – | – | – | MOCK (CI无DB) |
| `test_auth/test_b09_r4_rate_limit_audit.py:231` | – | – | – | MOCK (负路径) |
| `test_llm_client.py` | – | – | – | MOCK (HTTP) |
| `validation_v12/test_g5_gate.py` | – | – | – | MOCK (合同级) |

### D7.2 — P0 发现详述

#### D7.1.A — M2 asset / condition_evaluator 测试全部硬编码

**模式** (`tests/test_condition_evaluator.py:29-35`, `tests/test_m2_asset_integration.py:40-44`):
```python
canonical_state = {
    "ten_gods_distribution": {"YIN_XING": 1, "QI_SHA": 2}
}
result = evaluator.evaluate(canonical_state)
assert result == EvaluationResult.TRUE
```

**风险**: 评估器逻辑正确,但 `BaziEngine.compute()` 或 `CanonicalStateProducer.produce()` 一旦回归,这些测试 **全部仍绿**。"测试通过 ≠ 生产正确"。

**严重度**: **P0** (测试真实性)

#### D7.1.B — yinyang 测试用 6 字符串 assertIn

**模式** (`tests/test_strength_engine_yinyang.py:33, 61`):
```python
self.assertIn(r.verdict, ("身强", "从强", "从强(假)", "身弱", "从弱", "从弱(假)"))
```

**风险**: 即使 `evaluate_strength` 把所有命例坍缩成"身强",这些测试全过。文件 docstring 声称"P2-D1R1 阴阳修正"被证伪时,无护栏。

**严重度**: **P0** (测试语义破坏)

#### D7.1.C — `test_p2_direction_golden.py` 加载 golden 但不读

**模式** (line 25-26):
```python
golden_path = Path(__file__).resolve().parent.parent / "dataset" / "golden_v1" / "golden_cases.json"
self.golden_data = json.loads(golden_path.read_text(encoding="utf-8"))
```
后续 6 个 test_body_* 方法无 `self.golden_data` 引用,全部用字面日期 `_eval_with_judgment("1724-08-03", 12, "male")`。

**风险**: 文件名 "Golden" 误导,实际断言 `len(favorable_elements) > 0` 不与任何 golden 期望对齐。

**严重度**: **P1**

#### D7.1.D — test_judgment_engine.py / test_p2_direction_golden.py 守卫失配

**模式** (test_judgment_engine.py:81):
```python
if "身强" in r.verdict_from_d1 or "从强" in r.verdict_from_d1:
    self.assertIn("OFFICIAL", r.favorable)
    ...
```

**风险**: verdict 不含"身强"或"从强"时,内部断言全跳过,test 通过。等于"verdict 错误时不报警"。

**严重度**: **P1**

#### D7.1.E — test_ziping_assertion.py / test_assertion_producers.py 预制 pillars

**模式** (test_ziping_assertion.py:24-31):
```python
self.context = {
    "birth": (1974, 4, 28, 16, "male"),
    "bazi": [("甲","寅"),("戊","辰"),("己","亥"),("壬","申")],
    ...
}
a = p.produce(self.inp, chart={}, context=self.context)
```

**风险**: `chart={}` 是空 dict,`BaziEngine.compute()` 从未被调用。`BaziChart` 回归时这些测试仍绿。

**严重度**: **P1**

### D7.3 — 严重度总览

| ID | 发现 | 严重度 | 文件:行 |
|---|---|---|---|
| D7-A | M2 asset / condition_evaluator 测试硬编码 | **P0** | tests/test_m2_asset_*.py; tests/test_condition_evaluator.py |
| D7-B | yinyang 测试 6 字符串 assertIn | **P0** | tests/test_strength_engine_yinyang.py:33,61 |
| D7-C | p2_direction_golden 加载 golden 不读 | P1 | tests/test_p2_direction_golden.py:25-26 |
| D7-D | judgment / p2 测试 verdict 守卫失配 | P1 | tests/test_judgment_engine.py:81-127; tests/test_p2_direction_golden.py:41-95 |
| D7-E | assertion producers 预制 pillars | P1 | tests/test_ziping_assertion.py:24-31; tests/test_assertion_producers.py:33-41 |
| D7-F | confidence 上限断言 (LIKELY/WEAK/INSUFFICIENT) | P2 | tests/test_assertion_producers.py:50; tests/test_ziping_assertion.py:42; tests/test_assertion_contract.py:148 |
| D7-G | test_heluo_context MockBazi 不全 | P2 | tests/test_heluo_context.py:19-27 |
| D7-H | conftest 全局开 ziwei stub | P3 (acknowledged) | tests/conftest.py:16 |
| D7-I | audit_gates 合成 SIR dict | P3 | tests/test_audit_gates.py |
| D7-J | k2g_golden 仅 shape | P3 | tests/test_k2g_golden.py |

---

## 8. Domain 8 — Quality (Code Smell / Duplication / Drift)

### D8.1 — 代码质量与漂移

| Smell | 位置 | 评级 |
|---|---|---|
| 同命名类同时存在两份: `RootConditionEvaluator` v1 vs v2 | canonical/root_evaluator.py:35 + _v2.py:22 | **P0** (命名冲突 + 死代码) |
| `BRANCH_HIDDEN_STEMS` 多份独立副本 (root_evaluator.py:18-31 vs reasoning/bazi_ten_gods.py) | canonical/root_evaluator.py:18-31 | **P0** (事实表分裂) |
| `EVIDENCE` dict 复制粘贴 (`_EVIDENCE` 在 strength_engine.py:109, judgment_engine.py:251, health_signals.py:88) | 3 文件 | P3 |
| 调候表 (`_TIAO_HOU_BY_*`) 在 judgment_engine.py 占 200+ 行,违反单一职责 | judgment_engine.py:58-240 | P2 |
| strength_engine.py 文件头声称"LEGACY/DEPRECATED"但 `__all__` 仍 export 4 个 public 名字 | strength_engine.py:610-616 | P2 (声明与现实不一致) |
| `evaluate_strength_features` / `infer_verdict` 无调用方但 export | strength_engine.py:476-586 | P3 (死代码 export) |
| sys.path.insert(0, 'src') 散布多处 | annual_event_evaluator.py:32; compute_stage.py 在运行时计算 | P3 |
| 多个文件用字面量重写 `_STRONG_STAGES = {"临官", "帝旺"}` 而非 import 常量 | strength_engine.py:48 (only one) | ✅ |

### D8.2 — 严重度

| ID | 发现 | 严重度 | 文件:行 |
|---|---|---|---|
| D8-A | RootConditionEvaluator 同命名两份 (v1+v2) | **P0** | canonical/root_evaluator.py:35; canonical/root_evaluator_v2.py:22 |
| D8-B | BRANCH_HIDDEN_STEMS 表分裂 (root_evaluator.py 副本 vs reasoning/bazi_ten_gods.py 权威版) | **P0** | canonical/root_evaluator.py:18-31 |
| D8-C | strength_engine.py header 注释与 `__all__` 矛盾 | P2 | strength_engine.py:3-7 vs 610-616 |
| D8-D | 调候表膨胀 200+ 行 | P2 | engines/judgment_engine.py:58-240 |
| D8-E | 死代码 export (evaluate_strength_features, infer_verdict, D1FeatureResult) | P3 | strength_engine.py:476-616 |

---

## 9. Domain 9 — Documentation Sync vs Implementation

### D9.1 — 文档声明 vs 代码现实

| 文档 | 声明 | 实代码 | 评级 |
|---|---|---|---|
| `strength_engine.py:3-7` | "【生产调用】annual_event_evaluator.py:207 / health_signals.py:99 / judgment_engine.py:41(类型)" | judgment_engine.py:41 仅类型;annual_event_evaluator 仅 main() CLI;health_signals 无调用方 | **STALE** |
| `docs/audit/STEP0_FREEZE_BASELINE.md:22-24` | "Legacy Strength Engine 生产调用路径:annual_event_evaluator.py:37, judgment_engine.py:41" | 同上 | **STALE** |
| `docs/audit/P0_ISOLATION_PLAN.md:11-19` | 调用链图 annual_event_evaluator → health_signals → judgment_engine | 同上 | **STALE** |
| `docs/audit/INDEPENDENT_CODE_AUDIT_REPORT.md:38-44` | "_WANG_SCORE_THRESHOLD = 2.0" | 仍存在 strength_engine.py:75 | PARTIAL |
| `docs/P0_2_LEGACY_STRENGTH_ENGINE_MIGRATION_PLAN.md` | migration 计划 | 未实施 | NEVER-IMPLEMENTED |
| `docs/P0_2_LEGACY_STRENGTH_ENGINE_CALL_GRAPH_AUDIT.md` | 调用图审计 | 历史快照,现状已变 | STALE |
| `canonical/producer.py:6` | "迁移方向: health_signals.py / annual_event_evaluator.py 改为消费 CanonicalState" | 未实施 | STALE |
| `p0_8_10/M3_PHASE2_STRICT_FINAL_REPORT_V6.md` 系列 | "14/16 测试通过" | 基于 mock dict 模式 | PARTIAL STALE |
| `tests/test_strength_engine.py:80-88` | "从强格: 只有全局无异党时才允许标注" | 注释自承"构造难以精确控制" | acknowledged |
| `docs/USER_DECISION_20260830.md` | 强度引擎相关决策 | 已过时 | STALE |
| `docs/P0_TAKEOVER_AUDIT_20260830.md` | takeover 决策 | 反映旧状态 | STALE |
| `tests/test_p2_direction_golden.py:1-8` docstring | "判定引擎输出的 favorable/unfavorable 方向需与 Golden 数据集中的历史事件一致" | self.golden_data 从未读取 | **STALE** |

### D9.2 — 严重度

| ID | 发现 | 严重度 | 文件:行 |
|---|---|---|---|
| D9-A | `strength_engine.py:3-7` header "生产调用"陈旧 | STALE | strength_engine.py:3-7 |
| D9-B | `STEP0_FREEZE_BASELINE.md` "生产调用路径"陈旧 | STALE | docs/audit/STEP0_FREEZE_BASELINE.md:22-24 |
| D9-C | `P0_ISOLATION_PLAN.md` 调用链图基于陈旧假设 | STALE | docs/audit/P0_ISOLATION_PLAN.md:11-19 |
| D9-D | `producer.py:6` 迁移方向未实施 | STALE | canonical/producer.py:6 |
| D9-E | test docstring 与代码行为不一致 | STALE | tests/test_p2_direction_golden.py:1-8 |
| D9-F | p0_8_10 系列报告基于 mock dict 模式 | PARTIAL STALE | p0_8_10/M3_PHASE2_*.md (12 份) |

### D9.3 — 反驳风险

> Q: 文档 stale 是否严重?
> A: 是。如果 Hermes / OpenCode 基于 STEP0_FREEZE_BASELINE.md 的"生产调用路径"修复,会修错文件(annual_event_evaluator.py:37 / judgment_engine.py:41),实际真正的风险是 (a) wang_score 阈值仍激活, (b) /admin shadow 链路在跑。

---

## 10. Domain 10 — Security

### D10.1 — 安全隐患清单

| ID | 发现 | 严重度 | 文件:行 |
|---|---|---|---|
| D10-A | `os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")` 在 conftest,生产默认 fail-closed 但测试全局开 stub | P2 (测试口径与生产不一致) | tests/conftest.py:16 |
| D10-B | `api/app.py:589-590` `include_router(admin_router)` 无 feature flag / 鉴权筛选 | **P1 (admin 端点公网可达时)** | api/app.py:589-590 |
| D10-C | `sys.path.insert(0, 'src')` 多处硬编码,部署路径敏感 | P3 | annual_event_evaluator.py:32 |
| D10-D | 未发现 hard-coded secret / API key (除 .env.example) | ✅ | .env.example:1-30 |
| D10-E | 未发现 pickle / yaml.load 不安全用法 | ✅ | (grep 无命中) |
| D10-F | dao.py / db/ 未发现 SQL 字符串拼接 | ✅ (待 spot-check) | – |

---

## 11. Domain 11 — Performance

### D11.1 — 性能关注点

| ID | 发现 | 严重度 | 文件:行 |
|---|---|---|---|
| D11-A | `_HEALTH_MOD_CACHE` 缓存无淘汰 (`event_topic.py`) | P3 | reasoning/event_topic.py:432-440 |
| D11-B | `signal_engine.build()` 每次重算 heluo context | P3 | reasoning/signal_engine.py:53-95 |
| D11-C | `BaziEngine.compute()` 在 pipeline.run 一次 (`compute_stage.py:118`) | ✅ 单次计算 | – |
| D11-D | `cross_analyzer.analyze()` O(n*m) 信号交叉 | ⚠️ 待测 | compute_stage.py:148 |
| D11-E | strength_engine.py:285-358 多重嵌套循环(`for s in stems` × `for h, w in _weighted_hidden`) | P3 (仅 admin 触发) | strength_engine.py:285-358 |

---

## 12. Domain 12 — Legacy / Stale Code

### D12.1 — Legacy 资产盘点

| 资产 | 状态 | 评级 |
|---|---|---|
| `src/tongshu/legacy/` 目录 | 全部重新 export 到 `src/tongshu/assertion/` | ACTIVE_SHIM |
| `tongshu/assertion/__init__.py` 27-73 重新 export 9 个 legacy 子模块 | ✅ 存在但**没有调用方** | ORPHAN |
| `tongshu/admin/service.py:73` 唯一活跃调用 legacy | `produce_all_evidence` | ACTIVE (admin 路由) |
| `src/tongshu/legacy/assertion_v1/engine_adapters.py` | /admin 调用 | ACTIVE |
| `src/tongshu/legacy/assertion_v1/environmental_fit.py` | 无调用 | ORPHAN |
| `src/tongshu/legacy/assertion_v1/systems.py` | 无调用 | ORPHAN |
| `src/tongshu/legacy/assertion_v1/flow_year.py` | 重新 export 到 `tongshu/assertion.flow_year`,**0 调用** | ORPHAN |
| `src/tongshu/engines/strength_engine.py` 函数仍在 export | ✅ | ACTIVE_CODE,DEAD_PROD |
| `src/tongshu/engines/judgment_engine.py:371 judgment()` | 0 调用方 | ORPHAN |

### D12.2 — 严重度

| ID | 发现 | 严重度 | 文件:行 |
|---|---|---|---|
| D12-A | legacy/assertion_v1/ 9 子模块通过 shim re-export,无 feature flag | P2 (难清理) | tongshu/assertion/__init__.py:27-73 |
| D12-B | `evaluate_strength` 仍 export,wang_score 阈值仍激活 | P2 | strength_engine.py:75,223,396-397,613 |
| D12-C | `judgment_engine.judgment()` 死代码 (P2JudgmentResult dataclass 100+ 行) | P3 | engines/judgment_engine.py:307-616 |
| D12-D | `evaluate_strength_features` / `infer_verdict` / `D1FeatureResult` 死代码 | P3 | strength_engine.py:448-616 |
| D12-E | legacy/assertion_v1/systems.py 仍有 wangshuai 调用 (`mechanism` 字符串拼接) | P2 | legacy/assertion_v1/systems.py:645-680 |

---

## 13. 总体裁决 / Action 清单

### 13.1 P0 级别（必须解决）

| ID | 主题 | 严重度 |
|---|---|---|
| **P0-①** | 两份 RootConditionEvaluator (v1+v2) 同命名冲突,BRANCH_HIDDEN_STEMS 表分裂 | **P0 BLOCKER** |
| **P0-②** | M2 asset / condition_evaluator 测试全部硬编码 dict,生产回归无护栏 | **P0 BLOCKER** |
| **P0-③** | yinyang 测试 6 字符串 assertIn,阴阳从格回归无护栏 | **P0 BLOCKER** |

### 13.2 P1 级别（重要修复）

| ID | 主题 |
|---|---|
| P1-① | CanonicalState / 五经辨证链路未接入生产管线 (架构未完成) |
| P1-② | wang_score 阈值判定仍在 strength_engine.py 激活 |
| P1-③ | p2_direction_golden 加载 golden 不读 |
| P1-④ | judgment / p2 测试 verdict 守卫失配 |
| P1-⑤ | assertion producers 预制 pillars |
| P1-⑥ | `/admin` 路由无 feature flag 直接暴露 legacy engine_adapters |

### 13.3 P2 / STALE 级别

(详见各 Domain)

### 13.4 RESEARCH 级别

- CanonicalState / 五经辨证是否需要在现有 pipeline 之外独立运行
- wang_score 是否可以彻底删除 (vs 保留 LEGACY_RESEARCH_ONLY)

---

## 14. 证据清单（所有发现均可在以下文件中复核）

- `src/tongshu/engines/strength_engine.py` (1-616 行)
- `src/tongshu/engines/judgment_engine.py` (1-616 行)
- `src/tongshu/engines/annual_event_evaluator.py` (1-711 行)
- `src/tongshu/reasoning/health_signals.py` (1-186 行)
- `src/tongshu/reasoning/event_topic.py` (1-660 行)
- `src/tongshu/canonical/state.py` (1-484 行)
- `src/tongshu/canonical/producer.py` (1-347 行)
- `src/tongshu/canonical/composer.py` (1-158 行)
- `src/tongshu/canonical/condition_evaluator.py` (1-401 行)
- `src/tongshu/canonical/root_evaluator.py` (1-122 行)
- `src/tongshu/canonical/root_evaluator_v2.py` (1-156 行)
- `src/tongshu/canonical/tengod_mapper.py` (1-310 行)
- `src/tongshu/canonical/negation_evaluator.py` (1-96 行)
- `src/tongshu/canonical/day_year_evaluator.py` (1-235 行, 已修改在 dirty)
- `src/tongshu/pipeline.py` (1-432 行)
- `src/tongshu/pipeline_stages/compute_stage.py` (1-303 行)
- `src/tongshu/pipeline_stages/validation_stage.py` (1-112 行)
- `src/tongshu/legacy/assertion_v1/engine_adapters.py` (1-128 行)
- `src/tongshu/admin/service.py:73`
- `src/tongshu/api/app.py:589-590`
- `tests/conftest.py:16`
- `tests/test_strength_engine.py` (1-93 行)
- `tests/test_strength_engine_yinyang.py` (1-90 行)
- `tests/test_judgment_engine.py` (1-134 行)
- `tests/test_p2_direction_golden.py` (1-161 行)
- `tests/test_condition_evaluator.py` (1-180 行)
- `tests/test_m2_asset_integration.py`
- `tests/test_ziping_assertion.py`
- `tests/test_assertion_producers.py`
- `tests/test_heluo_context.py:19-27`

---

**审计完成时间**: 2026-08-31  
**审计状态**: 仅发现,**未执行任何修复** (符合 STEP 0 冻结要求)  
**下步**: 等待 Hermes 处置 P0/P1 列表 (建议按 P0-① → P0-② → P0-③ → P1-① 顺序)