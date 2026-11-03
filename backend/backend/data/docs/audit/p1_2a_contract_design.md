# P1.2-A — Contract Design: EngineEvidence → SemanticAtom → Assertion

**Date**: 2026-09-01  
**Owner**: Agnes (Subagent)  
**Branch**: main  
**Status**: 🟡 CONDITIONAL — 需 User 裁决 7 项架构修正后批准

> **V2 Revision**（基于 User 裁决修正）：
> ① `EngineEvidence` 增加 `evidence_id`（与 `rule_id` 分离）
> ② `direction` 必须由 Authorized Assertion Rule 产生，禁止 MappingLayer 自由决定
> ③ 删除 `CanonicalAssertion.intensity: 0-100`
> ④ `Judgment` ≠ `AssertionCluster`，Judgment 需经授权规则
> ⑤ `EvidenceCoverage` ≠ `Judgment`，前者是横向组织，后者是授权结论
> ⑥ 各 Engine 独立 Evidence Producer，禁止万能 EngineAdapter
> ⑦ `calculation_version` 可演进，Contract version 冻结  

---

## 背景

当前生产路径违反 V13 第 1 条硬约束：

```
pipeline.py → ComputeStage → SignalEngine.build() → dict[str, list[Signal]]
```

`Signal`（`reasoning/signal_engine.py:110`）携带 `direction`/`polarity`/`strength`，这是 V13 **明确禁止**的。

V13 最终架构要求的数据链为：

```
Engine → EngineEvidence（纯事实）→ SemanticAtom → Assertion → Mapping → Guidance
```

本文档是 P1.2-A 的最终设计基线，定义 EngineEvidence / SemanticAtom / Assertion / Judgment 四个核心合约的边界与迁移路径。

---

## 1. EngineEvidence Schema

### 1.1 设计原则

1. **纯事实**：只描述客观计算结果（结构/数值/位置/时间/关系/状态）
2. **禁止价值判断**：无 `direction` / `polarity` / `strength` / `confidence`
3. **规则可追溯**：`rule_id` 稳定不变，可反查到具体规则文件
4. **引擎可识别**：`engine` 字段标识来源（ZI_PING / BLIND_SCHOOL / ZI_WEI / HE_LUO / YI_JING）
5. **时间可定位**：`temporal_scope` 标准化（birth / year / month / day / hour）

### 1.2 完整 Schema 定义

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Literal
from enum import Enum


class EngineName(str, Enum):
    """五大引擎枚举（V13 §三冻结）"""
    ZI_PING = "ZI_PING"
    BLIND_SCHOOL = "BLIND_SCHOOL"
    ZI_WEI = "ZI_WEI"
    HE_LUO = "HE_LUO"
    YI_JING = "YI_JING"


class TemporalScope(str, Enum):
    """时间粒度枚举（V13 §三冻结）"""
    BIRTH = "birth"       # 本命/先天结构
    YEAR = "year"         # 流年
    MONTH = "month"       # 流月
    DAY = "day"           # 流日
    HOUR = "hour"         # 流时


@dataclass(frozen=True)
class EngineEvidence:
    """V13 统一证据合约。所有引擎输出到此层。
    
    禁止字段：direction, polarity, strength, confidence
    
    V2 修正：
    - 增加 evidence_id（与 rule_id 分离，支持同规则多次命中）
    - calculation_version 可演进，不永久冻结
    """
    # 身份
    evidence_id: str                              # 本次证据实例唯一 ID（非 rule_id）
    engine: EngineName
    rule_id: str                                  # 稳定规则ID，禁止运行时变更语义
    
    # 核心事实
    value: Any                                    # 原始计算值（天干/地支/十神/星曜/卦象等）
    temporal_scope: TemporalScope                 # birth/year/month/day/hour
    
    # 附加属性（各引擎自有语义）
    attributes: dict[str, Any] = field(default_factory=dict)
    
    # 追溯字段（V13 §四强制要求）
    source_rule_ref: Optional[str] = None         # 规则文件引用（如 "rules/zp_zheng_cai.json"）
    source_field: Optional[str] = None            # 原始计算字段名（如 "ten_god", "branch_clash"）
    calculation_version: str = "2026.08"          # 计算版本（可演进，每次算法修复递增）
    contract_version: str = "v13.0"               # Contract 版本（P0-P4 冻结）
    
    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "engine": self.engine.value,
            "rule_id": self.rule_id,
            "value": self.value,
            "temporal_scope": self.temporal_scope.value,
            "attributes": dict(self.attributes),
            "source_rule_ref": self.source_rule_ref,
            "source_field": self.source_field,
            "calculation_version": self.calculation_version,
            "contract_version": self.contract_version,
        }
```

### 1.3 示例

**子平伤官示例**（正确）：
```python
EngineEvidence(
    evidence_id="EV-ZP-20260901-001",  # 本次实例唯一，非 rule_id
    engine=EngineName.ZI_PING,
    rule_id="ZP_TEN_GOD_SHANG_GUAN",
    value="丙",
    temporal_scope=TemporalScope.BIRTH,
    attributes={
        "ten_god": "伤官",
        "element": "火",
        "stem": "丙",
        "position": "year",
    },
    source_rule_ref="rules/zp_ten_god.json",
    source_field="ten_god",
    calculation_version="2026.08",      # 可演进
    contract_version="v13.0",            # 冻结
)
```

**同一规则多次命中示例**：
```python
# year pillar 命中
EngineEvidence(evidence_id="EV-001", rule_id="ZP_TEN_GOD_SHANG_GUAN", ...)
# month pillar 命中（同规则，不同证据实例）
EngineEvidence(evidence_id="EV-002", rule_id="ZP_TEN_GOD_SHANG_GUAN", ...)
# day pillar 又命中（同规则，不同证据实例）
EngineEvidence(evidence_id="EV-003", rule_id="ZP_TEN_GOD_SHANG_GUAN", ...)
```

**紫微化忌示例**（正确）：
```python
EngineEvidence(
    engine=EngineName.ZI_WEI,
    rule_id="ZW_TRANS_HUA_JI",
    value="禄存",
    temporal_scope=TemporalScope.YEAR,
    attributes={
        "star": "禄存",
        "transformation": "化忌",
        "palace": "财帛宫",
    },
    source_rule_ref="rules/zw_sihua.json",
    source_field="transformation",
)
```

### 1.4 禁止示例（错误）

```python
# ❌ 禁止携带 value 附带价值判断
EngineEvidence(engine=..., rule_id=..., value="伤官", attributes={"polarity": "positive"})

# ❌ 禁止在 EngineEvidence 层计算 direction
EngineEvidence(engine=..., rule_id=..., value=..., attributes={"direction": "caution"})
```

---

## 2. SemanticAtom Schema

### 2.1 设计原则

1. **查表产物**：SemanticAtom 是 EngineEvidence 经过语义知识库查表后的产物
2. **无方向**：SemanticAtom 不产生 direction，仅携带语义键（semantic_keys）
3. **领域候选**：通过 `domain_candidates` 提供候选人生维度，不预分配 domain
4. **溯源到 EngineEvidence**：每个 SemanticAtom 必须保留 evidence_ref

### 2.2 完整 Schema 定义

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class SemanticAtom:
    """语义原子层数据合约。从 EngineEvidence 经知识库查表后生成。
    
    禁止字段：direction, polarity
    """
    # 身份
    atom_id: str                                # 如 "TEN_GOD_SHANG_GUAN", "ZW_STAR_ZIWEI"
    engine: EngineName                          # 来源引擎
    evidence_ref: str                           # 追溯到 EngineEvidence.evidence_id
    
    # 语义内容（无方向）
    semantic_keys: List[str] = field(default_factory=list)   # 如 ["EXPRESSION", "INNOVATION", ...]
    domain_candidates: List[str] = field(default_factory=list)  # 如 ["CAREER", "GROWTH", "DECISION"]
    
    # 附加元数据
    label_zh: str = ""                          # 中文标签（如 "伤官"）
    category: str = ""                          # 类别（如 "TEN_GOD", "FIVE_ELEMENT", "ZIWEI_MAJOR"）
    guidance_keys: List[str] = field(default_factory=list)  # 行为指引键
    
    def to_dict(self) -> dict:
        return {
            "atom_id": self.atom_id,
            "engine": self.engine.value,
            "evidence_ref": self.evidence_ref,
            "semantic_keys": list(self.semantic_keys),
            "domain_candidates": list(self.domain_candidates),
            "label_zh": self.label_zh,
            "category": self.category,
            "guidance_keys": list(self.guidance_keys),
        }
```

### 2.3 从 EngineEvidence → SemanticAtom 的映射规则

#### 规则 1：查表映射

```python
# 语义知识库路径（data/semantic_atoms/*.json）
SEMANTIC_ATOMS_PATH = "data/semantic_atoms/"

# 查表逻辑（伪代码）
def evidence_to_atom(evidence: EngineEvidence) -> SemanticAtom:
    """从 EngineEvidence 查找对应 SemanticAtom"""
    
    # 1. 确定知识库文件
    engine = evidence.engine
    if engine == EngineName.ZI_PING:
        if "ten_god" in evidence.attributes:
            atom_file = f"{SEMANTIC_ATOMS_PATH}ten_gods.json"
        elif "element" in evidence.attributes:
            atom_file = f"{SEMANTIC_ATOMS_PATH}five_elements.json"
        else:
            return None  # 未知类型
    elif engine == EngineName.ZI_WEI:
        if "star" in evidence.attributes:
            atom_file = f"{SEMANTIC_ATOMS_PATH}ziwei_stars.json"
        elif "transformation" in evidence.attributes:
            atom_file = f"{SEMANTIC_ATOMS_PATH}transformations.json"
        else:
            return None
    elif engine == EngineName.HE_LUO:
        atom_file = f"{SEMANTIC_ATOMS_PATH}he_luo.json"
    elif engine == EngineName.YI_JING:
        if "hexagram" in evidence.attributes:
            atom_file = f"{SEMANTIC_ATOMS_PATH}hexagrams.json"
        elif "yao_position" in evidence.attributes:
            atom_file = f"{SEMANTIC_ATOMS_PATH}yao.json"
        else:
            return None
    else:
        return None
    
    # 2. 加载知识库并匹配 atom_id
    atom = load_atom(atom_file, evidence.attributes)
    if atom is None:
        return None
    
    # 3. 构造 SemanticAtom（不带 direction）
    return SemanticAtom(
        atom_id=atom["atom_id"],
        engine=evidence.engine,
        evidence_ref=evidence.evidence_id,     # V2: 追溯到 evidence_id
        semantic_keys=atom["semantic_keys"],
        domain_candidates=atom["domain_candidates"],
        label_zh=atom.get("label_zh", ""),
        category=atom["category"],
        guidance_keys=atom.get("guidance_keys", []),
    )
```

#### 规则 2：保留 EngineEvidence 原始值

以下字段从 EngineEvidence 透传到 SemanticAtom：
- `evidence_ref` → `evidence.evidence_id`（必须）
- `engine` → 保留原始引擎标识

#### 规则 3：domain 不预分配

SemanticAtom 只提供 `domain_candidates`（候选列表），不选择最终 domain。domain 在 Assertion 层根据 context 确定。

### 2.4 关键设计决策

**Q: 是否需要 direction 的早期预标注？**

**A: 否**。direction 在 Assertion 层才产生。SemanticAtom 只携带语义键（semantic_keys），不做吉凶判断。

```
EngineEvidence（纯事实）
    ↓ 查表
SemanticAtom（语义键 + 候选 domain）
    ↓ 结合 context
Assertion（domain + direction + temporal_scope + authorization）
```

---

## 3. Assertion Boundary

### 3.1 什么是 Assertion

**Assertion 是系统对某个命主状态的结构化断言**，包含：
- `domain`：人生维度（CAREER / FINANCE / RELATIONSHIP / ...）
- `semantic`：语义原子标签（如 OUTPUT_ACTIVATION）
- `direction`：方向（supportive / caution / neutral）— **必须由 Authorized Assertion Rule 产生**
- `temporal_scope`：时间范围
- `source_engine` / `source_rule` / `authorized_rule_id`：追溯信息
- `evidence`：追溯到 EngineEvidence 的完整链

V2 修正：删除 `intensity: 0-100`，避免重新引入评分/权重机制。

### 3.2 完整 Schema 定义

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Optional


class AssertionDirection(str, Enum):
    """V13 冻结的方向枚举（仅 3 值）"""
    SUPPORTIVE = "supportive"    # 支持性
    CAUTION = "caution"          # 警示性
    NEUTRAL = "neutral"          # 中性


@dataclass(frozen=True)
class CanonicalAssertion:
    """V13 Canonical Assertion 合约。
    
    direction 在此层才产生，且必须由 Authorized Assertion Rule 授权。
    V2: 删除 intensity 字段，禁止重新引入评分机制。
    """
    assertion_id: str
    subject: str                                    # case_id
    domain: str                                     # CAREER / FINANCE / RELATIONSHIP / FAMILY / SOCIAL / GROWTH / HEALTH / DECISION
    semantic: str                                   # 语义原子标签（如 OUTPUT_ACTIVATION）
    direction: AssertionDirection                   # supportive / caution / neutral
    temporal_scope: str                             # birth / year / month / day / hour
    source_engine: str                              # ZI_PING / BLIND_SCHOOL / ...
    source_rule: str                                # rule_id
    authorized_rule_id: str                         # 授权此 direction 的断言规则 ID
    evidence: dict                                  # 追溯到 EngineEvidence 的完整链
    
    def to_dict(self) -> dict:
        return {
            "assertion_id": self.assertion_id,
            "subject": self.subject,
            "domain": self.domain,
            "semantic": self.semantic,
            "direction": self.direction.value,
            "temporal_scope": self.temporal_scope,
            "source_engine": self.source_engine,
            "source_rule": self.source_rule,
            "authorized_rule_id": self.authorized_rule_id,
            "evidence": self.evidence,
        }
```

### 3.3 Assertion 边界问题解答

#### Q1: Assertion 何时产生 direction？

**A**: direction 在 Assertion 层产生，不在 EngineEvidence 或 SemanticAtom 层。

**关键约束：direction 必须由 Authorized Assertion Rule 授权产生，禁止 MappingLayer 自由决定。**

```
EngineEvidence（纯事实）
    ↓
SemanticAtom（语义键 + domain_candidates）
    ↓
Authorized Assertion Rule（原典授权）
    ↓
CanonicalAssertion（domain + direction + temporal_scope）
```

产生时机：
1. EngineEvidence 提供纯事实
2. SemanticAtom 提供语义键和候选 domain
3. **Authorized Assertion Rule** 结合命主 context（旺衰/格局/用神/时间）决定 direction
4. direction 来自规则原文授权，不是 Python 逻辑推断

**禁止**：
```python
# ❌ V1 错误模式：MappingLayer 自由决定 direction
direction = mapping.determine_direction(atom, context)

# ✅ V2 正确模式：从 Authorized Assertion Rule 读取
direction = assertion_rule.match(atom, context).direction
```

```python
# 示例：断言生成（V2 修正）
def generate_assertion(
    atom: SemanticAtom,
    context: TemporalContext,
    authorized_rules: AssertionRuleLibrary,
) -> CanonicalAssertion:
    # 1. 确定 domain（从 domain_candidates 中选）
    domain = select_domain(atom.domain_candidates, context)
    
    # 2. 查找授权规则，获取 direction（禁止 MappingLayer 自由决定）
    rule = authorized_rules.find_rule(atom, context)
    if rule is None:
        direction = AssertionDirection.NEUTRAL
    else:
        direction = rule.direction
    
    return CanonicalAssertion(
        assertion_id=f"AS-{atom.evidence_ref}-{domain}",
        subject=context.case_id,
        domain=domain,
        semantic=atom.atom_id,
        direction=direction,
        temporal_scope=context.temporal_scope,
        source_engine=atom.engine.value,
        source_rule=atom.evidence_ref,
        authorized_rule_id=rule.rule_id if rule else "UNAUTHORIZED",
        evidence={"evidence_ref": atom.evidence_ref},
    )
```

#### Q2: Assertion 的输入是什么？

**A**: `SemanticAtom + TemporalContext + AuthorizedAssertionRuleLibrary`

- **SemanticAtom**：提供语义键和候选 domain
- **TemporalContext**：提供命主完整时序上下文（本命/大运/流年）
- **AuthorizedAssertionRuleLibrary**：提供 direction 授权的规则来源（原典授权，非 Python 逻辑推断）

**禁止**：
```python
# ❌ 禁止 MappingLayer 自由决定 direction
direction = mapping.determine_direction(atom, context)

# ✅ 正确：从规则库中匹配授权
rule = assertion_rule_library.match(atom, context)
direction = rule.direction if rule else NEUTRAL
```

#### Q3: Assertion 的 `domain` 字段如何确定？

**A**: domain 由 Mapping Layer 从 `domain_candidates` 中选定，依据是：
1. SemanticAtom 提供的候选列表
2. TemporalContext 中的时序激活信息
3. Mapping 表的域映射规则

**禁止**：直接硬编码 domain 到 EngineEvidence 或 SemanticAtom 层。

**注意**：domain 选择与 direction 授权是**两步独立操作**：
- domain → Mapping Layer（允许）
- direction → Authorized Assertion Rule（必须）

#### Q4: Assertion 与 EngineEvidence 的追溯关系如何建立？

**A**: 通过 `evidence` 字段建立完整链：

```
Assertion.evidence.evidence_ref = EngineEvidence.evidence_id
Assertion.evidence.engine = EngineEvidence.engine
Assertion.evidence.temporal_scope = EngineEvidence.temporal_scope
Assertion.evidence.value = EngineEvidence.value
Assertion.evidence.attributes = EngineEvidence.attributes
```

完整追溯链：
```
Assertion → SemanticAtom → EngineEvidence → rule file → original calculation
```

---

## 4. Judgment Boundary

### 4.1 什么是 Judgment

**Judgment 是经过原典授权规则的结构化判断结论。**

Judgment ≠ AssertionCluster。二者职责完全不同：

| 维度 | EvidenceCoverage | Judgment |
|------|-----------------|----------|
| 性质 | 数据组织结构 | 授权断言结论 |
| 输入 | 多个 CanonicalAssertion | EvidenceCoverage + Authorized Judgment Rule |
| 输出 | evidence_count / source_engines | judgment_id / domain / supporting_assertions |
| 授权 | 无需授权（结构性统计） | 必须有原典授权规则 |
| 比较 | 不做方向比较 | 不产生方向（仅引用 Assertion 的 direction） |

### 4.2 关键设计决策

**Q1: Judgment 是否聚合多个 Assertion？**

**A**: 是，但必须经过 Authorized Judgment Rule 授权。

```
CanonicalAssertion (来自多个引擎)
        ↓
EvidenceCoverage (结构性组织，不比较方向)
        ↓
Authorized Judgment Rule (原典授权)
        ↓
Judgment (结构化判断结论)
```

**禁止**：
```python
# ❌ 禁止：聚合成群就自动成为 Judgment
judgment = Judgment(assertions=cluster.assertions)

# ✅ 正确：需要授权规则
rule = judgment_rule_library.find_rule(cluster)
if rule:
    judgment = Judgment(
        judgment_id=rule.judgment_id,
        assertions=cluster.assertions,
        authorized_by=rule.rule_id,
    )
```

**Q2: EvidenceCoverage 与 Judgment 的关系**

**A**: EvidenceCoverage 是 Judgment 的前置条件，不是 Judgment 本身。

```
Assertion1 (ZI_PING, CAREER, supportive)
Assertion2 (BLIND_SCHOOL, CAREER, supportive)
Assertion3 (HE_LUO, CAREER, supportive)
        ↓
EvidenceCoverage: {domain: "CAREER", evidence_count: 3, source_engines: [...]}
        ↓
Authorized Judgment Rule: RULE_JUDGMENT_CAREER_MULTI_SOURCE
        ↓
Judgment: {judgment_id: "J-CAREER-001", evidence_coverage: ..., authorized_by: "..."}
```

**Q3: EvidenceCoverage 是否需要方向比较？**

**A**: 否。V13 §二明确规定："互补不比较，不投票、不评分、不多数决、不加权"。

EvidenceCoverage 只记录：
- 哪些 Assertion 存在
- 来自哪些引擎
- 覆盖哪些 domain/semantic

不做任何方向比较或聚合判断。

---

## 5. Migration Map

### 5.1 当前生产路径

```
pipeline.py
    ↓
ComputeStage
    ↓
SignalEngine.build() → dict[str, list[Signal]]
    ↓
CrossAnalyzer.analyze(bazi_signals, ziwei_signals) → CrossResult
    ↓
CanonicalComposer.compose(signals, cross_result, ...) → CanonicalContent
```

**问题**：Signal 携带方向字段，违反 V13 第 5 条硬约束。

### 5.2 目标路径

```
pipeline.py
    ↓
ComputeStage
    ↓
EngineEvidenceProducers（各引擎独立）
    ├── ZiPingEvidenceProducer
    ├── BlindSchoolEvidenceProducer
    ├── ZiWeiEvidenceProducer
    ├── HeLuoEvidenceProducer
    └── YiJingEvidenceProducer
    ↓ list[EngineEvidence]
SemanticAtomMapper
    ↓ list[SemanticAtom]
AssertionBuilder（使用 AuthorizedAssertionRuleLibrary）
    ↓ list[CanonicalAssertion]
EvidenceCoverage（替代 CrossAnalyzer，只做结构性组织）
    ↓ dict[str, EvidenceCoverage]
AuthorizedJudgmentRuleLibrary
    ↓ list[Judgment]
MappingLayer → GuidanceComposer
    ↓ Guidance
```

V2 修正：
- 删除万能 EngineAdapter，改为各 Engine 独立 Evidence Producer
- 添加 AuthorizedAssertionRuleLibrary / AuthorizedJudgmentRuleLibrary
- 添加 EvidenceCoverage 概念（替代 CrossAnalyzer + AssertionCluster）

### 5.3 字段迁移对照表

| 当前字段（Signal） | 迁移目标 | 说明 |
|-------------------|----------|------|
| `signal_id` | `EngineEvidence.evidence_id` | 证据实例唯一 ID |
| `ontology_type` | `SemanticAtom.atom_id` | 通过查表转换为语义原子 |
| `direction` | **废弃** | 禁止在 EngineEvidence/SemanticAtom 层携带，仅在 Assertion 层由 Rule 授权产生 |
| `polarity` | **废弃** | 禁止在任何生产层携带 |
| `strength` | **废弃** | 由 Assertion.authorized_rule_id 追溯授权来源 |
| `layer` | `TemporalScope` | 标准化为 birth/year/month/day/hour |
| `rule_refs` | `EngineEvidence.source_rule_ref` | 规范化引用 |
| `evidence_refs` | `SemanticAtom.evidence_ref` | 追溯到 EngineEvidence.evidence_id |

### 5.4 废弃字段清单

| 字段 | 位置 | 废弃原因 |
|------|------|----------|
| `Signal.direction` | `reasoning/signal_engine.py:110` | V13 §四明确废除，方向由 Rule 授权 |
| `Signal.polarity` | `reasoning/signal_engine.py:110` | V13 §四明确废除 |
| `Signal.strength` | `reasoning/signal_engine.py:110` | V13 §四明确废除，评分机制 |
| `CanonicalSignal.direction` | `spec/canonical_signal.py:73` | 新架构不携带方向 |
| `CanonicalSignal.confidence` | `spec/canonical_signal.py:74` | 新架构不携带置信度 |
| `CanonicalAssertion.intensity` | `p1_2a_contract_design.md`（旧版） | V2 删除，避免重新引入评分 |
| `CrossAnalyzer` 方向比较逻辑 | `reasoning/cross_analysis.py:83-99` | V13 §二禁止跨体系方向比较 |
| `ConvergenceArbiter` | `signal/convergence.py` | V13 §二禁止多体系方向比较 |

### 5.5 SignalEngine.build() 返回值类型变化

**当前**：
```python
def build(self, bazi, ziwei, huangli, gender, theme=None, heluo_result=None) -> dict:
    return {
        "BASELINE": list[Signal],
        "CYCLE_CONTEXT": list[Signal],
        "DAILY_ACTIVATION": list[Signal],
    }
```

**目标**：
```python
def build(self, bazi, ziwei, huangli, gender, theme=None, heluo_result=None) -> dict:
    return {
        "BASELINE": list[EngineEvidence],
        "CYCLE_CONTEXT": list[EngineEvidence],
        "DAILY_ACTIVATION": list[EngineEvidence],
    }
```

后续处理链：
```python
evidence_list = signal_engine.build(...)
atoms = semantic_mapper.to_atoms(evidence_list)
assertions = assertion_builder.build_atoms(atoms, context)
coverages = evidence_coverage_builder.build_coverages(assertions)
judgments = judgment_rule_library.authorize(coverages)
```

### 5.6 EvidenceCoverage（替代 CrossAnalyzer）

**当前问题**：CrossAnalyzer 比较 Bazi 和 Ziwei 的方向是否一致（ALIGNED/CONFLICTED/PARTIAL），这违反 V13 §二"互补不比较"原则。

**V2 修正**：EvidenceCoverage 只做结构性组织，不做方向比较，也不产生 Judgment。

```python
@dataclass(frozen=True)
class EvidenceCoverage:
    """证据覆盖面统计，替代 CrossAnalyzer。
    
    只做结构性组织：记录哪些 Assertion 存在，来自哪些引擎。
    不做方向比较，不产生 Judgment。
    """
    domain: str
    semantic: str
    evidence_count: int                     # 证据数量（非投票）
    source_engines: List[str]               # 哪些引擎提供了证据
    evidence_types: List[str]               # 哪些类型的证据
    assertion_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "semantic": self.semantic,
            "evidence_count": self.evidence_count,
            "source_engines": list(self.source_engines),
            "evidence_types": list(self.evidence_types),
            "assertion_ids": self.assertion_ids,
        }


class EvidenceCoverageBuilder:
    """构建 EvidenceCoverage，替代 CrossAnalyzer。
    
    注意：此组件不比较方向，不产生 Judgment。
    Judgment 由 AuthorizedJudgmentRuleLibrary 授权产生。
    """
    
    def __init__(self):
        self._coverages: dict[str, EvidenceCoverage] = {}
    
    def add_assertion(self, assertion: CanonicalAssertion):
        """添加 Assertion 到对应覆盖范围。
        
        不再比较方向，只记录哪些引擎提供了哪些领域的证据。
        """
        key = f"{assertion.domain}:{assertion.semantic}"
        if key not in self._coverages:
            self._coverages[key] = EvidenceCoverage(
                domain=assertion.domain,
                semantic=assertion.semantic,
                evidence_count=0,
                source_engines=[],
                evidence_types=[],
            )
        cover = self._coverages[key]
        self._coverages[key] = EvidenceCoverage(
            domain=cover.domain,
            semantic=cover.semantic,
            evidence_count=cover.evidence_count + 1,
            source_engines=list(set(cover.source_engines + [assertion.source_engine])),
            evidence_types=list(set(cover.evidence_types + [assertion.semantic])),
            assertion_ids=cover.assertion_ids + [assertion.assertion_id],
        )
    
    def get_coverages(self) -> dict:
        """返回证据覆盖面统计。"""
        result = {}
        for cover in self._coverages.values():
            domain = cover.domain
            semantic = cover.semantic
            if domain not in result:
                result[domain] = {}
            result[domain][semantic] = cover.to_dict()
        return result
```

---

## 6. Deletion List

### 6.1 必须删除的文件

| 文件路径 | 删除范围 | 原因 |
|----------|----------|------|
| `src/tongshu/reasoning/signal_engine.py` | 整个文件 | Signal class 违反 V13；需重写为各 EngineEvidenceProducer |
| `src/tongshu/reasoning/cross_analysis.py` | 整个文件 | CrossAnalyzer 比较方向违反 V13 §二 |
| `src/tongshu/signal/convergence.py` | 整个文件 | ConvergenceArbiter 做跨体系方向比较 |
| `src/tongshu/signal/aggregator.py` | 整个文件 | 基于 Signal 的聚合逻辑需替换 |
| `src/tongshu/signal/legacy_adapter.py` | 整个文件 | 已在 9005c8e 标记 NON_PRODUCTION，零引用 |
| `src/tongshu/spec/canonical_signal.py` | 整个文件 | V1.2 旧 schema，将被 EngineEvidence 替代 |
| `src/tongshu/signal/canonical_signal.py` | 整个文件 | 扩展版 CanonicalSignal，无生产调用 |
| `src/tongshu/signal/normalizer.py` | 整个文件 | 基于旧方向逻辑的归一化 |

### 6.2 需要新建的文件

| 文件路径 | 内容 | 说明 |
|----------|------|------|
| `src/tongshu/spec/canonical/engine_evidence.py` | EngineEvidence / EngineName / TemporalScope | 新 Contract |
| `src/tongshu/spec/canonical/semantic_atom.py` | SemanticAtom | 新 Contract |
| `src/tongshu/spec/canonical/assertion.py` | CanonicalAssertion / AssertionDirection | 新 Contract |
| `src/tongshu/spec/canonical/judgment.py` | Judgment / EvidenceCoverage | 新 Contract |
| `src/tongshu/engines/ziping/evidence_producer.py` | ZiPingEvidenceProducer | 各引擎独立 Producer |
| `src/tongshu/engines/blind/evidence_producer.py` | BlindEvidenceProducer | 各引擎独立 Producer |
| `src/tongshu/engines/ziwei/evidence_producer.py` | ZiWeiEvidenceProducer | 各引擎独立 Producer |
| `src/tongshu/engines/heluo/evidence_producer.py` | HeLuoEvidenceProducer | 各引擎独立 Producer |
| `src/tongshu/engines/yi/evidence_producer.py` | YiEvidenceProducer | 各引擎独立 Producer |
| `src/tongshu/assertion/assertion_rule_library.py` | AuthorizedAssertionRuleLibrary | direction 授权来源 |
| `src/tongshu/assertion/judgment_rule_library.py` | AuthorizedJudgmentRuleLibrary | judgment 授权来源 |
| `data/semantic_atoms/modern_concepts.json` | 现代概念词典 | V13 §八要求 |

### 6.3 需要修改的代码引用

| 文件 | 修改内容 |
|------|----------|
| `src/tongshu/types.py` | 移除 Signal / CrossResult 引用，新增 EngineEvidence / SemanticAtom / CanonicalAssertion |
| `src/tongshu/pipeline.py` | 移除 CrossAnalyzer 实例化，改用 EvidenceCoverageBuilder |
| `src/tongshu/pipeline_stages/compute_stage.py` | 替换 SignalEngine 为各 EngineEvidenceProducer，移除 CrossAnalyzer |
| `src/tongshu/canonical/composer.py` | 移除 Signal 格式化逻辑，改用 Assertion 序列化 |
| `src/tongshu/engines/annual_event_evaluator.py` | 移除 ConvergenceArbiter 引用 |
| `src/tongshu/reasoning/__init__.py` | 移除 CrossAnalyzer / CrossResult 导出 |

### 6.4 可选保留的文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `src/tongshu/assertion_v2/contract.py` | 审查后决定 | 包含 NativeJudgment / JudgmentLibrary，可参考但需重构 |
| `src/tongshu/reasoning/temporal_context_contract.py` | 保留 | TemporalContext 可作为 context 输入 |
| `src/tongshu/feature_registry/contract.py` | 保留 | Feature 注册表可参考 |
| `data/semantic_atoms/*.json` | 保留 + 补充 | 7 个现有文件保留，需补充 modern_concepts.json |

### 6.5 删除顺序（V2 修正）

**禁止一次性删除所有旧文件**。必须按以下顺序执行：

```
阶段 1: 新建 Contract
  → 创建 spec/canonical/*.py（EngineEvidence / SemanticAtom / CanonicalAssertion / Judgment）
  → 创建 data/semantic_atoms/modern_concepts.json

阶段 2: 实现单引擎 Evidence Producer
  → 选择一个引擎（推荐 ZiPing）实现 ZiPingEvidenceProducer
  → 在独立测试路径验证

阶段 3: 接入生产路径
  → 修改 compute_stage.py 使用新 Producer + EvidenceCoverageBuilder
  → 运行全量测试，确认无回归

阶段 4: 扩展其他引擎
  → 依次实现 Blind/Ziwei/HeLuo/Yi EvidenceProducer
  → 每步独立测试

阶段 5: 删除旧文件
  → 确认新生产路径跑通后，再删除旧文件
  → 逐文件删除，每步回归测试
```

---

## 附录 A：V13 硬约束回顾

| 约束编号 | 内容 |
|----------|------|
| ① | 不再改引擎算法，只改中间链路 |
| ② | 不再做体系投票：互补不比较，不投票、不评分、不多数决、不加权 |
| ③ | 不让 LLM 判断方向：LLM 只负责自然语言表达 |
| ④ | 不让传统术语直接穿透到用户界面：必须经过 Semantic Atom → Modern Concept → Domain → Guidance |
| ⑤ | **EngineEvidence 不能有 polarity/direction**：只保留事实/数值/结构/位置/时间，方向在 Assertion 之后才产生 |
| ⑥ | SYSTEM_WEIGHTS 彻底删除 |
| ⑦ | 喜用神走同一条链 |
| ⑧ | AuditFlag 冻结（P0-P4 不主动触发） |

---

## 附录 B：数据流向图（V2 修正）

```
┌──────────────────────────────────────────────────────────────────────┐
│ Deterministic Engine                                                │
│ 子平/盲派/紫微/河洛/易经                                             │
└───────────────────────┬──────────────────────────────────────────────┘
                        │ raw calculation results（纯事实）
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│ EngineEvidenceProducers（各引擎独立，禁止万能 Adapter）               │
│  - ZiPingEvidenceProducer                                           │
│  - BlindEvidenceProducer                                            │
│  - ZiWeiEvidenceProducer                                            │
│  - HeLuoEvidenceProducer                                            │
│  - YiEvidenceProducer                                               │
└───────────────────────┬──────────────────────────────────────────────┘
                        │ list[EngineEvidence]
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│ EngineEvidence                                                      │
│ - evidence_id: str (唯一实例ID，与 rule_id 分离)                     │
│ - engine: EngineName                                                │
│ - rule_id: str (stable)                                             │
│ - value: Any (事实值)                                                │
│ - temporal_scope: TemporalScope                                     │
│ - attributes: dict (十神/五行/天干/宫位等)                            │
│ - calculation_version: str (可演进)                                  │
│ - contract_version: str (P0-P4 冻结)                                 │
│                                                                      │
│ ❌ 禁止: direction, polarity, strength, confidence                  │
└───────────────────────┬──────────────────────────────────────────────┘
                        │ 查表（data/semantic_atoms/*.json）
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│ SemanticAtom                                                        │
│ - atom_id: str                                                      │
│ - engine: EngineName                                                │
│ - evidence_ref: str (追溯到 EngineEvidence.evidence_id)             │
│ - semantic_keys: List[str]                                          │
│ - domain_candidates: List[str]                                      │
│ - label_zh: str                                                     │
│ - category: str                                                     │
│                                                                      │
│ ❌ 无 direction                                                       │
└───────────────────────┬──────────────────────────────────────────────┘
                        │ + TemporalContext
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│ AuthorizedAssertionRuleLibrary                                      │
│ - 原典授权的断言规则库                                                 │
│ - 输入: SemanticAtom + TemporalContext                               │
│ - 输出: AuthorizedAssertionRule (包含 direction)                    │
│                                                                      │
│ ✅ direction 由此层授权产生，禁止 MappingLayer 自由决定               │
└───────────────────────┬──────────────────────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│ CanonicalAssertion                                                  │
│ - assertion_id: str                                                 │
│ - subject: str (case_id)                                            │
│ - domain: str (CAREER/FINANCE/...)                                  │
│ - semantic: str (语义原子标签)                                        │
│ - direction: Literal["supportive", "caution", "neutral"]            │
│ - temporal_scope: str                                               │
│ - source_engine: str                                                │
│ - source_rule: str                                                  │
│ - authorized_rule_id: str (追溯授权规则)                              │
│ - evidence: dict (追溯到 EngineEvidence)                              │
│                                                                      │
│ ✓ direction 由 Authorized Rule 授权产生                               │
│ ❌ 无 intensity (V2 删除，避免评分机制)                               │
└───────────────────────┬──────────────────────────────────────────────┘
                        │ 结构性组织（不比较方向）
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│ EvidenceCoverageBuilder                                             │
│ - 替代 CrossAnalyzer / ConvergenceArbiter                           │
│ - 只做结构性组织：记录哪些 Assertion 存在                            │
│ - 不做方向比较 / 不产生 Judgment                                     │
└───────────────────────┬──────────────────────────────────────────────┘
                        │ EvidenceCoverage
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│ AuthorizedJudgmentRuleLibrary                                       │
│ - 原典授权的结构化判断规则                                             │
│ - 输入: EvidenceCoverage                                             │
│ - 输出: Judgment (如有授权规则)                                       │
│                                                                      │
│ ✅ Judgment 必须由原典授权规则产生                                     │
│ ❌ 禁止：聚合即 Judgment                                               │
└───────────────────────┬──────────────────────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Judgment (optional, 需授权)                                          │
│ - judgment_id: str                                                  │
│ - evidence_coverage: EvidenceCoverage                               │
│ - authorized_by: str (rule_id)                                      │
│                                                                      │
│ ❌ 不产生新方向，仅引用已有 Assertion 的 direction                     │
└───────────────────────┬──────────────────────────────────────────────┘
                        │ Mapping Layer
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Guidance                                                            │
│ - domain: str                                                       │
│ - headline: str                                                     │
│ - state: str                                                        │
│ - opportunities: List[str]                                          │
│ - cautions: List[str]                                               │
│ - actions: List[str]                                                │
│ - avoid: List[str]                                                  │
│ - evidence: List[str] (rule_id 列表)                                 │
└───────────────────────┬──────────────────────────────────────────────┘
                        │ LLM Renderer（只负责自然语言表达）
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 用户界面                                                            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 附录 C：实施阶段对齐

| V13 阶段 | 内容 | 本文档覆盖 |
|----------|------|-----------|
| P0 | 接口统一 + 清除旧方向机制 | §5 Migration Map、§6 Deletion List |
| P1 | Semantic Atom 知识库建设 | §2 SemanticAtom Schema |
| P2 | Rules → Semantic Atoms | §1 EngineEvidence Schema |
| P3 | Signal → Semantic Signal | §5 Migration Map |
| P4 | Assertion Cluster | §4 Judgment Boundary |
| P5 | Mapping + Guidance Composer | （后续文档） |
| P6 | Golden Dataset / 真实案例验证 | （后续文档） |

---

*本文档为 P1.2-A V2 设计基线，依据 ARCHITECTURE_V13_FINAL.md §三~§四制定。*

---

## 附录 D：V2 修正摘要（User 裁决）

| # | 修正项 | 旧版问题 | V2 修正 |
|---|--------|---------|---------|
| ① | `evidence_id` | `rule_id` 同时作为追溯锚点，同规则多次命中时无法区分 | 新增 `evidence_id`（实例唯一）与 `rule_id`（规则稳定）分离 |
| ② | `direction` 来源 | `MappingLayer.determine_direction()` 自由决定方向 | `AuthorizedAssertionRuleLibrary` 原典授权产生方向 |
| ③ | `intensity: 0-100` | 重新引入评分/权重机制，违背 V13 §二 | **删除**，禁止 0-100 数值化强度 |
| ④ | `Judgment` 定义 | `Judgment = AssertionCluster`，聚合成群即判断 | `EvidenceCoverage ≠ Judgment`，Judgment 需授权规则 |
| ⑤ | `EvidenceCoverage` 定义 | 命名为 `AssertionCluster`，语义不清 | 重命名为 `EvidenceCoverage`，明确只做结构性组织 |
| ⑥ | Engine 接入方式 | 万能 `EngineAdapter`，if-else 分支 | 各 Engine 独立 `EvidenceProducer`，禁止 God Adapter |
| ⑦ | 版本冻结 | `calculation_version = "2026.08"` 永久冻结 | `calculation_version` 可演进，新增 `contract_version` 冻结 |
| — | 删除顺序 | 一次性删除所有旧文件 | 五阶段渐进迁移，新路径跑通后再删旧 |
