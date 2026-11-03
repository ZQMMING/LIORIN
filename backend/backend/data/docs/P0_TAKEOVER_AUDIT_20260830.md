# PROJECT TAKEOVER AUDIT — Hermes 接手报告

> **生成时间**: 2026-08-30
> **生成者**: Hermes (PMO/Governor)
> **仓库**: https://github.com/ZQMMING/wisdom
> **HEAD**: defbaa2 fix(signal_engine): skip draft rules missing produces_layer_output_template
> **状态**: 仅诊断，未修改任何代码

---

## 1. 当前 HEAD commit

```
defbaa2 fix(signal_engine): skip draft rules missing produces_layer_output_template
b87249a P0-3.3 Evidence→Primitive/Condition结构化提取
aed4c7e P0-3.3 修复strength_engine BOM语法错误 + assertion模块兼容层
ce7409b P0-3.2 全量 Evidence Classification：376条五分类
664439c P0-3.1 交叉验证引擎：Cross-Validation + 50条跨经典抽样
ca719ca 角色分工修正：工程执行者不做裁决，裁决由GPT审计GitHub commit完成
2584e6a P0-3.0 五经Corpus辨证工程化
```

共121 commits，main分支最新。

---

## 2. 当前生产入口

| 端点 | 状态 | 说明 |
|------|------|------|
| `/health` | ✅ ok | renderer=stub, model=stub, v0.2.0 |
| `/v1/calculate` | ✅ 生产 | compute_only模式 |
| `/v1/daily-guide` | ✅ 生产 | LLM渲染模式 |
| `/v1/today` | ✅ 生产 | 公共时间层 |
| NFC端点 | 501下线 | `/daily` `/relationship` `/state` 统一返回501 |

**权威基准**: `docs/SHUNTIAN_V1.3_GOVERNANCE_RESET_权威基准.md`

---

## 3. 当前实际运行引擎

| 引擎 | 生产路径 | 状态 |
|------|----------|------|
| BaziEngine | ✅ 主链 | `src/tongshu/engines/bazi_engine.py:670` |
| ZiweiEngine | ⚠️ 需stub | `TONGSHU_ALLOW_ZIWEI_STUB=1` 否则抛 `ZiweiEngineUnavailableError` |
| HeluoYiEngine | ✅ 已接入 | `src/tongshu/engines/heluo_yi_flow.py` |
| BlindSchoolEngine | ✅ 已接入 | `src/tongshu/assertion/systems.py` |
| YiJingEngine | ✅ 已接入 | `src/tongshu/engines/` |

**关键发现**: 紫微引擎在生产测试中不可用（无stub），导致cross_analysis只能消费单方面信号。

---

## 4. strength_engine 是否仍在生产链

**✅ 是，仍在生产链，5处直接调用**

| 文件 | 行号 | 调用方式 |
|------|------|----------|
| `src/tongshu/engines/annual_event_evaluator.py` | 207 | `evaluate_strength(chart)` |
| `src/tongshu/engines/judgment_engine.py` | 41 | `D1StrengthResult` import |
| `src/tongshu/reasoning/event_topic.py` | 445 | `evaluate_strength(chart)` |
| `src/tongshu/reasoning/health_signals.py` | 99 | `evaluate_strength(chart)` |
| `src/tongshu/legacy/assertion_v1/engine_adapters.py` | 45 | `evaluate_strength(bchart)` |

**⚠️ 问题**: 仍使用 `wang_score >= _WANG_SCORE_THRESHOLD(2.0)` 阈值判定身强，违反P6.1冻结原则"禁止评分/阈值/权重"。

**结论**: 需审计后决定是隔离为Legacy Reference还是逐步替换。

---

## 5. direction/score/vote 是否仍在生产链

**✅ direction/polarity 仍在生产链**

| 位置 | 说明 |
|------|------|
| `src/tongshu/reasoning/signal_engine.py:113-114` | Signal dataclass 含 direction/polarity |
| `data/rules/*.json` | 136条规则中，produces_layer_output_template 含 direction/polarity |
| `src/tongshu/engines/strength_engine.py:75` | `_WANG_SCORE_THRESHOLD = 2.0` |

**❌ SYSTEM_WEIGHTS 已删除** (V13拍板定死)

**关键风险**: Signal层的direction/polarity与五经辨证层需分离——方向应在Assertion层才产生，而非Signal层。

---

## 6. 河洛评分是否仍在生产链

**待审计** — grep未发现明显的"+1/-1"五行评分代码，但需三重取证确认。

**已知**: 河洛Canonical V2.0已冻结(本命→元堂→后天换卦→流年→流月→流日→时刻→节候卦→卦气)。

---

## 7. 五经 Corpus 当前状态

| 组件 | 状态 | 位置 |
|------|------|------|
| Corpus Adapter | ✅ 已完成 | `src/tongshu/corpus/adapter.py` |
| Corpus Audit | ✅ 已完成 | `docs/P0_3_0_CORPUS_AUDIT_REPORT.md` |
| Evidence Candidate Retrieval | ✅ 已完成 | `src/tongshu/corpus/retrieval.py` |
| Cross-Validation (阶段4) | ⏳ 未执行 | — |
| 五经辨证规则工程化 (阶段5) | 🔴 未执行 | — |

**数据规模**: 5部经典 / 376条条目 / 16分类 / 96标签

**证据分类**:
- EXACT_PRIMARY: 已隔离
- PARTIAL: 已隔离
- DERIVED_TEXT: 已隔离(严禁冒充原典)
- NOT_FOUND: 已标记
- CONFLICT: 已记录

---

## 8. Evidence → Primitive → Condition 当前实现

| 层级 | 状态 | 说明 |
|------|------|------|
| Evidence | ✅ 已实现 | 376条五分类，EVIDENCE_STATUS分离 |
| Primitive | ⚠️ 概念研究 | DTS-WS-001~010，但rules中无primitive字段 |
| Condition | ✅ 已实现 | 136条规则均有conditions字段 |
| Local Judgment | 🔴 未实现 | 无代码实现 |
| Composite Judgment | 🔴 未实现 | 无代码实现 |

**断裂点**: Primitive未在rules schema中落地，Evidence→Primitive→Condition链路在Primitive层断裂。

---

## 9. 当前测试真实状态

**Collection errors**: 8个(legacy assertion v1兼容层问题，非生产链路)

**可运行测试**:
- 总计: 1648
- Passed: 1615
- Failed: 3
- Skipped: 5
- xfailed: 1
- xpassed: 7

**3个失败详情**:

| 测试 | 期望 | 实际 | 根因 |
|------|------|------|------|
| `test_v1_calculate_compute_only` | cross=ALIGNED | cross=INSUFFICIENT | signal_engine跳过25条active规则 |
| `test_v1_daily_guide_golden001` | cross=ALIGNED | cross=INSUFFICIENT | 同上 |
| `test_ten_mappings_all_pass` | MAP-1001=PASS | MAP-1001=REVIEW | direction/polarity不匹配 |

---

## 10. 当前最高优先级 3 个问题

### P0-1: signal_engine 跳过active规则导致测试失败
- **影响**: 25条active规则只有`produces_semantic_atoms`，被`_rule_to_signal`跳过
- **后果**: BASELINE只产出1个信号(SIG-ZW-BL-000，紫微stub)，cross_analysis=INSUFFICIENT
- **待裁决**: 是让signal_engine兼容两种格式，还是补充template字段？

### P0-2: strength_engine wang_score阈值仍在生产链
- **影响**: 违反P6.1冻结原则"禁止评分/阈值/权重"
- **位置**: `strength_engine.py:75, 396`
- **待裁决**: 隔离为Legacy Reference or 逐步替换？

### P0-3: Primitive字段未入rules schema
- **影响**: Evidence→Primitive→Condition链路在Primitive层断裂
- **后果**: 无法执行五经辨证的Local Judgment Engine
- **待裁决**: 先补Primitive schema还是先做闭环验证？

---

## 11. 下一批具体开发任务

### T1: signal_engine格式兼容修复 (P0)
- Scope: 让`_rule_to_signal`同时支持`produces_layer_output_template`和`produces_semantic_atoms`
- 或: 补充25条active规则的template字段
- 验收: 3个失败测试变绿，不修改Golden期望值

### T2: strength_engine生产链审计 (P0)
- Scope: 三重取证确认所有调用方，评估隔离方案
- 输出: `docs/P0_STRENGTH_ENGINE_AUDIT.md`
- 裁决: 隔离 or 替换

### T3: Primitive→Condition小闭环验证 (P1)
- Scope: 20-50条规则，完整 Evidence→Primitive→Condition→Local Judgment
- 验收: 可追溯、可验证、UNRESOLVED输出正常

---

## 附录：冻结资产清单

| 资产 | 状态 | 约束 |
|------|------|------|
| Golden Dataset | 受保护 | 禁止修改期望值 |
| 紫微Canonical | BLOCKED | 禁止补算法 |
| NFC端点 | 501下线 | 保留路由 |
| DB双库 | 现状冻结 | 禁止跨库混用 |
| 子初换日规则 | B-02已锚定 | 修改须经User批准 |
| otcg基线行数 | 55rules/52evidence/10mappings | 精确等值断言 |

---

## 附录：待User裁决事项

1. **T1方案选择**: signal_engine兼容两种格式 vs 补充template字段
2. **T2处理方向**: strength_engine隔离为Legacy Reference vs 逐步替换
3. **T3优先级**: 先补Primitive schema还是先做闭环验证

---

*本报告由Hermes生成，未经User裁决前不得作为执行依据。*
*裁决流程: Hermes裁定 → GitHub docs/发布 → 飞书通知User*
