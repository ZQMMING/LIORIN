# Production Path Closure Audit

> **审计目标**：回答一个问题——现在到底有几条路径能够最终产生"命理结论"？
> **审计基线**：commit `d87d562` (Step 9 Phase 7.5)
> **审计方式**：全仓库 `src/` 代码扫描 + 调用图追踪 + HTTP 入口可达性验证
> **审计者**：Claude (opencode 独立审计)
> **审计结论**：**2 条独立活的生产管线 + 5 个 HTTP 端点** 可产生最终命理结论；Authority Ledger 完全未被执行；多条死代码残留。

---

## 一、总判定

| 维度 | 结论 |
|------|------|
| 能独立产生最终命理结论的**活管线** | **2 条** |
| 产生最终命理结论的 **HTTP 端点** | **5 个**（2 canonical + 3 admin） |
| Authority Ledger 运行时强制 | **🔴 未强制**（零 `.py` 引用） |
| `infer_verdict()` 旧判定逻辑 | 🟢 死代码（零调用者） |
| `evaluate_strength()` 桩 | 🟡 被 admin 路径调用，但返回 UNRESOLVED |
| 新旧 Assertion 并存 | 🟡 `assertion/`(活-仅admin) + `assertion_v2/`(仅契约) |
| Canonical 与 Admin 管线共享代码 | **🔴 零共享**（完全平行） |

**理想态**：Production Judgment → 唯一 Resolver → 唯一 Authority Ledger。
**现状**：两条平行管线，各自有独立的 Signal/Resolver/Renderer，Ledger 形同虚设。

---

## 二、两条活的生产管线

### 管线 A：Canonical `TONGSHUPipeline`

- **入口**：`src/tongshu/pipeline.py:63` `TONGSHUPipeline`
- **HTTP 端点**：
  - `POST /v1/daily-guide` (`api/app.py:320-344`)
  - `POST /api/reading` (DEPRECATED，alias，`api/app.py:531-553`)
  - CLI `python -m tongshu.main` (`main.py:15`)
- **子路径**：`POST /v1/calculate` (`compute_only=True`) 返回中间 `atomic_claims`/`signals`，无 rendered text
- **输出**：`rendered_text`（最终渲染命理结论）
- **链路**：`ComputeStage`(BaziEngine/ZiweiEngine/HuangliEngine/SignalEngine/CrossAnalyzer/ThemeEngine/HeluoCanonical/YiInterpretationEngine) → `RenderStage`(Renderer/TemplateFallback) → `ValidationStage` → `AuditComposer`
- **Ledger**：绕过（doc-only）

### 管线 B：Admin P3→P5 管线（🔴 关键发现：完全平行）

- **入口**：`src/tongshu/admin/service.py:56` `compute_case_snapshot()`
- **HTTP 端点**：
  - `POST /admin/cases` (`admin/router.py:84-97`) → 返回 `rendered_guidance` markdown
  - `GET /admin/cases/{id}/guidance/rendered` (`admin/router.py:257-276`) → 最终命理结论
  - `POST /admin/playground/run` (`admin/router.py:362-375`)
- **输出**：`rendered_guidance` markdown + `assertions_p4`(含 `direction`) + `composed_guidance`
- **链路**（与 Canonical **零代码共享**）：
  1. `produce_all_evidence()` (`legacy/assertion_v1/engine_adapters.py:558`) → EngineEvidence（内部调 `AssertionEngine`）
  2. `P3SignalEngine.match_evidence()` → SemanticSignal[]
  3. `RuleResolver` → resolved rules
  4. `ContextResolver.resolve()` → **CanonicalAssertion[]（direction 产生于此）**
  5. `AssertionClusterer.cluster()` → AssertionCluster[]
  6. `AssertionGuidanceMapper.map_from_clusters()` → GuidanceAtom[]
  7. `GuidanceComposer.compose()` → ComposedGuidance
  8. `GuidanceRenderer.render_markdown()` → **最终命理结论**
- **Ledger**：完全绕过（Ledger 甚至未提及 P3SignalEngine/ContextResolver/GuidanceComposer/GuidanceRenderer）

**判定**：这是与 Canonical 管线**完全平行的第二条结论生产栈**，使用不同的 Signal 引擎（P3SignalEngine vs SignalEngine）、不同的 Renderer（GuidanceRenderer vs Renderer）、不同的 Composer（GuidanceComposer vs CanonicalComposer）。这是当前最大的"旧系统残留 + 新系统并存"问题。

---

## 三、死代码结论生产者（存在于 src/ 但未接任何生产入口）

| # | 位置 | 产出 | 状态 |
|---|------|------|------|
| 1 | `engines/strength_engine.py:406` `infer_verdict()` | 身强/身弱/从强/从弱 | **零调用者**（仅定义+`__all__`） |
| 2 | `engines/judgment_engine.py:371` `judgment()` | P2JudgmentResult(用神/喜忌) | **仅测试** |
| 3 | `assertion/judgment_production.py:104` `JudgmentProducer.evaluate()` | JudgmentVerdict(APPROVED/HOLD/REJECTED) | **仅测试** |
| 4 | `engines/annual_event_evaluator.py:531` | AnnualPrediction | **仅 `__main__`+测试** |
| 5 | `services/daily_api.py:38` `get_daily_tongshu()` | 硬编码占位结论('火山旅'等) | **仅测试** |
| 6 | `services/daily_state_service.py:48` `compute_daily_state()` | DailyState(能量/建议) | WIP B-06 未接 |

---

## 四、Strength Engine 残留审计

| 符号 | 位置 | 生产可达？ | 旧逻辑是否执行？ |
|------|------|-----------|----------------|
| `evaluate_strength()` | `strength_engine.py:227` | **是**（via `POST /admin/cases`） | **否**——是 UNRESOLVED 桩，返回 `verdict=""`，所有评分逻辑已挖空 |
| `evaluate_strength_features()` | `strength_engine.py:293` | **否**（仅 `scripts/p0_*` 研究脚本） | N/A |
| `infer_verdict()` | `strength_engine.py:406` | **否**（零调用者） | N/A |
| `wang_score` 计算 | `strength_engine.py:376-383` | **否**（仅 `evaluate_strength_features` 内部） | N/A |
| `de_di>=2`/`support_count>drain*1.5` 阈值 | `strength_engine.py:413-415` | **否**（仅 `infer_verdict` 内部） | N/A |

**关键纠正**：审计文档 `CURRENT_STATE.md:133`/`CONFLICT_REGISTRY.md:126` 声称 `evaluate_strength` "0 production calls"，这是**过时/不准确**的。实际调用链：
```
POST /admin/cases (api/app.py:590 → admin/router.py:84)
  → compute_case_snapshot (admin/service.py:87)
    → produce_all_evidence (admin/service.py:108)
      → ADAPTER_REGISTRY[ZI_PING].produce_evidence (engine_adapters.py:542,:569)
        → evaluate_strength(bchart) (engine_adapters.py:55)
```
但函数体是桩，所以 `if sr.verdict:` 分支（`engine_adapters.py:68`）是死的，不产生 `ZP_WANGSHUAI_VERDICT` 证据。`BLOCKER_REGISTRY.md` B-03 关于 admin 暴露 legacy `evaluate_strength` 的判定正确。

---

## 五、Assertion 层并存审计

| 层 | 状态 | 生产可达？ |
|----|------|-----------|
| `assertion/` | **活**——是 `legacy/assertion_v1/` 的 re-export shim；contract/systems/engine_adapters 真实实现 | **是**（仅 admin 路径：`admin/service.py`、`reasoning/assertion_cluster.py`、`reasoning/context_resolver.py`） |
| `legacy/assertion_v1/` | **活实现**——被 admin 路径调用 | **是**（via admin） |
| `assertion_v2/` | **仅契约**——只有 `contract.py`（数据类/枚举），无引擎；仅自身 `__init__` 导入 | **否**（无生产代码引用） |
| `judgment_architecture/` | 研究——`SchoolIsolatedResolver` 仅 `__main__` 测试块调用 | 否 |

**核心问题**：`assertion/` = `legacy/assertion_v1/`（同一份代码），只在 admin 平行管线上活；Canonical 管线完全不触碰 assertion 层。`assertion_v2/` 是契约规格层，尚未有引擎实现。**新旧断言入口物理边界未收敛**。

---

## 六、Authority Ledger 强制审计

`RUNTIME_AUTHORITY_LEDGER.yaml` 是**纯文档**。

- 全仓库 `.py` 文件对 `RUNTIME_AUTHORITY_LEDGER`/`authority_ledger`/`AuthorityLedger` 的引用：**0 处**（grep 确认）
- 无 `LedgerValidator`、无 `assert_authority()`、无 import-time 校验
- 一个 PR 可以把 `BaziEngine` 换成任意实现，代码层零拦截
- Ledger 的 `entry_point` 字段还引用了陈旧路径前缀 `backend/src/tongshu/...`（实际仓库无 `backend/` 前缀）

**判定**：权威源目前 = 约定 + 文档，不是机器可读的运行时治理资产。

---

## 七、收敛方案（唯一权威源）

### 目标态
```
Registry → Authority Ledger → Resolver → Runtime
（唯一）   （机器强制）        （唯一）   （唯一生产链）
```

### P0 — 切断第二条平行管线（最高优先级）
1. **决策点**：Admin P3→P5 管线是"收编进 Canonical"还是"降级为 Research Only"？
   - 若收编：将 `ContextResolver`/`AssertionClusterer`/`GuidanceComposer`/`GuidanceRenderer` 接入 Canonical 管线，删除 admin 独立路径
   - 若降级：`/admin/cases` 系列端点返回 410 或加 `RESEARCH_ONLY` 标记，不对外产生命理结论
2. **理由**：当前 admin 管线绕过 Ledger，且与 Canonical 零代码共享——这是"旧架构偷偷跑"的真实风险点（BLOCKER B-03 已记录但未关闭）

### P1 — 死代码物理移除
3. 删除 `strength_engine.py` 中 `infer_verdict()`（`strength_engine.py:406-432`，含 `__all__` 条目）——零调用者，纯迁移诱饵
4. 删除 `judgment_engine.py` 整文件或迁入 `legacy/` 并加 `RESEARCH_ONLY` 头——仅测试引用
5. 删除 `assertion/judgment_production.py` 的 `JudgmentProducer`——仅测试引用
6. `evaluate_strength_features()` 保留但加 `RESEARCH_ONLY` 强约束（`raise RuntimeError` 若从 `src/tongshu/api|services|pipeline` 导入）

### P2 — Ledger 机器化
7. 实现 `LedgerValidator`：启动时加载 `RUNTIME_AUTHORITY_LEDGER.yaml`，校验所有生产入口的 engine 引用在 Ledger 内
8. 修正 Ledger 的 `entry_point` 路径前缀（`backend/src/tongshu/...` → `src/tongshu/...`）
9. 增加 import-time 断言：生产管线只能实例化 Ledger 列出的 engine

### P3 — Assertion 层收敛
10. 决策：`assertion/`(=legacy v1) 是迁入 `assertion_v2/` 还是保留为 admin 专用？
11. 收敛后，`assertion_v2/` 必须有引擎实现，而非仅契约
12. 删除 `assertion/__init__.py` 对 `legacy/assertion_v1/` 的 re-export shim（强制显式导入路径）

### P4 — Bazi Engine 冻结
13. `bazi_engine.py` 冻结，只接受确定性 Bug 修复，不接受架构改动（避免重引入日主/农历/时区错误）

---

## 八、不建议立即扩张

在上述 P0-P2 完成前，**不应**开始把五部经典从 4 条生产 Judgment 扩展到几十/几百条。理由：第二条平行管线和未强制的 Ledger 意味着新资产可能在非权威路径上被调用，反而放大治理债。

**完成 P0-P2 后，Golden Path 已证明"新架构能跑 + 旧架构不能偷偷跑"，才真正具备扩展资格。**
