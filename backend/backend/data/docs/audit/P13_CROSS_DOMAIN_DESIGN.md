# P1.3 — Cross-Domain Evidence Integration Design

> **设计时间**：2026-09-01
> **状态**：🔒 FINAL（基于 User 裁决补全 6 条边界）
> **基线**：P1.2 冻结（commit 28133c0）

---

## 一、目标

验证：**两个不同体系（子平 + 紫微）进入同一事件上下文时，系统能否保持"互补不比较"**。

不是：
```text
子平 vs 紫微
  ↓
谁更强？谁冲突？
```

而是：
```text
子平 Evidence ──┐
紫微 Evidence ──┼→ EvidenceCoverage（结构性组织）
                │
                └→ 各自独立 Assertion
```

---

## 二、当前架构支持情况

### 2.1 已具备的跨域机制

| 组件 | 当前状态 | P1.3 用途 |
|------|---------|----------|
| `EvidenceCoverage.source_engines` | ✅ 支持多引擎列表 | 记录哪些引擎提供了证据 |
| `EvidenceCoverage.assertion_ids` | ✅ 支持多 Assertion 聚合 | 记录覆盖范围内所有 Assertion |
| `JudgmentRule.MULTI_SOURCE` | ✅ 检查 source_engines 包含关系 | 触发跨体系 Judgment |
| `EvidenceCoverage.evidence_count` | ✅ 仅统计，不参与 Judgment | 记录证据数量（非投票） |

### 2.2 缺失的组件

| 组件 | 说明 | 优先级 |
|------|------|--------|
| `CrossDomainOrchestrator` | 接收多引擎 Evidence，构建 EvidenceCoverage | 🔴 HIGH |
| `cross_domain_assertion_builder` | 合并多个引擎的 Assertion，不做方向比较 | 🔴 HIGH |
| P1.3 集成测试 | 验证 Bazi + Ziwei 共享上下文 | 🔴 HIGH |

---

## 三、6 条硬边界（User 裁决，不可突破）

### 边界 1：Coverage 只做结构性组织，不做 Judgment

允许：
```text
Bazi Evidence
Ziwei Evidence
     ↓
Evidence Coverage
```

**禁止**：
```text
Bazi Assertion  ↕  Ziwei Assertion
                    ↓
              比较 / 投票 / 冲突裁决
```

Coverage 不是新的 Convergence Engine。

### 边界 2：Coverage 不产生新语义结论

Coverage 只能回答：
```text
哪些体系提供了什么 Evidence？
哪些 Evidence 已映射到什么 Atom？
哪些 Assertion 获得了什么体系的授权？
```

**禁止输出**：
```text
更强 / 更可信 / 更准确 / 互相印证所以成立 / 冲突
```

否则 Coverage 会悄悄变成第二套判断引擎。

### 边界 3：必须保持体系 Provenance

EvidenceCoverage 必须按体系分离存储：
```text
EvidenceCoverage
├── by_engine: Dict[str, EngineEvidenceSet]
│   ├── "ZI_PING":
│   │   ├── evidence_ids: List[str]
│   │   └── assertion_ids: List[str]
│   └── "ZI_WEI":
│       ├── evidence_ids: List[str]
│       └── assertion_ids: List[str]
├── domain: str
├── semantic: str
├── evidence_count: int  # 仅统计，不触发 Judgment
└── source_engines: List[str]
```

**禁止**：将两个体系的 Evidence 混成一个无来源集合。

### 边界 4：同一现代语义 ≠ 同一断言

两个体系都映射到 `CAREER_CHANGE` 时：
```text
Bazi → CAREER_CHANGE（来自 Bazi 授权规则）
Ziwei → CAREER_CHANGE（来自 Ziwei 授权规则）
```

**禁止**：
```text
2 个体系都指向 → confidence + 1
2 个体系都指向 → stronger assertion
```

**必须保持**：各自独立的 Assertion，各自独立的授权链。

### 边界 5：Cross-Domain 层禁止拥有 direction 相关字段

CrossDomainOrchestrator 及其产出物的任何字段不得包含：
```text
❌ direction
❌ polarity
❌ strength
❌ confidence
❌ score
❌ weight
```

Cross-Domain 层只处理纯结构关系：
```text
✅ Domain / Evidence / Atom / Assertion / Coverage
```

### 边界 6：必须包含"负向测试"

P1.3 不能只证明正确路径 PASS。

必须主动构造**方向相反**的场景：
```text
Bazi Evidence → Assertion(direction = supportive)
Ziwei Evidence → Assertion(direction = caution)
```

然后验证：
```text
✅ 两个 Assertion 都保留
✅ 不产生 CONFLICTED
✅ 不产生 ALIGNED
✅ 不裁决谁胜出
✅ Coverage 仅记录两套独立证据
```

这是 P1.3 最有价值的一条测试。

---

## 四、最终数据流（P1.3 冻结形态）

```text
                 ┌─ Bazi ── Evidence ── Atom ── Rule ── Assertion ─┐
Event Context ───┤                                                   │
                 └─ Ziwei ─ Evidence ── Atom ── Rule ── Assertion ──┤
                                                                      ↓
                                                           Evidence Coverage
                                                                      ↓
                                                        Structured Observation
```

注意最后输出的是：

> **Structured Observation**

而不是：
> Judgment / Convergence / Resolution

---

## 五、P1.3 测试计划（25 项）

### 5.1 测试文件

```
tests/spec/test_cross_domain_integration.py
```

### 5.2 测试用例

#### Stage 1: Evidence 独立生产（3 tests）

| 用例 | 验证 |
|------|------|
| T1 | Bazi Evidence 无 direction/strength/confidence |
| T2 | Ziwei Evidence 无 direction/strength/confidence |
| T3 | 两套 Evidence 结构独立，互不影响 |

#### Stage 2: Assertion 独立生成（6 tests）

| 用例 | 验证 |
|------|------|
| T4 | Bazi Assertion direction 来自 Bazi 授权规则 |
| T5 | Ziwei Assertion direction 来自 Ziwei 授权规则 |
| T6 | Bazi Assertion 不引用 Ziwei Evidence |
| T7 | Ziwei Assertion 不引用 Bazi Evidence |
| T8 | 两套 Assertion 的 assertion_id 格式正确 |
| T9 | 同一 semantic（如 CAREER_CHANGE）不合并为单一 Assertion |

#### Stage 3: EvidenceCoverage 合并（5 tests）

| 用例 | 验证 |
|------|------|
| T10 | EvidenceCoverage.source_engines 包含 ZI_PING + ZI_WEI |
| T11 | EvidenceCoverage.evidence_count = 各体系证据数之和 |
| T12 | EvidenceCoverage.assertion_ids 包含所有 Assertion |
| T13 | EvidenceCoverage 无 direction/polarity/strength/confidence 字段 |
| T14 | EvidenceCoverage.by_engine 保持体系分离存储 |

#### Stage 4: 禁止行为验证（5 tests）

| 用例 | 验证 |
|------|------|
| T15 | 无 CrossAnalyzer 调用 |
| T16 | 无 ConvergenceArbiter 调用 |
| T17 | 无 evidence_count 阈值触发 Judgment |
| T18 | 无 NEUTRAL fallback |
| T19 | 追溯链完整：Assertion → Rule → Evidence → Engine |

#### Stage 5: 负向测试（3 tests）—— P1.3 灵魂

| 用例 | 验证 |
|------|------|
| T20 | **方向相反场景**：Bazi=supportive + Ziwei=caution，两 Assertion 都保留 |
| T21 | **无 CONFLICTED**：方向相反时不产生 CONFLICTED/ALIGNED/PARTIAL |
| T22 | **无裁决**：方向相反时不判断谁胜出，只做结构性记录 |

#### Stage 6: 真实命例验证（2 tests）

| 用例 | 验证 |
|------|------|
| T23 | 纪晓岚命例：Bazi + Ziwei 同时跑通 |
| T24 | 两套 Assertion 可独立追溯到各自 Engine |
| T25 | Coverage 输出为 Structured Observation（非 Judgment） |

---

## 五、验收红线（严格禁止）

```text
❌ 任何跨引擎 direction 比较
❌ 任何 vote / score / weight / confidence 聚合
❌ 任何 CONFLICTED / ALIGNED / PARTIAL 状态
❌ 任何 evidence_count >= N 触发 Judgment
❌ 任何 NEUTRAL 作为默认 fallback
❌ 任何旧 Signal / CrossAnalyzer / Convergence 调用
❌ 任何强度/置信度数值计算
❌ 任何"哪个体系更准"的推断
```

---

## 六、验收红线（严格禁止）

```text
❌ 任何跨引擎 direction 比较
❌ 任何 vote / score / weight / confidence 聚合
❌ 任何 CONFLICTED / ALIGNED / PARTIAL 状态
❌ 任何 evidence_count >= N 触发 Judgment
❌ 任何 NEUTRAL 作为默认 fallback
❌ 任何旧 Signal / CrossAnalyzer / Convergence 调用
❌ 任何强度/置信度数值计算
❌ 任何"哪个体系更准"的推断
❌ Coverage 产生新语义结论（不是结构性记录）
❌ 同一 semantic 自动合并为更强断言
```

---

## 七、实施步骤

### Phase 1: Design（已完成）
- [x] 本设计文档（含 6 条硬边界）
- [x] User 裁决通过

### Phase 2: Contract Extension
- [ ] 新增 `CrossDomainContext` / `CrossDomainResult`（如需要）
- [ ] 扩展现有 `EvidenceCoverage`（添加 by_engine 分离存储）

### Phase 3: Orchestrator Implementation
- [ ] 实现 `CrossDomainOrchestrator`
- [ ] 实现 `cross_domain_assertion_builder`

### Phase 4: Tests
- [ ] 编写 `test_cross_domain_integration.py`（25 项）
- [ ] 所有红线测试 PASS
- [ ] **负向测试（T20-T22）必须 PASS**

### Phase 5: Audit
- [ ] 独立审计（Claude 只读）
- [ ] 输出 `docs/audit/p1_3_cross_domain_audit.md`

---

## 八、与 P1.2 的关系

| 维度 | P1.2 | P1.3 |
|------|------|------|
| 范围 | 单引擎垂直切片 | 多引擎横向编排 |
| Contract | 建立 Evidence/Atom/Assertion | 复用，不修改 |
| 验证 | 单引擎全链路 | 跨引擎共存验证 |
| 禁止行为 | 方向泄漏/投票 | 同左 + 跨引擎比较 |
| 冻结 | ✅ FROZEN | ✅ FINAL（待实施） |

**关键原则**：
1. P1.3 不得修改 P1.2 已冻结的 Contract
2. Coverage 只做结构性组织，不做 Judgment
3. 同语义不同体系 ≠ 同一断言
4. 方向相反 ≠ CONFLICTED，只是互补证据

---

## 九、P1.3 最终架构冻结

```
                 ┌─ Bazi ── Evidence ── Atom ── Rule ── Assertion ─┐
Event Context ───┤                                                   │
                 └─ Ziwei ─ Evidence ── Atom ── Rule ── Assertion ──┘
                                                                      ↓
                                                           Evidence Coverage
                                                                      ↓
                                                        Structured Observation
```

**最终输出 = Structured Observation**（非 Judgment / Convergence / Resolution）

---

*本文档为 P1.3 最终设计基线，基于 User 裁决补全 6 条硬边界。*
*状态：FINAL — 待实施（Phase 2+ 开始编码）*
