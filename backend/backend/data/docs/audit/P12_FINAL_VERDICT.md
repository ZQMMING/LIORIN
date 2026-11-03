# P1.2 阶段总裁决 — Signal Contract Unification

> **拍板时间**：2026-09-01
> **状态**：🔒 FROZEN
> **基线 commit**：28133c0

---

## 一、总裁决结论

**P1.2 全部完成，正式冻结。**

P1.2 的目标是：**将生产路径从旧 Signal Runtime 迁移到 V13 定义的 Evidence → Atom → Assertion → Judgment 架构**。

经过 11 个 commit、3 轮独立审计、7 次用户裁决修正，最终确认：

```
✅ P1.2-A  Contract Design          — 787行设计文档
✅ P1.2-B  Contract Implementation  — 17个新文件，+1394行
✅ P1.2-B.1 Contract Correction     — MatchStrategy结构化/删除evidence_count/NO_ASSERTION
✅ P1.2-C  Vertical Slice (子平)    — 18 tests PASS
✅ P1.2-D  Real Bazi Runtime        — 11 tests PASS（真实纪晓岚命例）
✅ P1.2-E  Independent Audit        — 3 HIGH + 4 MEDIUM + 2 LOW
✅ P1.2-F  Contract Remediation     — 修复全部 HIGH/MEDIUM
✅ P1.2-F.1 Provenance Gate         — 索引迁移+状态分层
✅ P1.2-F.1.1 Gate Hardening        — 路径修复+Rule ID一致性
✅ P1.2-F.1.2 Canonical Rule Binding — 28/32 entries绑定
✅ P1.2-G  Ziwei Runtime            — 13 tests PASS
```

---

## 二、架构最终形态

### 2.1 核心数据链（V13 §二冻结）

```
Deterministic Engine（子平/紫微/盲派/河洛/易经）
        │
        ▼
EngineEvidence（纯事实）
  evidence_id: str           ← 实例唯一（与 rule_id 分离）
  engine: EngineName
  rule_id: str               ← 稳定规则ID
  value: Any                 ← 原始计算值
  temporal_scope: TemporalScope
  attributes: dict           ← 附加属性（无方向/强度）
  source_rule_ref: str       ← 指向 data/rules/*.json
  source_field: str
  calculation_version: str   ← 可演进
  contract_version: str      ← 冻结 v13.0

        │ 查表（data/semantic_atoms/*.json）
        ▼
SemanticAtom（语义原子）
  atom_id: str
  engine: EngineName
  evidence_ref: str          ← 追溯到 EngineEvidence.evidence_id
  semantic_keys: List[str]
  domain_candidates: List[str]  ← 候选领域，不预分配
  label_zh: str
  category: str

        │ + AuthorizedAssertionRule
        ▼
CanonicalAssertion（授权断言）
  assertion_id: str
  subject: str               ← case_id
  domain: str                ← 来自 Mapping Layer
  semantic: str
  direction: AssertionDirection  ← ONLY 此处产生（supportive/caution/neutral）
  temporal_scope: str
  source_engine: str
  source_rule: str
  authorized_rule_id: str    ← 授权此 direction 的规则ID
  evidence: EvidenceRef      ← 结构化追溯引用

        │ 结构性组织（不比较方向）
        ▼
EvidenceCoverage（证据覆盖面）
  domain: str
  semantic: str
  evidence_count: int        ← 仅统计，不触发Judgment
  source_engines: List[str]
  evidence_types: List[str]
  assertion_ids: List[str]

        │ + AuthorizedJudgmentRule
        ▼
Judgment（授权判断）
  judgment_id: str
  domain: str
  semantic: str
  evidence_coverage: EvidenceCoverage
  authorized_by: str         ← 授权规则ID
  supporting_assertions: List[str]
```

### 2.2 严格禁止（V13 §四冻结）

以下任何字段/机制**禁止出现在以下层级**：

| 禁止项 | 禁止层级 | 替代方案 |
|--------|---------|---------|
| `direction` | EngineEvidence / SemanticAtom | 仅在 CanonicalAssertion 由规则授权产生 |
| `polarity` | 所有新层 | 已废除 |
| `strength` | EngineEvidence / SemanticAtom | 仅保留结构性事实 |
| `confidence` | 所有新层 | 已废除 |
| `intensity: 0-100` | CanonicalAssertion | 已删除，禁止重新引入 |
| `CONFLICTED` | 跨体系比较 | 已废除，反方向=算法问题 |
| `evidence_count >= N` | Judgment 触发条件 | 禁止数量阈值，需原典授权规则 |
| `Vote / Weight / Score` | 所有新层 | 已废除 |
| `NEUTRAL as default` | find_rule() fallback | 返回 None（NO_ASSERTION），不是 NEUTRAL |

### 2.3 生产调用链（当前新架构）

```
BaziEngine.compute()
  → BaziEvidenceProducer.produce()
    → list[EngineEvidence]（无方向/强度）

ZiweiEngine.compute() (stub)
  → ZiweiEvidenceProducer.produce()
    → list[EngineEvidence]（无方向/强度）

AssertionRuleLibrary.load("data/rules_index/*.json")
  → find_rule(atom, context)
    → Optional[AssertionRule]（None = NO_ASSERTION）

JudgmentRuleLibrary.load()
  → find_judgment(coverage)
    → Optional[JudgmentRule]（需原典授权）
```

---

## 三、Provenance 分层模型

### 3.1 三层分离

```
┌──────────────────────────────────────────────────────────┐
│ Layer 1: Engine Evidence（计算事实）                       │
│   文件: data/rules/<engine>_<category>.json              │
│   状态: calculation_version 可演进                        │
└──────────────────────────────────────────────────────────┘
                          ↓ ref
┌──────────────────────────────────────────────────────────┐
│ Layer 2: Canonical Rule（原典授权）                        │
│   文件: data/rules/*.json                                │
│   状态: verification_status + admission_status           │
│   要求: rule_id + title + source + conditions + conclusion│
└──────────────────────────────────────────────────────────┘
                          ↓ canonical_rule_id
┌──────────────────────────────────────────────────────────┐
│ Layer 3: Assertion Rule（断言授权）                        │
│   文件: data/rules_index/*.json                          │
│   状态: status=index, verification_status=unverified     │
│   要求: evidence_rule_id + canonical_rule_id + ref       │
└──────────────────────────────────────────────────────────┘
```

### 3.2 Status 枚举

```
verification_status:
  - unverified    ← 初始状态（默认）
  - verified      ← 原典核验通过
  - rejected      ← 核验失败

admission_status:
  - candidate     ← 初始状态（默认）
  - approved      ← 通过 Rule Admission
  - production    ← 进入生产资产库
```

### 3.3 Index Entry 格式

```json
{
  "rule_id": "ZP_STEM_YEAR",
  "ref": "data/rules/ZPZ-101.json",
  "canonical_rule_id": "ZPZ-101",
  "field": "heavenly_stem",
  "pillar": "year"
}
```

---

## 四、当前测试覆盖

### 4.1 单元测试（P1.2-C）

| 测试文件 | 用例数 | 覆盖 |
|---------|-------|------|
| `test_vertical_slice.py` | 18 | 子平垂直切片（虚构 chart） |
| `test_contract_gate.py` | — | 跨 Schema 导入检查 |

### 4.2 运行时测试（P1.2-D）

| 测试文件 | 用例数 | 覆盖 |
|---------|-------|------|
| `test_vertical_slice_runtime.py` | 11 | 真实纪晓岚命例全链路 |

### 4.3 紫微切片（P1.2-G）

| 测试文件 | 用例数 | 覆盖 |
|---------|-------|------|
| `test_vertical_slice_ziwei.py` | 13 | 紫微垂直切片（模拟 chart） |

### 4.4 审计脚本

| 脚本 | 用途 |
|-----|------|
| `audit_p12f_provenance.py` | Provenance Gate 持续验证 |
| `add_canonical_rule_id.py` | 一次性迁移工具 |

**总计：179 spec tests PASS**

---

## 五、待处理事项（非阻塞）

### 5.1 MEDIUM 风险（后续处理）

| # | 问题 | 建议 |
|---|------|------|
| 1 | SET_SUBSET 单键过宽 | 规则编写规范明确 minimum_keys >= 2 |
| 2 | TEMPORAL/ATTRIBUTE/GRAPH matcher 未实现 | 标记 `NotImplementedError`，不 return True |
| 3 | evidence dict 最小字段约束 | 已用 EvidenceRef 替代开放 dict |

### 5.2 文档更新（非阻塞）

- README 中仍有旧术语 "Semantic Signals"，需在后续文档整理中统一
- `SHUNTIAN_P1_P3_DEVELOPMENT_PLAN.md` 已归档（ARCHIVED/SUPERSEDED）

### 5.3 未来扩展

- 盲派 EvidenceProducer 已建立，待独立 Runtime 验证
- 河洛 EvidenceProducer 已建立，待独立 Runtime 验证
- 易经 EvidenceProducer 已建立，待独立 Runtime 验证
- 五部经典原典资产生产（需走 Source → Passage → Rule → Verification → Admission 流程）

---

## 六、冻结清单

以下文件和 Contract **禁止修改**，除非出现明确的架构缺陷：

```
src/tongshu/spec/canonical/
  ├── engine_evidence.py
  ├── semantic_atom.py
  ├── assertion.py
  └── judgment.py

src/tongshu/assertion/
  ├── assertion_rule_library.py
  └── judgment_rule_library.py

data/rules_index/          （索引格式冻结）
data/semantic_atoms/       （查表数据冻结）
```

---

## 七、Commit 历史

```
28133c0  P1.2-G: 紫微真实 Runtime Vertical Slice — 13/13 PASS
9fc29b5  P1.2-F.1.2: Canonical Rule Binding
ac47312  P1.2-F.1.1: Provenance Gate Hardening
9d4d5dd  P1.2-F.1: Provenance/Admission Gate
17d4b4d  P1.2-F: Contract 整改 — 3 HIGH + 3 MEDIUM
fae7225  P1.2-E: Independent Contract + Runtime Audit
dec9f47  P1.2-D: Real Bazi Runtime Vertical Slice — 11/11 PASS
a4725e6  P1.2-C: 修复 heluo/yi evidence_producer import 路径
42a35b4  P1.2-C: ZiPing 单引擎垂直切片测试 — 18项全通过
3787df6  P1.2-B.1: Contract 修正 — MatchStrategy/evidence_count/NO_ASSERTION
99c904c  P1.2-B: Contract 实现 — 新建 spec/canonical/ + 5引擎 EvidenceProducer
963ec07  P1.2-A V3: 3处文档残留修复
68a8444  P1.2-A V2: 7项架构修正
a710f33  P1.2-A: Contract Design
948e58d  P1.2: Signal Contract Audit Report
9005c8e  P1-Architecture-Gate
```

---

## 八、下一步

**P1.3 — Cross-Domain Evidence Integration**

目标：验证子平 + 紫微进入同一事件上下文时，系统保持"互补不比较"。

关键验证点：
1. 两个体系各自独立产出 Assertion
2. EvidenceCoverage 只做结构性组织（不比较 direction）
3. 无任何投票/权重/冲突裁决逻辑
4. 追溯链完整：每个 Assertion → Rule → Evidence → Engine

**仍冻结**：
- ❌ 删除旧 Signal / CrossAnalyzer
- ❌ 切换主 Pipeline
- ❌ 五经 Agent
- ❌ 大规模断言生产

---

*本文档为 P1.2 阶段最终裁决记录，依据 ARCHITECTURE_V13_FINAL.md 制定。*
