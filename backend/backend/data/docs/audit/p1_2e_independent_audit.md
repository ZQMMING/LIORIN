# P1.2-E: Independent Contract + Runtime Audit

> **审计时间**: 2026-09-02  
> **审计方式**: 只读静态代码分析 + grep 取证  
> **审计范围**: P1.2 阶段新建的所有 Contract 和运行时代码  
> **基线参考**: `p1_2a_contract_design.md`（设计基线）/ `p1_2d_runtime_trace.md`（运行时轨迹）  
> **状态**: 🟡 CONDITIONAL — 发现 3 项 HIGH + 4 项 MEDIUM 风险，无 CRITICAL 违反

---

## 执行摘要

对 P1.2 阶段新建的 11 个文件（6 个 Contract/RuleLibrary + 5 个 EvidenceProducer）完成攻击性审计。新代码在架构隔离方面表现良好：旧组件（SignalEngine / CrossAnalyzer / ConvergenceArbiter / LegacyAdapter / Aggregator）**未被任何新代码 import**，生产路径隔离完整。但发现以下关键风险：

1. **盲派 evidence_producer 将 `zuo_gong_strength`（强度评分）写入 attributes**，与 V13 §五"禁止 strength"冲突
2. **所有 source_rule_ref 指向不存在的规则文件**（rules/ 目录为空），追溯链形同虚设
3. **canonical_source 无验证机制**，仅字符串引用，无法作为实质授权证据
4. **SET_SUBSET 策略可被滥用**：空 keys 已被防御（返回 False），但单键匹配可覆盖大量语义原子

---

## A. direction 泄漏检查

### A1. EngineEvidence 类定义
- **文件**: `src/tongshu/spec/canonical/engine_evidence.py:44-70`
- **结论**: ✅ PASS — 字段列表不含 direction/polarity/strength/confidence，注释明确禁止（line 47）

### A2. EngineEvidence.to_dict()
- **文件**: `src/tongshu/spec/canonical/engine_evidence.py:72-84`
- **结论**: ✅ PASS — 序列化字典不含方向字段

### A3. EvidenceProducer attributes 泄漏
- **文件**: `src/tongshu/engines/blind/evidence_producer.py:97-101`
- **问题**:
  ```python
  attributes={
      "zuo_gong": result.zuo_gong,
      "zuo_gong_type": result.zuo_gong_type,
      "zuo_gong_methods": result.zuo_gong_methods,
      "zuo_gong_strength": result.zuo_gong_strength,  # ← 强度评分 (float 0.0-1.0)
  },
  ```
- **严重度**: **HIGH** — `zuo_gong_strength` 是 `blind_bazi_engine.py:113` 定义的 `float = 0.0`，范围 0.0-1.0，语义上等价于 V13 禁止的 `strength` 字段。虽然标签不同，但下游消费者可从该值推断方向倾向。
- **其余 4 个 Producer**: ✅ 无泄漏（bazi/heluo/yi/ziwei 的 attributes 均仅含结构/数值/位置/时间）

### A4. SemanticAtom 是否携带 direction
- **文件**: `src/tongshu/spec/canonical/semantic_atom.py:19-37`
- **结论**: ✅ PASS — 无 direction 字段

### A5. find_rule 返回 None 时的 fallback
- **文件**: `src/tongshu/assertion/assertion_rule_library.py:88-93`
- **结论**: ✅ PASS — `find_rule()` 返回 None，**无自动 NEUTRAL fallback**
- **注意**: 设计文档 `p1_2a_contract_design.md:423` 和 `p1_2a_contract_design.md:456` 显示伪代码中使用了 `NEUTRAL` fallback，但这是设计文档而非实际代码。实际代码中**不存在 `generate_assertion` 函数**，Assertion 构造由调用方手动完成。

---

## B. hidden scoring 检查

### B1. EvidenceCoverage.evidence_count
- **文件**: `src/tongshu/spec/canonical/judgment.py:26`
- **结论**: ✅ PASS — `evidence_count` 仅作为统计记录，**未被 JudgmentRuleLibrary 用于条件判断**
- **证据**: `judgment_rule_library.py:62-84` 的 `find_judgment()` 只检查 domain + semantic + condition_type，不引用 evidence_count

### B2. JudgmentRule 是否隐含依赖 evidence_count
- **文件**: `src/tongshu/assertion/judgment_rule_library.py:86-131`
- **结论**: ✅ PASS — `_match_condition()` 对所有 condition_type 均不检查 evidence_count：
  - `MULTI_SOURCE`: 检查 source_engines 集合包含关系
  - `TEMPORAL`: 简化返回 True（实际需要调用方传入 context）
  - `ATTRIBUTE`: 简化返回 True
  - `GRAPH`: 检查 `len(assertion_ids) >= len(required_atoms)` — ⚠️ 见 G 项
  - `SINGLE_SOURCE_AUTHORIZED`: 仅检查 canonical_source 非空

### B3. MatchStrategy.SET_SUBSET 滥用风险
- **文件**: `src/tongshu/assertion/assertion_rule_library.py:109-113`
- **结论**: ⚠️ **MEDIUM** — 虽然空 keys 被防御（line 111-112 返回 False），但单键匹配可导致过度泛化：
  ```python
  # 例如 condition={"keys": ["EXPRESSION"]} 会命中所有包含 EXPRESSION 的 atom
  # 无论该 atom 来自哪个引擎、哪个领域
  ```
  这不是直接的"关键词命中自动断言"（需要 rule.direction 存在），但 SET_SUBSET 的条件宽松性可能导致大量不相关 atom 被同一规则覆盖。

### B4. 数值计算涉及 confidence/score/weight
- **结论**: ✅ PASS — 新代码中无任何数值计算涉及这些字段。旧代码（`temporal/convergence.py`, `spec/severity.py`）中存在 `convergence_score`，但不在 P1.2 新代码路径中。

---

## C. NEUTRAL fallback 检查

### C1. find_rule() 返回 None 时
- **结论**: ✅ PASS — 无自动 NEUTRAL fallback。返回 None 即 NO_ASSERTION。

### C2. generate_assertion 默认 direction
- **结论**: ✅ PASS — 代码库中**不存在 `generate_assertion` 函数**。Assertion 的构造由测试代码（`test_vertical_slice.py:298-319`）和运行时测试（`test_vertical_slice_runtime.py:193-214`）手动完成，调用方负责判断 find_rule 返回值。

### C3. NO_ASSERTION vs NEUTRAL 语义区分
- **结论**: ✅ PASS — 两者在概念上清楚区分：
  - `NO_ASSERTION` = `find_rule()` 返回 None，不产出 CanonicalAssertion
  - `NEUTRAL` = `AssertionDirection.NEUTRAL`，是规则明确授权的方向值（如 `ASR-BT-BI_JIAN` 在测试规则中设置了 direction="neutral"）
- **风险**: 调用方必须在 find_rule 返回 None 时**显式决定不产出 Assertion**，否则可能引入隐式 NEUTRAL。但当前测试代码和运行时路径均已正确处理（见 test_vertical_slice.py:319 `no_assertion_count += 1`）。

---

## D. EvidenceCoverage → 投票风险

### D1. evidence_count 触发 Judgment
- **结论**: ✅ PASS — `EvidenceCoverage.evidence_count` 不被 `JudgmentRuleLibrary.find_judgment()` 使用

### D2. source_engines 多源隐式推断
- **结论**: ✅ PASS — `source_engines` 仅在 `MULTI_SOURCE` 条件下作为集合包含检查，不做"多源=更强"的推断

### D3. 跨引擎 direction 比较
- **结论**: ✅ PASS — 新代码中无任何跨引擎 direction 比较逻辑。旧代码 `reasoning/cross_analysis.py` 和 `signal/convergence.py` 存在此类逻辑，但未被新代码 import。

---

## E. Rule Library 授权边界

### E1. AssertionRule.condition 结构化程度
- **文件**: `src/tongshu/assertion/assertion_rule_library.py:48`
- **结论**: ⚠️ **MEDIUM** — condition 是 `Dict[str, Any]`，结构化程度取决于 JSON 编写者。当前策略：
  - EXACT: `{"atom_id": "..."}` — 精确，安全
  - SET_EXACT: `{"keys": [...]}` — 集合相等，安全
  - SET_SUBSET: `{"keys": [...]}` — 子集匹配，可泛化
  - GRAPH: `{"nodes": [...]}` — 安全
  - CONDITION: `{"domain": ..., "temporal_scope": ..., "attributes": {...}}` — 最灵活但也最危险，domain 检查使用 `not in` 过滤，其他可选

### E2. JudgmentRule.condition 显式原典授权
- **结论**: ✅ PASS — 所有 condition_type 均需显式指定，无 evidence_count 阈值

### E3. canonical_source 授权证据充分性
- **文件**: `src/tongshu/assertion/assertion_rule_library.py:50`
- **结论**: 🔴 **HIGH** — `canonical_source` 仅是 `str` 类型，无任何验证机制：
  - 无法验证该原典引用是否真实存在
  - 无法验证该原典是否真的授权了此 direction
  - 可以填写任意字符串（如 `"伪造的来源"`）而代码层面不会报错
  - 建议增加 `verification_status` 字段或 passage_ref 字段以支撑实质授权

---

## F. provenance 完整性

### F1. EngineEvidence 追溯链
- **文件**: `src/tongshu/spec/canonical/engine_evidence.py:55-70`
- **结论**: ✅ PASS — 字段完整：
  - `evidence_id`: 实例唯一 ID
  - `rule_id`: 稳定规则 ID
  - `source_rule_ref`: 规则文件引用（如 `"rules/bazi_stems.json"`）
  - `source_field`: 原始计算字段名（如 `"heavenly_stem"`）
  - `calculation_version`: 计算版本
  - `contract_version`: Contract 版本

### F2. CanonicalAssertion.evidence 字段
- **文件**: `src/tongshu/spec/canonical/assertion.py:40`
- **结论**: ⚠️ **MEDIUM** — `evidence: dict[str, Any]` 是开放结构，追溯深度取决于调用方：
  - 测试代码（`test_vertical_slice.py:393-398`）只存入 `{evidence_ref, engine, value, source_rule_ref}`
  - 运行时测试（`test_vertical_slice_runtime.py:287-296`）存入了更完整的字段（含 `temporal_scope`, `rule_id`, `calculation_version`, `contract_version`）
  - **无强制性完整性约束**：调用方可选择性地省略某些字段
  - 建议在 Contract 层定义 `evidence` 的最小字段集（至少应包含 evidence_id, engine, value, source_rule_ref, source_field）

### F3. source_rule_ref 实际存在性
- **结论**: 🔴 **HIGH** — 所有 EvidenceProducer 的 `source_rule_ref` 指向 `rules/*.json` 文件，但项目中**不存在 `rules/` 目录**：
  - `glob("rules/**/*.json")` 返回空
  - 所有引用（如 `rules/bazi_stems.json`, `rules/bazi_ten_gods.json`, `rules/ziwei_stars.json` 等共 18 个路径）均指向不存在的文件
  - 这意味着追溯链在实际运行时是断裂的

---

## G. EngineEvidence 语义污染

### G1. 各 Producer attributes 判断性值
- **BaziEvidenceProducer**: ✅ 无判断性值 — attributes 仅含 `stem`, `element`, `pillar`, `ten_god`, `branch`, `peach_blossom`, `balance` 等事实字段
- **HeLuoEvidenceProducer**: ✅ 无判断性值 — attributes 仅含 `tian_shu`, `di_shu`, `hexagram_name`, `upper_gua`, `lower_gua`, `yuantang` 等事实字段
- **YiEvidenceProducer**: ✅ 无判断性值 — attributes 仅含 `hexagram_name`, `hexagram_number`, `yao_position`, `yao_text` 等事实字段
- **ZiweiEvidenceProducer**: ✅ 无判断性值 — attributes 仅含 `star`, `palace`, `position`, `sihua`, `is_main` 等事实字段
- **BlindEvidenceProducer**: ⚠️ **MEDIUM** — `zuo_gong_strength`（第 101 行）是一个 float 强度值，语义上编码了做功强度的定量评估。虽然不直接是 direction，但可作为间接推断方向的材料。

### G2. value 字段方向语义
- **结论**: ✅ PASS — value 字段存储的是纯计算结果（天干/地支/十神名/星曜名/卦名），这些是传统命理学中的中性术语，本身不携带方向判断。"伤官"作为 value 是事实描述，方向由 AssertionRule 层授权。

### G3. source_rule_ref 指向真实规则文件
- **结论**: 🔴 **HIGH** — 如上 F3 所述，所有 source_rule_ref 指向的文件不存在。这不仅是追溯完整性问题，还可能影响未来的规则加载和验证。

---

## H. 生产路径隔离

### H1. 旧组件 import 检查
| 旧组件 | 被新代码 import？ | 证据 |
|--------|------------------|------|
| `reasoning.signal_engine.SignalEngine` | ❌ 否 | 5 个 evidence_producer + assertion_rule_library + judgment_rule_library + spec/canonical/*.py 均无此 import |
| `reasoning.cross_analysis.CrossAnalyzer` | ❌ 否 | 同上 |
| `signal.convergence.ConvergenceArbiter` | ❌ 否 | 同上 |
| `signal.aggregator.CanonicalSignalAggregator` | ❌ 否 | 同上 |
| `signal.legacy_adapter` | ❌ 否 | 同上 |

### H2. 新代码依赖旧 Pipeline
- **结论**: ✅ PASS — 新代码（Contract 层 + EvidenceProducer + RuleLibrary）完全独立，不依赖旧 Pipeline

### H3. 旧 Pipeline 仍在运行
- **结论**: ⚠️ **MEDIUM** — 旧 Pipeline 仍在生产路径中：
  - `pipeline.py:26-27` 导入 SignalEngine 和 CrossAnalyzer
  - `pipeline_stages/compute_stage.py:34,37` 导入 CrossAnalyzer 和 SignalEngine
  - `main.py:34` 引用 `result.canonical.cross_analysis['status']`
  - `api/app.py:299,374` 引用 cross_analysis
  - 这意味着新旧两套系统**并行存在**，新代码尚未接管生产入口

### H4. 禁用旧 Pipeline 后新代码独立性
- **结论**: ✅ PASS — 如果禁用旧 Pipeline，新代码可独立运行（证据：测试已通过）

---

## I. spec/canonical/__init__.py 导出检查

- **文件**: `src/tongshu/spec/canonical/__init__.py:15-28`
- **导出列表**:
  ```python
  __all__ = [
      "EngineEvidence",
      "EngineName",
      "TemporalScope",
      "SemanticAtom",
      "CanonicalAssertion",
      "AssertionDirection",
      "EvidenceCoverage",
      "Judgment",
  ]
  ```
- **结论**: ✅ PASS — 正确导出了所有 P1.2 Contract 类，**未意外导出旧类型**（如 CanonicalSignal、EventDirection 等）

---

## 问题清单

| # | 严重度 | 文件:行号 | 问题描述 | 建议修复 |
|---|--------|-----------|----------|----------|
| 1 | **HIGH** | `engines/blind/evidence_producer.py:101` | `zuo_gong_strength`（float 0.0-1.0）写入 EngineEvidence.attributes，违反 V13 §五禁止 strength 的硬约束 | 删除 `zuo_gong_strength` 字段，或将其重命名为中性描述（如 `zuo_gong_method_count`） |
| 2 | **HIGH** | 所有 evidence_producer.py（18 处 source_rule_ref） | `source_rule_ref` 指向不存在的 `rules/*.json` 文件，追溯链在实际运行时断裂 | 创建 `rules/` 目录并填充实际规则文件，或将 source_rule_ref 改为指向已有的 `data/semantic_atoms/*.json` |
| 3 | **HIGH** | `assertion/assertion_rule_library.py:50` + `judgment_rule_library.py:50` | `canonical_source` 仅为 str 字段，无验证机制，可填任意字符串而无代码层面错误 | 增加 `verification_status` 字段（如 "verified"/"unverified"）或 `passage_ref` 指向具体原文段落 |
| 4 | **MEDIUM** | `assertion/assertion_rule_library.py:109-113` | SET_SUBSET 策略条件宽松，单键匹配可覆盖大量语义原子，可能被滥用为"软断言" | 在规则编写规范中明确 SET_SUBSET 的 keys 至少 2 个；或在代码层增加最小 key 数校验 |
| 5 | **MEDIUM** | `spec/canonical/assertion.py:40` | `evidence: dict[str, Any]` 无最小字段约束，调用方可选择性省略追溯字段 | 定义 `MIN_EVIDENCE_FIELDS = {"evidence_ref", "engine", "value", "source_rule_ref", "source_field"}` 并在构造时校验 |
| 6 | **MEDIUM** | `engines/blind/evidence_producer.py:97-101` | `zuo_gong_methods`（list）也可能包含带有方向暗示的描述性文本 | 审查 `zuo_gong_methods` 的内容，确认不含 "吉"/"凶"/"好"/"坏" 等评价性词汇 |
| 7 | **LOW** | `assertion/judgment_rule_library.py:106` | TEMPORAL condition 简化返回 True，未真正检查 temporal_scope | 完善实现，从 assertion_ids 反查 temporal 信息或要求调用方传入 context |
| 8 | **LOW** | `assertion/judgment_rule_library.py:111` | ATTRIBUTE condition 简化返回 True，未真正检查 attributes | 完善实现，从 assertion_ids 反查 attributes 信息 |

---

## 结论

### 架构符合性评分

| 维度 | 评级 | 说明 |
|------|------|------|
| direction 泄漏 | ✅ 通过 | 除 G1 外全部通过 |
| hidden scoring | ✅ 通过 | evidence_count 未被投票逻辑使用 |
| NEUTRAL fallback | ✅ 通过 | find_rule 返回 None，无隐式 NEUTRAL |
| EvidenceCoverage 投票风险 | ✅ 通过 | 无跨引擎方向比较 |
| Rule Library 授权边界 | ⚠️ 部分通过 | condition 结构化，但 canonical_source 无验证 |
| provenance 完整性 | ⚠️ 部分通过 | 字段设计完整，但 source_rule_ref 指向空文件 |
| 语义污染 | ⚠️ 部分通过 | BlindProducer 有 zuo_gong_strength |
| 生产路径隔离 | ✅ 通过 | 新代码零依赖旧组件 |
| __init__.py 导出 | ✅ 通过 | 仅导出新类型 |

### 总体结论

**P1.2 新 Contract 代码在架构隔离和方向冻结方面基本符合 V13 约束**，核心设计原则（direction 仅在 Assertion 层由授权规则产生、禁止 CrossAnalyzer 方向比较、禁止 evidence_count 投票）在代码层面得到严格遵守。

**主要风险集中在三层**：
1. **BlindEvidenceProducer 的 `zuo_gong_strength`**（HIGH #1）— 需要立即修复
2. **source_rule_ref 指向不存在的规则文件**（HIGH #2）— 追溯链形同虚设，需尽快创建规则文件
3. **canonical_source 无验证**（HIGH #3）— 授权机制存在形式化漏洞

建议在进入 P1.2-F 之前修复上述 3 项 HIGH 风险。

---

*审计完成。本报告只读，未修改任何代码文件。*
