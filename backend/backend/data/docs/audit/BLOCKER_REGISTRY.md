# 🚨 BLOCKER REGISTRY — STEP 1 Audit

**审计日期**: 2026-08-31  
**审计者**: Claude (独立审计方)  
**Commit 基线**: aa35031 (STEP0-FREEZE-20260831-054019)  
**方法**: 调用图取证 + 实代码验证 + 文档声明对照 + 测试对象核对

> 本文件列出 STEP 1 审计中发现的**必须解决的阻塞项**(P0 BLOCKER / P1 CRITICAL)。每条记录标明:阻塞主题、严重度、证据、影响范围、建议 Owner、建议 Action。
>
> **重要**:**仅发现,不修复**。所有修复必须经 OpenCode → Claude 复审 → Hermes → User 终裁的提交链。

---

## 阻塞项索引

| # | 严重度 | 主题 | 类别 |
|---|---|---|---|
| B-01 | **P0** | wang_score 阈值判定仍激活 + 全 docs 误指隔离 | 代码真实性 + 文档一致性 |
| B-02 | **P0** | `canonical/state.py:437` 黑名单缺失 `wang_score` | 治理防御失效 |
| B-03 | **P0** | `/admin/cases/compute` HTTP 路径暴露 legacy `evaluate_strength` | 三重取证失误 |
| B-04 | **P0** | 两份 RootConditionEvaluator (v1+v2) 同命名冲突 | 命名冲突 |
| B-05 | **P0** | BRANCH_HIDDEN_STEMS 表分裂(root vs reasoning 权威版) | 事实表分裂 |
| B-06 | **P0** | M2 asset / condition_evaluator 测试全部硬编码 dict | 测试真实性 |
| B-07 | **P0** | yinyang 测试 6 字符串 assertIn | 测试语义破坏 |
| B-08 | **P1** | P0_ISOLATION_PLAN 路径错误 + 调用点遗漏 4/7 | 计划可执行性 = 0 |
| B-09 | **P1** | CanonicalState / 五经辨证未接入生产管线 | 架构未完成 |
| B-10 | **P1** | STEP0_FREEZE_BASELINE.md 含未展开 shell + GATE PASS 自相矛盾 | 治理追溯失效 |
| B-11 | **P1** | HERMES_DISPATCH 声称 M2 14/16 通过,实 23 失败 | 调度事实失实 |
| B-12 | **P1** | p2_direction_golden 加载 golden 但不读 + verdict 守卫失配 | 测试真实性 |
| B-13 | **P1** | assertion producers 预制 pillars + chart={} | 测试真实性 |
| B-14 | **P1** | test_p6c_3c2_permanent_negative return True 模式 | 测试基础设施风险 |
| B-15 | **P1** | validate_token 桩 + lazy auth_gate | 安全桩 |
| B-16 | **P1** | sys.path.insert 多处硬编码(end_to_end.py 路径错误) | 部署脆弱 |
| B-17 | **P1** | _case_cache / _BUCKETS 限流器无限增长 | DoS 放大 |
| B-18 | **P2** | evaluate_strength_features 死代码但被宣传为隔离层 | 治理误信 |
| B-19 | **P2** | strength_engine.py 双 docstring + `from __future__` 失效 | 类型注解语义 |
| B-20 | **P2** | PowerComparisonEvaluator 纯计数比较无原典授权 | 治理潜在风险 |
| B-21 | **P2** | condition_evaluator.evaluate() 收 Dict[str, Any] 而非 CanonicalState | 类型解耦 |
| B-22 | **P2** | canonical/composer.py 与 canonical/state.py 共用包名但无关 | 命名冲突隐患 |
| B-23 | **P2** | ARCHITECTURE_DECISION_RESULT.md:227 ✅ 但模块不存在 | 文档误标 |
| B-24 | **P2** | p0_8_10 系列报告基于 mock dict 模式 | 测试真实性 |

---

## B-01 — P0 — wang_score 阈值判定仍激活 + 全 docs 误指隔离

### 现状描述
- `src/tongshu/engines/strength_engine.py:75` `_WANG_SCORE_THRESHOLD = 2.0` 仍定义
- `src/tongshu/engines/strength_engine.py:353-358` wang_score 计算公式仍激活
- `src/tongshu/engines/strength_engine.py:396` `strong = wang_score >= _WANG_SCORE_THRESHOLD` 仍判定 verdict
- `src/tongshu/engines/strength_engine.py:367,380` 从强/从弱判定仍依赖 `wang_score > 4.0` / `< 1.5`

### 三份权威文档同时误指隔离
1. `docs/T2_GEMINI_VERDICT.md:41` "🟢 **已隔离**"
2. `docs/T2_STRENGTH_ENGINE_AUDIT_VERDICT.md:37,45,56` "wang_score 仅历史记录"
3. `docs/P0_2_LEGACY_STRENGTH_ENGINE_CALL_GRAPH_AUDIT.md:60-73` "legacy/assertion_v1/... ✅ 已隔离"

### 治理原则冲突
- AGENTS.md §5: 禁止 wang_score/root_score 进生产 verdict
- AUDIT_GUIDE.md §4.3: 禁止"五行计分→强弱"
- ARCHITECTURE_V13_FINAL.md: 五经辨证为唯一权威

### 影响
- 决策方基于"已隔离"声明继续推进,实际 wang_score 仍在判定链
- 用户面向 API 路径虽已断(详见 B-03),但 `/admin` 端点 HTTP 可达
- 测试 mock dict 模式使回归无护栏(详见 B-06)

### 建议 Owner
- Hermes (调度 + 决策)
- OpenCode (实现)
- GPT (终裁)

### 建议 Action
1. **KEEP**: 保留 `strength_engine.py` 作为 LEGACY_RESEARCH_ONLY (历史价值)
2. **FIX**: 在 `strength_engine.py:223` 加 `DeprecationWarning` + 在 `__all__` 注明 "PROD-DISABLED"
3. **REMOVE**: 删除 `evaluate_strength` 函数,仅保留 `evaluate_strength_features` (无 verdict)
4. **RESEARCH**: wang_score 是否彻底删除 vs 保留 LEGACY_RESEARCH_ONLY

---

## B-02 — P0 — canonical/state.py:437 黑名单缺失 wang_score

### 现状描述
- `src/tongshu/canonical/state.py:437` `validate()` 拒绝 `strength_score`/`root_score`/`wangshuai_score`/`qiangruo_score`
- 实际生产字段名是 `wang_score` (strength_engine.py:353-358)
- `wangshuai_score` 与 `wang_score` 是不同名字——前者是"旺衰分数"的扩展名,后者是生产实际计算出的字段

### 治理原则冲突
- 这是治理规则存在的核心目的——拦截评分字段混入 CanonicalState
- 实际:守卫封禁了不存在的字段名,放行了实际字段名

### 影响
- 即使有人在 metadata 中塞 `wang_score`,validate() 不会拒绝
- 工程阈值冒充 Canonical 的核心风险无法被防御

### 建议 Owner
- OpenCode (实现修复)
- Claude (复审)

### 建议 Action
1. **FIX**: 在 `state.py:437` 黑名单加入 `wang_score`
2. **TEST**: 加 unit test 验证 `validate(state_with_wang_score)` 抛 `ValidationError`
3. **STALE**: 同步更新 `INDEPENDENT_CODE_AUDIT_REPORT.md` 与 `T2_GEMINI_VERDICT.md`

---

## B-03 — P0 — /admin/cases/compute HTTP 路径暴露 legacy evaluate_strength

### 现状描述
- `src/tongshu/admin/router.py:85` `POST /admin/cases/compute`
- `src/tongshu/admin/service.py:73,108` `produce_all_evidence`
- `src/tongshu/legacy/assertion_v1/engine_adapters.py:42,45` `evaluate_strength(chart)`
- `src/tongshu/legacy/assertion_v1/engine_adapters.py:57-63` `sr.verdict` → evidence `ZP_WANGSHUAI_VERDICT`
- `src/tongshu/legacy/assertion_v1/engine_adapters.py:104-112` 扶抑喜忌 elements 派生
- `src/tongshu/api/app.py:589-590` `include_router(admin_router)` 无 feature flag / 鉴权筛选

### 完整 HTTP 路径
```
POST /admin/cases/compute
  → admin/router.py:85
  → admin/service.py:73, 108
  → legacy/assertion_v1/engine_adapters.py:42, 45
  → strength_engine.py:396 (verdict = wang_score >= 2.0)
  → engine_adapters.py:57-63 (ZP_WANGSHUAI_VERDICT evidence)
  → engine_adapters.py:104-112 (扶抑喜忌)
```

### 三重取证失误证据
- `docs/audit/P0_ISOLATION_PLAN.md` 列 3 个调用点,这是唯一 HTTP 可达的活路径,**未被任何文档列出**
- `docs/P0_2_LEGACY_STRENGTH_ENGINE_CALL_GRAPH_AUDIT.md:73` 明确声称"已隔离,不影响生产路径"
- `docs/audit/HERMES_DISPATCH_STEP1_*.md:28` 关注 3 个 ORPHAN,跳过 `/admin` 活路径

### 影响
- 用户面向 API 路径 (`/api/reading`, `/v1/daily-guide`, `/api/today`) 0 调用——已断
- 但 `/admin` HTTP 端点**无鉴权筛选,公网可达时**直接触发 verdict 链
- 任何修复必须切这条路径,否则 P0 隔离无效

### 建议 Owner
- Hermes (决定策略:删除 / 留作 LEGACY_RESEARCH)
- OpenCode (实现)

### 建议 Action
1. **FIX**: 在 `api/app.py:589-590` 加 feature flag (`TONGSHU_ADMIN_ROUTER_ENABLED`),默认 false
2. **FIX**: 在 `admin/router.py:85` 加 `Depends(require_admin_role)` 鉴权
3. **REMOVE**: 如 admin router 不再需要,直接 `uninclude_router`
4. **STALE**: 修正 `P0_ISOLATION_PLAN.md` 与 `CALL_GRAPH_AUDIT.md` 加入此路径

---

## B-04 — P0 — 两份 RootConditionEvaluator (v1+v2) 同命名冲突

### 现状描述
- `src/tongshu/canonical/root_evaluator.py:35` `class RootConditionEvaluator(BaseConditionEvaluator)` (v1)
- `src/tongshu/canonical/root_evaluator_v2.py:22` `class RootConditionEvaluator(BaseConditionEvaluator)` (v2)
- 两份同名类,均无生产 consumer

### 影响
- Python 缓存机制只解析一个——任何 import `RootConditionEvaluator` 的代码可能拿到非预期版本
- BRANCH_HIDDEN_STEMS 表分裂(见 B-05)
- 测试无法同时跑两份

### 建议 Owner
- OpenCode
- Claude (复审)

### 建议 Action
1. **FIX**: 决定 v1 vs v2,删除其一
2. **REMOVE**: 若两者均 dead code,删除整个 `root_evaluator.py` 与 `root_evaluator_v2.py`,仅保留 BRANCH_HIDDEN_STEMS 常量(移到 `bazi_ten_gods.py`)

---

## B-05 — P0 — BRANCH_HIDDEN_STEMS 表分裂

### 现状描述
- `src/tongshu/canonical/root_evaluator.py:18-31` 自带一份 `BRANCH_HIDDEN_STEMS`
- `src/tongshu/reasoning/bazi_ten_gods.py` 权威版本

### 影响
- 两份独立副本,可能漂移
- consumer 应使用权威版,但 `root_evaluator.py` 用了本地副本
- 若两份不一致,同一地支的"藏干"判定会有不同结果

### 建议 Owner
- OpenCode

### 建议 Action
1. **FIX**: 删除 `root_evaluator.py:18-31` 的副本,改为 `from tongshu.reasoning.bazi_ten_gods import BRANCH_HIDDEN_STEMS`
2. **TEST**: 加 unit test 验证两份表 hash 一致
3. **STALE**: 同步 ARCHITECTURE 文档

---

## B-06 — P0 — M2 asset / condition_evaluator 测试全部硬编码 dict

### 现状描述
- `tests/test_condition_evaluator.py:29-35` `canonical_state = {"ten_gods_distribution": {"YIN_XING": 1, "QI_SHA": 2}}`
- `tests/test_m2_asset_integration.py:40-44` 同模式
- 8 个 M2 asset 测试文件,~120 个 case,均使用字面 dict

### 影响
- 测试用字面 dict 评估,`BaziEngine.compute()` 或 `CanonicalStateProducer.produce()` 一旦回归,**全部仍绿**
- "测试通过 ≠ 生产正确"
- pytest baseline 23 例失败中,20 例是 M2 asset 测试——这些测试既无法验证生产,也无法识别生产错误

### 建议 Owner
- OpenCode
- Claude (复审)

### 建议 Action
1. **FIX**: 重写 M2 asset 测试,使用真实 `BaziChart` / `CanonicalState` 对象而非字面 dict
2. **FIX**: 在 conftest 提供 fixture factory,生成已知命例
3. **REMOVE**: 若测试无法改造为真实生产对象,删除它们并接受覆盖率损失

---

## B-07 — P0 — yinyang 测试 6 字符串 assertIn

### 现状描述
- `tests/test_strength_engine_yinyang.py:33, 61` `self.assertIn(r.verdict, ("身强", "从强", "从强(假)", "身弱", "从弱", "从弱(假)"))`

### 影响
- 即使 `evaluate_strength` 把所有命例坍缩成"身强",测试全过
- 文件 docstring 声称"P2-D1R1 阴阳修正"被证伪时,无护栏
- 6 字符串中任何被命中即算通过,等同于"verdict 是 6 个之一"

### 建议 Owner
- OpenCode
- Claude (复审)

### 建议 Action
1. **FIX**: 替换为 `assertEqual(r.verdict, expected_verdict_per_case)`
2. **FIX**: 每个 case 期望值写明("阴阳从格 P2-D1R1 矩阵"已在 `tests/test_strength_engine.py:80-88`)
3. **REMOVE**: 若无法构造精确控制命例,删除这些测试并接受损失

---

## B-08 — P1 — P0_ISOLATION_PLAN 路径错误 + 调用点遗漏 4/7

### 现状描述
- `docs/audit/P0_ISOLATION_PLAN.md:11-19` 文件路径声称在 `canonical/`,实际在 `engines/` + `reasoning/`
- 调用链图仅列 3 个调用点,实际 7 个

### 影响
- 计划可执行性 = 0
- 按计划修复会修错文件
- 即使路径正确,按计划修复会遗漏 4 个调用点(其中 `engine_adapters.py:42,45` 是唯一 HTTP 可达的活路径)

### 建议 Owner
- Hermes (重写计划)
- Claude (复审)

### 建议 Action
1. **FIX**: 重写 `P0_ISOLATION_PLAN.md`,使用真实路径
2. **FIX**: 列出全部 7 个调用点 + 7 个间接 verdict 传播点
3. **FIX**: 加"生产入口链"验证——`/admin` HTTP 路径必须列出

---

## B-09 — P1 — CanonicalState / 五经辨证未接入生产管线

### 现状描述
- `src/tongshu/canonical/state.py:334` `CanonicalState` dataclass 定义
- `src/tongshu/canonical/producer.py:35` `CanonicalStateProducer` 算法
- `src/tongshu/canonical/composer.py` `CanonicalComposer` 已运行 pipeline(但数据源是 BaziChart + Signals,与 CanonicalState 无关)
- `src/tongshu/canonical/condition_evaluator.py` 多 Evaluator 实现
- **生产代码 0 调用方**——`grep -r "CanonicalStateProducer\|producer.produce" src/tongshu/` 仅命中 producer.py 自引用

### 影响
- 五经辨证作为"替代 wang_score 的方案"已声明,但与 `compute_stage.py:138-148` 路径完全平行,互不连通
- AGENTS.md §2 描述的"辨证中间状态容器"是空骨架

### 建议 Owner
- OpenCode (实现 glue code)
- Claude (复审)
- Hermes (协调)

### 建议 Action
1. **FIX**: 在 `compute_stage.py:148` 后调 `producer.produce(chart)` 构造 `CanonicalState`
2. **FIX**: 在 `compute_stage.py` 末尾调 `condition_evaluator.evaluate(state)` 收集 condition results
3. **FIX**: 在 `render_stage.py` 前读 verdict(若 UNRESOLVED 则 fail-closed)

---

## B-10 — P1 — STEP0_FREEZE_BASELINE.md 含未展开 shell + GATE PASS 自相矛盾

### 现状描述
- `docs/audit/STEP0_FREEZE_BASELINE.md:32-35` 含字面 `$(cat ...)` 占位符
- `docs/audit/STEP0_FREEZE_COMPLETE.md:69` 声称 pytest PASS,`:31` 承认失败
- `pytest-baseline-20260831-054019.log` last line `23 failed, 1772 passed`

### 影响
- "冻结基线 = 0 数字"的空 artifact
- 治理追溯性失效——无法判断冻结点的真实状态
- 后续 STEP 1-6 的基线对比无据

### 建议 Owner
- Hermes

### 建议 Action
1. **FIX**: 重跑 shell 命令,真实值替换 `STEP0_FREEZE_BASELINE.md` 占位符
2. **FIX**: `STEP0_FREEZE_COMPLETE.md` GATE 表同步承认失败,标 ⚠️ FAIL
3. **RESEARCH**: 是否需要"修复" 23 例失败 vs 承认 baseline 含已知失败

---

## B-11 — P1 — HERMES_DISPATCH 声称 M2 14/16 通过,实 23 失败

### 现状描述
- `docs/audit/HERMES_DISPATCH_STEP1_*.md:72-73` (两份 dispatch 同 Task ID) "M2资产验证进度: 14/16 (87.5%)"
- pytest baseline 23 例失败,其中 20 例是 M2 asset 测试

### 影响
- 调度方对进度的乐观声明与测试实况严重不符
- 用户(User 终裁)基于乐观声明推进,实际进度落后 10+ 测试

### 建议 Owner
- Hermes (重新计算真实进度)

### 建议 Action
1. **FIX**: 重新跑 pytest,统计 M2 asset 真实通过率
2. **STALE**: 修正 `HERMES_DISPATCH_STEP1_*.md` 中数字
3. **RESEARCH**: 是否承认 STEP 1 起点 baseline 含 23 失败

---

## B-12 — P1 — p2_direction_golden 加载 golden 但不读 + verdict 守卫失配

### 现状描述
- `tests/test_p2_direction_golden.py:25-26` `self.golden_data = json.loads(golden_path.read_text(encoding="utf-8"))` 但从不读取
- 6 个 `test_body_*` 方法无 `self.golden_data` 引用
- `tests/test_judgment_engine.py:81` `if "身强" in r.verdict_from_d1 or "从强" in r.verdict_from_d1: assertIn("OFFICIAL", r.favorable)` — verdict 不含"身强"时内部断言全跳过

### 影响
- 文件名 "Golden" 误导,实际断言 `len(favorable_elements) > 0` 不与 golden 对齐
- verdict 错误时不报警

### 建议 Owner
- OpenCode
- Claude (复审)

### 建议 Action
1. **FIX**: 让 `test_body_*` 方法实际使用 `self.golden_data` 比对 favorable/unfavorable
2. **FIX**: 删除 `test_judgment_engine.py:81` 守卫,直接断言
3. **REMOVE**: 若无法构造 golden 一致性,删除守卫并接受损失

---

## B-13 — P1 — assertion producers 预制 pillars + chart={}

### 现状描述
- `tests/test_ziping_assertion.py:24-31` `self.context = {"bazi": [("甲","寅"),...], ...}; a = p.produce(self.inp, chart={}, context=self.context)`
- `tests/test_assertion_producers.py:33-41` 同模式

### 影响
- `chart={}` 是空 dict,`BaziEngine.compute()` 从未被调用
- `BaziChart` 回归时这些测试仍绿

### 建议 Owner
- OpenCode

### 建议 Action
1. **FIX**: 用真实 `BaziChart` 对象替代 `chart={}`
2. **FIX**: 让 `assertion_producers` 测试覆盖 `BaziEngine.compute()` 真实输出
3. **REMOVE**: 若 producer 内部不接受 chart,改 producer 接口

---

## B-14 — P1 — test_p6c_3c2_permanent_negative return True 模式

### 现状描述
- `tests/test_p6c_3c2_permanent_negative.py` 所有测试函数以 `return True` 结尾
- pytest 警告: `PytestReturnNotNoneWarning: Test functions should return None, but ... returned <class 'bool'>.`

### 影响
- 即使内部 assert 全部失败,函数末尾 return True 让 pytest 报告通过
- 测试基础设施层面的真实性问题

### 建议 Owner
- OpenCode

### 建议 Action
1. **FIX**: 删除所有 `return True`,改为 `assert ...` 模式
2. **TEST**: 跑 pytest,确认 23 失败中是否有部分被掩盖

---

## B-15 — P1 — validate_token 桩 + lazy auth_gate

### 现状描述
- `src/tongshu/services/daily_api.py:77-82` `validate_token()` 是长度检查桩,任何 ≥16 字符字符串通过
- `src/tongshu/api/deps.py:67-73, 220-235` `TONGSHU_AUTH_ENFORCED` 默认 `false`
- 注释 "实际应查询数据库验证"

### 影响
- 任何带 16+ 字符 token 的请求都被认作已认证用户
- 若 daily_api 被接入公开路由,严重安全事故

### 建议 Owner
- OpenCode (修复桩)
- Hermes (确认 deploy runbook 有 flag-flip 步骤)

### 建议 Action
1. **FIX**: 替换 `validate_token` 为真实 DB 查询
2. **FIX**: 在 `TONGSHU_AUTH_ENFORCED` 默认值改为 `true`(或显式 fail-closed 模式)
3. **DOC**: 部署 runbook 加 `TONGSHU_AUTH_ENFORCED=true` flip 步骤

---

## B-16 — P1 — sys.path.insert 多处硬编码

### 现状描述
- `src/tongshu/v_validation/end_to_end.py:16` `sys.path.insert(0, str(Path("D:/today/backend/src")))` — **错误路径**(旧目录)
- `src/tongshu/canonical/root_evaluator_v2.py:151` `sys.path.insert(0, "/d/shuntian/backend")` — **绝对路径**,其他机器必破
- 5 处相对/计算路径(annual_event_evaluator.py:32 / g3_safety.py:51 / daily_state_service.py:15 / context_assembler.py:27 / l2_direction.py:23)

### 影响
- end_to_end.py 在其他机器上 fail
- root_evaluator_v2.py 在 Linux/Mac 上 fail

### 建议 Owner
- OpenCode

### 建议 Action
1. **FIX**: 删除 end_to_end.py:16 sys.path.insert(改用 `pip install -e .`)
2. **FIX**: 删除 root_evaluator_v2.py:151 绝对路径
3. **FIX**: 改用 PYTHONPATH 环境变量或 `setup.py` 配置

---

## B-17 — P1 — _case_cache / _BUCKETS 限流器无限增长

### 现状描述
- `src/tongshu/admin/router.py:36` `_case_cache: dict[str, Any] = {}` 无淘汰
- `src/tongshu/api/deps.py:282-299` `_BUCKETS[name]._requests[key]` 无淘汰,高基数 key 下放大 DoS

### 影响
- long-running admin process OOM
- DoS 放大向量

### 建议 Owner
- OpenCode

### 建议 Action
1. **FIX**: 用 `functools.lru_cache` 或 `cachetools.LRUCache(maxsize=N)`
2. **FIX**: `_BUCKETS` 加 TTL + size cap

---

## B-18 — P2 — evaluate_strength_features 死代码但被宣传为隔离层

### 现状描述
- `src/tongshu/engines/strength_engine.py:476, 589` `evaluate_strength_features()` 与 `infer_verdict()` 定义
- **生产代码 0 调用**
- **测试代码 0 调用**
- **唯一调用**: `scripts/p0_3_9_real_integration.py:16, 156`
- `docs/T2_STRENGTH_ENGINE_AUDIT_VERDICT.md` 仍宣传为 "clean layer"

### 建议 Action
1. **RESEARCH**: V4 隔离层方向是否正确
2. **FIX**: 若方向正确,真正接入 `compute_stage.py`
3. **REMOVE**: 若方向错误,删除函数

---

## B-19 — P2 — strength_engine.py 双 docstring + from __future__ 失效

### 现状描述
- `src/tongshu/engines/strength_engine.py:1-7` 第一个字符串字面量(LEGACY 声明)
- `src/tongshu/engines/strength_engine.py:8-32` 第二个字符串字面量(D1 契约规范)
- `from __future__ import annotations` 在第 2 行嵌进字符串字面量内部,**不生效**

### 影响
- Python 模块的 postponed-annotation 在此模块静默失效

### 建议 Action
1. **FIX**: 合并两段 docstring 为一个
2. **FIX**: 将 `from __future__ import annotations` 移到所有字符串字面量之后

---

## B-20 — P2 — PowerComparisonEvaluator 纯计数比较无原典授权

### 现状描述
- `src/tongshu/canonical/condition_evaluator.py:144-210` `PowerComparisonEvaluator` 用 count 比较
- TODO 注释: "后续实现真正的力量计算（基于月令、通根等）" (line 167-170)

### 影响
- 一旦连通到生产,即可激活"按 count 授权 verdict"
- 无原典授权

### 建议 Action
1. **FIX**: 引用五经中"力量对比"的原典章节
2. **FIX**: 删除 TODO,实现真正的力量计算
3. **REMOVE**: 若无法找到原典,删除 evaluator

---

## B-21 — P2 — condition_evaluator.evaluate() 收 Dict[str, Any]

### 现状描述
- `src/tongshu/canonical/condition_evaluator.py:80+` `evaluate(canonical_state: Dict[str, Any])`
- 与 `state.py:334` `CanonicalState` dataclass 无关

### 建议 Action
1. **FIX**: 改为 `evaluate(state: CanonicalState)`
2. **FIX**: 在 `condition_evaluator.py` 与 `state.py` 之间建立类型约束

---

## B-22 — P2 — canonical/composer.py 与 canonical/state.py 共用包名但无关

### 现状描述
- `src/tongshu/canonical/composer.py` = `CanonicalComposer` 从 `Signal`/`CrossResult` 构造 `CanonicalContent` (V1 render path)
- `src/tongshu/canonical/state.py` = `CanonicalState` dataclass,五经辨证替代方案
- 两个不同的 "canonical" 含义在同一个 package 下共存

### 建议 Action
1. **FIX**: 重命名 `composer.py` 为 `signal_renderer.py` 或类似,避免命名冲突
2. **DOC**: ARCHITECTURE 文档同步

---

## B-23 — P2 — ARCHITECTURE_DECISION_RESULT.md:227 ✅ 但模块不存在

### 现状描述
- `docs/ARCHITECTURE_DECISION_RESULT.md:227` 裁决 3 ✅ "canonical_state + canonical_state_engine"
- `find src -name "*canonical_state*"` → 无结果

### 建议 Action
1. **FIX**: 改为 ⏳ NOT-STARTED
2. **STALE**: 同步 AGENTS.md 权威指针

---

## B-24 — P2 — p0_8_10 系列报告基于 mock dict 模式

### 现状描述
- `p0_8_10/M3_PHASE2_STRICT_FINAL_REPORT_V6.md` 等 12 份报告声称 "14/16 测试通过"
- 基于 mock dict + 字面 evaluator.evaluate(state_dict)

### 建议 Action
1. **STALE**: 修正报告,说明测试真实性问题
2. **REMOVE**: 删除基于 mock 的测试结论

---

## 阻塞项统计

| 严重度 | 数量 |
|---|---|
| **P0 BLOCKER** | 7 (B-01, B-02, B-03, B-04, B-05, B-06, B-07) |
| **P1 CRITICAL** | 10 (B-08, B-09, B-10, B-11, B-12, B-13, B-14, B-15, B-16, B-17) |
| **P2 IMPORTANT** | 7 (B-18, B-19, B-20, B-21, B-22, B-23, B-24) |
| **RESEARCH** | (各 P0/P1 内含 RESEARCH 决策项) |

**总阻塞项数**: 24

---

## 处理顺序建议

按以下顺序处理 P0/P1(根据依赖关系):

1. **B-02** (state.py 黑名单修复) — 改动小,可独立完成
2. **B-04 / B-05** (RootConditionEvaluator + BRANCH_HIDDEN_STEMS) — 同主题
3. **B-06 / B-07** (测试真实性) — 涉及测试重写,需要协调
4. **B-01 / B-03** (wang_score + /admin 路径) — 核心治理,需要 Hermes 决策
5. **B-08** (P0_ISOLATION_PLAN 重写) — 依赖 B-01/B-03 决策
6. **B-09** (CanonicalState 接入) — 架构改动,需要 Claude 复审
7. **B-10 / B-11** (GATE + Dispatch 修正) — 文档级
8. **B-12 / B-13 / B-14** (测试真实性) — 与 B-06 协调
9. **B-15** (validate_token) — 安全桩
10. **B-16 / B-17** (sys.path / 缓存) — 工程 hygiene

---

## 风险与决策

### 风险 1: B-01 wang_score 真的需要彻底删除吗?
**置信度**: 中等  
**分析**:
- wang_score 是历史研究产物,有些命理研究者仍依赖它
- 但生产 verdict 链不应使用它(违反 AGENTS.md §5)
- 折中方案:保留 `strength_engine.py` 作为 LEGACY_RESEARCH_ONLY,加 `DeprecationWarning` + 环境变量 gate

### 风险 2: B-09 CanonicalState 接入可能引入新风险
**置信度**: 高  
**分析**:
- canonical/ 包未与生产 pipeline 验证过
- 一旦接入,可能触发"五经辨证 vs 工程阈值"的双轨冲突
- 建议:**先在只读 audit 路径试运行,确认 verdict = UNRESOLVED 时正确 fail-closed**

### 风险 3: B-03 /admin 路径若关闭,会破坏什么?
**置信度**: 中等  
**分析**:
- /admin 路由是 admin 内部观测端点,关闭不影响用户面向 API
- 但 admin 工具依赖此端点做 verification
- 建议:**加 feature flag 而非删除**

---

**审计完成时间**: 2026-08-31  
**审计原则**: 只发现不修复  
**下步**: 等待 Hermes 处置 P0 列表(7 项),按建议顺序开展修复