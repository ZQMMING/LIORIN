# P0-2.7.1A Judgment Logic Kernel — 辨证逻辑内核设计与验证

> **设计时间**：2026-08-29
> **设计目标**：实现一个通用的符号推理执行器（Judgment Logic Kernel），用人工构造的逻辑案例验证 A+B+C → Overall State，且全程无 score/weight/threshold
> **基于 commit**：`19409d9`
> **核心原则**：不使用数值评分；不使用"支持证据数量"判断整体；使用符号逻辑；UNRESOLVED 是合法结果。
> **验证状态**：✅ 已通过演示验证

---

## 一、设计背景

### 问题提出

P0-2.7（19409d9）定义了四层架构：Fact → Relation → Evidence → Judgment，但"Judgment Strategy"还只是一个名字，真正需要定义的是：

> 多个局部证据 ↓ 怎样组合？ ↓ 什么是必要条件？ 什么是充分条件？ 什么是抵消条件？ 什么是优先条件？ 什么是转化条件？ 什么是例外？ ↓ 整体辨证

如果直接写 `if root_support and seasonal_support: state = STRONG`，就会重新犯过去的错误——只不过这次不是 score，而是把"没有定义清楚的传统命理综合逻辑"硬编码成 if/else。

### 解决方案

建立 **Judgment Logic Kernel**（辨证逻辑内核）：

- 不是命理知识
- 不是五部经典
- 是一个通用的符号推理执行器

定义操作符：AND, OR, REQUIRED, SUFFICIENT, OPPOSE, BLOCK, OVERRIDE, TRANSFORM, QUALIFY, NEGATE, UNRESOLVED

以及机制：precedence（优先级）、conflict（冲突）、absence（缺失）、exception（例外）

---

## 二、核心数据结构

### 2.1 Polarity（证据极性）

```python
class Polarity(Enum):
    SUPPORT = "support"        # 支持结论
    CONSTRAINT = "constraint"  # 制约结论
    NEUTRAL = "neutral"        # 中性
    MODIFIER = "modifier"      # 修改其他证据的有效性
    TRANSFORM = "transform"    # 转化证据意义
```

### 2.2 EvidenceStatus（证据状态）

```python
class EvidenceStatus(Enum):
    PRESENT = "present"        # 证据存在
    ABSENT = "absent"          # 证据缺失
    UNKNOWN = "unknown"        # 证据未知
    MODIFIED = "modified"      # 证据被修改
    OVERRIDDEN = "overridden"  # 证据被覆盖
    BLOCKED = "blocked"        # 证据被阻断
```

### 2.3 JudgmentOutcome（辨证结果）

```python
class JudgmentOutcome(Enum):
    CONFIRMED = "confirmed"        # 确认成立
    QUALIFIED = "qualified"        # 有条件成立
    UNRESOLVED = "unresolved"      # 无法裁决
    REJECTED = "rejected"          # 不成立
    NOT_APPLICABLE = "not_applicable"  # 不适用
```

### 2.4 LogicOperator（逻辑操作符）

```python
class LogicOperator(Enum):
    AND = "and"              # 所有条件必须同时成立
    OR = "or"                # 任一条件成立即可
    REQUIRED = "required"    # 必要条件，缺失则 UNRESOLVED
    SUFFICIENT = "sufficient"  # 充分条件，成立则 CONFIRMED
    OPPOSE = "oppose"        # 反向制约
    BLOCK = "block"          # 阻断结论成立
    OVERRIDE = "override"    # 覆盖普通规则
    TRANSFORM = "transform"  # 转化证据意义
    QUALIFY = "qualify"      # 降低结论等级
    NEGATE = "negate"        # 否定证据
```

### 2.5 Evidence（证据）

```python
@dataclass
class Evidence:
    evidence_id: str                    # 证据 ID
    judgment_target: str                # 辨证目标（必须带）
    evidence_type: str                  # 证据类型
    polarity: Polarity                  # 证据极性
    status: EvidenceStatus              # 证据状态
    source_relation_ids: List[str]      # 来源 Relation ID
    context: Dict[str, Any]             # 上下文
    evidence_meaning: str               # 证据含义
    provenance: str                     # 来源
    confidence: float                   # 置信度（证据确定性，不是力量评分）
    scope: str                          # 范围
    modifiers: List[str]                # 应用于此证据的修改器
    original_polarity: Optional[Polarity]  # 被修改前的原始极性
```

**关键设计**：
- Evidence 必须带 `judgment_target`，说明这个证据是为哪个辨证目标服务的
- 同一个 Relation 可以为不同辨证目标产生不同 Evidence
- `confidence` 是证据确定性，不是力量评分
- 支持 `original_polarity` 记录被修改前的原始极性

### 2.6 LogicCondition（逻辑条件）

```python
@dataclass
class LogicCondition:
    condition_id: str                   # 条件 ID
    operator: LogicOperator             # 逻辑操作符
    evidence_type: Optional[str]        # 关联的证据类型
    evidence_id: Optional[str]          # 关联的具体证据 ID
    expected_status: EvidenceStatus     # 期望的证据状态
    sub_conditions: List[LogicCondition]  # 子条件（用于 AND/OR）
    description: str                    # 条件描述
    precedence: int                     # 优先级
    applies_to: str                     # 应用于哪个结论/状态
```

### 2.7 LogicGroup（逻辑组）

```python
@dataclass
class LogicGroup:
    group_id: str                       # 组 ID
    group_name: str                     # 组名称
    group_type: str                     # 组类型：SUPPORT / CONSTRAINT / MODIFIER / TRANSFORM / REQUIRED / BLOCK / OVERRIDE / QUALIFICATION
    conditions: List[LogicCondition]    # 条件列表
    combination_operator: LogicOperator  # 组内条件组合方式
    description: str                    # 组描述
```

**组类型**：
- `REQUIRED`：必要条件组
- `SUPPORT`：支持组
- `CONSTRAINT`：制约组
- `MODIFIER`：修改器组
- `BLOCK`：阻断组
- `OVERRIDE`：覆盖组
- `TRANSFORM`：转化组
- `QUALIFICATION`：限定组

### 2.8 JudgmentRule（辨证规则）

```python
@dataclass
class JudgmentRule:
    rule_id: str                        # 规则 ID
    rule_name: str                      # 规则名称
    system: str                         # 体系/经典
    target: str                         # 辨证目标
    output_state: str                   # 输出状态
    
    # 证据组（按优先级执行）
    required_groups: List[LogicGroup]       # 必要条件组
    support_groups: List[LogicGroup]        # 支持组
    constraint_groups: List[LogicGroup]     # 制约组
    modifier_groups: List[LogicGroup]       # 修改器组
    blocking_groups: List[LogicGroup]       # 阻断组
    override_groups: List[LogicGroup]       # 覆盖组
    transform_groups: List[LogicGroup]      # 转化组
    qualification_groups: List[LogicGroup]  # 限定组
    
    # 冲突与缺失策略
    conflict_policy: str = "unresolved"  # 冲突策略
    absence_policy: str = "unresolved"   # 缺失策略
    precedence: int = 0                   # 优先级
    
    # 元数据
    classical_source: str = ""
    description: str = ""
```

### 2.9 JudgmentEngine（辨证引擎）

```python
class JudgmentEngine:
    def __init__(self, system: str, target: str):
        self.system = system
        self.target = target
        self.rules: List[JudgmentRule] = []
    
    def add_rule(self, rule: JudgmentRule):
        """添加辨证规则（按 system 和 target 过滤）"""
    
    def evaluate(self, evidence_set: Set[Evidence]) -> FinalJudgment:
        """执行辨证"""
```

---

## 三、辨证执行流程

### 3.1 单条规则的执行顺序（按优先级）

```
1. OVERRIDE：覆盖普通规则（如果成立，直接输出结果）
   ↓
2. BLOCKING：阻断结论（如果成立，结论不成立）
   ↓
3. REQUIRED：必要条件（如果缺失，UNRESOLVED）
   ↓
4. TRANSFORM：转化证据意义（修改证据极性/状态）
   ↓
5. MODIFIER：修改证据有效性
   ↓
6. SUPPORT + CONSTRAINT：支持与制约的平衡
   ↓
7. QUALIFICATION：限定结论等级（CONFIRMED → QUALIFIED）
```

### 3.2 关键：不使用"支持证据数量"判断整体

**错误做法**（禁止）：
```python
support_count = len(support_evidence)
constraint_count = len(constraint_evidence)
if support_count > constraint_count:
    result = CONFIRMED
```

**正确做法**（符号逻辑）：
```python
# 1. 检查是否有充分支持条件（SUFFICIENT）
has_sufficient_support = any(
    condition.operator == SUFFICIENT 
    for group in support_groups 
    for condition in group.conditions
    if group.evaluate(evidence_set).satisfied
)

# 2. 检查是否有强制约条件（OPPOSE）
has_strong_constraint = any(
    condition.operator == OPPOSE
    for group in constraint_groups
    for condition in group.conditions
    if group.evaluate(evidence_set).satisfied
)

# 3. 综合判断
if has_sufficient_support and not has_strong_constraint:
    base_result = CONFIRMED
elif has_strong_constraint and not has_sufficient_support:
    base_result = REJECTED
elif support_satisfied and not constraint_satisfied:
    base_result = CONFIRMED
elif constraint_satisfied and not support_satisfied:
    base_result = REJECTED
elif support_satisfied and constraint_satisfied:
    # 支持与制约同时存在
    if conflict_policy == "unresolved":
        base_result = UNRESOLVED  # 关键：不强行判断
    ...
else:
    base_result = UNRESOLVED
```

### 3.3 多规则的综合

```
1. 执行所有适用规则（按 system 和 target 过滤）
2. 收集所有规则结果
3. 冲突处理：
   - CONFIRMED + REJECTED 同时存在 → UNRESOLVED
   - 只有 CONFIRMED → CONFIRMED
   - 只有 QUALIFIED → QUALIFIED
   - 只有 UNRESOLVED → UNRESOLVED
   - 只有 REJECTED → REJECTED
```

---

## 四、验证演示：A+B+C → 整体辨识

### 4.1 场景

甲日主，寅月：
- A = 得令（临官）→ SUPPORT
- B = 得地（本气根）→ SUPPORT
- C = 得势（透印）→ SUPPORT
- D = 官杀重 → CONSTRAINT
- E = 财旺 → CONSTRAINT
- F = 根被冲 → MODIFIER

### 4.2 输入证据（6 条）

```
E-S-001: 得令支持（甲在寅=临官） [support]
E-S-004: 本气根强支持（甲在寅=本气根） [support]
E-S-006: 印星生扶支持（透印） [support]
E-S-008: 财星耗泄（财旺） [constraint]
E-S-009: 官杀制约（官杀重） [constraint]
E-S-010: 根气受损（根被冲） [modifier]
```

### 4.3 辨证规则（滴天髓旺衰辨证-偏强）

```
规则 ID: J-DTS-STRONG-001
输出状态: 偏强
优先级: 10

必要条件组 (REQUIRED):
  - 得令证据必须存在 (REQUIRED)

支持组 (SUPPORT):
  - 本气根支持 (SUFFICIENT) AND 印星生扶支持 (AND)
  → 得地（本气根）+ 得势（透印）= 强支持

制约组 (CONSTRAINT):
  - 官杀重 (OPPOSE) → 强制约条件

修改器组 (MODIFIER):
  - 根被冲 (TRANSFORM) → 修改根气有效性

冲突策略: unresolved
缺失策略: unresolved
```

### 4.4 执行结果

```
[DITIANSUI] DAY_MASTER_STRENGTH: unresolved = UNRESOLVED
推理: 1 条规则无法裁决

详细规则结果：
  J-DTS-STRONG-001: unresolved → N/A
    推理: 支持条件成立：SUPPORT-ROOT-QI; 制约条件成立：CONSTRAINT-OFFICER
  J-DTS-WEAK-001: rejected → N/A
    推理: 阻断规则 得令阻断 成立，结论不成立
```

### 4.5 结果分析

**为什么是 UNRESOLVED？**

1. 支持条件成立：得令 + 得地（本气根）+ 得势（透印）
2. 制约条件成立：官杀重（OPPOSE，强制约）
3. 支持与制约同时存在
4. 冲突策略是 `unresolved`
5. 因此输出 UNRESOLVED，不强行判断

**这正是我们想要的行为**：
- 当证据冲突时，不使用"支持数量 > 制约数量"来强行判断
- 而是检查是否有充分条件（SUFFICIENT）和强制约（OPPOSE）
- 如果都存在且冲突，输出 UNRESOLVED
- UNRESOLVED 是合法结果，不是错误

### 4.6 关键验证清单

```
✓ 未使用 score/weight/threshold
✓ 未使用 support_count > oppose_count
✓ 使用符号逻辑：REQUIRED / SUFFICIENT / OPPOSE / BLOCK / TRANSFORM
✓ 证据带 judgment_target
✓ UNRESOLVED 是合法结果
✓ A+B+C+D+E+F 通过符号逻辑组合得到整体状态
```

---

## 五、与传统命理的对应

### 5.1 五部经典的差异不在"算什么"，而在"怎么辨"

| 经典 | 共享本体 | 选择的观察对象 | 选择的证据 | 证据组合逻辑 | 输出状态 |
|------|---------|--------------|-----------|------------|---------|
| 滴天髓 | 阴阳/五行/干支/藏干/十神/时令/刑冲合害 | 整体气势/体用 | 得令/得地/得势/生扶/克泄耗/制化 | 气势平衡/体用关系 | 旺/衰/中和/偏枯/太过/不及 |
| 子平真诠 | 同上 | 月令/格局 | 月令主气/透干/根气/财生官/印护官/伤官见官 | 格局成败/救应 | 格成/格破/待成 |
| 穷通宝鉴 | 同上 | 日主×月令×气候 | 调候五行/有根/可用/受阻/过量 | 调候成立/不足/太过 | 调候状态 |
| 三命通会 | 同上 | 关系/变化/合化 | 合/冲/刑/害/化气条件 | 关系转化/合化成立 | 合化/合绊 |
| 渊海子平 | 同上 | 基础格局/十神/神煞 | 十神关系/神煞/运命 | 传统语义 | 传统状态 |

### 5.2 关键：共享命理本体，不同辨证规则

五部经典不是五个"孤岛算法"，而是：

```
共享：阴阳/五行/干支/藏干/十神/时令/刑冲合害/生克制化
    ↓
不同经典
    ↓
选择不同观察对象
    ↓
选择不同证据
    ↓
使用不同证据组合逻辑
    ↓
得到不同辨证状态
```

---

## 六、旺衰不能被定义成"一个算法"

### 6.1 错误做法（禁止）

```python
strength_engine.calculate(chart) → STRONG / WEAK
```

### 6.2 正确做法

```python
# 允许不同体系有不同的旺衰辨证结果
DTS_STRENGTH_STATE = ditiansui_engine.evaluate(evidence_set)
ZIPING_STRENGTH_STATE = ziping_engine.evaluate(evidence_set)

# 甚至必要时：
UNRESOLVED  # 证据不足或冲突时
```

### 6.3 原因

"身强身弱"是辨证结果，不是原始计算结果。不同体系可能有不同的判断标准，证据不足时应该输出 UNRESOLVED。

---

## 七、顺天真正的核心链

```
【算】 Calculation
    ↓
Canonical Facts（确定性计算）
    ↓
Semantic Relations（关系引擎，越笨越好）
    ↓
【辨】 Judgment
    ↓
┌───────────┬───────────┬───────────┐
    ↓           ↓           ↓
  旺衰         格局         调候
    ↓           ↓           ↓
五部经典各自的 Evidence
    ↓           ↓           ↓
各自 Judgment Logic Kernel
    ↓           ↓           ↓
 State A     State B     State C
    └───────────┼───────────┘
                ↓
        Semantic Signal
                ↓
【解】 Interpretation
```

**关键**：
- 不是串行：八字 → 身强弱 → 格局 → 用神 → 断事
- 而是并行：同一 Fact State 同时进入旺衰、格局、调候辨证
- 不同体系共享 Fact 和 Relation，但有不同的 Evidence 和 Judgment Logic

---

## 八、当前状态总结

### Judgment Logic Kernel 状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 核心数据结构 | ✅ 已定义 | Evidence, LogicCondition, LogicGroup, JudgmentRule, JudgmentEngine |
| 逻辑操作符 | ✅ 已定义 | AND, OR, REQUIRED, SUFFICIENT, OPPOSE, BLOCK, OVERRIDE, TRANSFORM, QUALIFY, NEGATE |
| 执行流程 | ✅ 已实现 | OVERRIDE → BLOCK → REQUIRED → TRANSFORM → MODIFIER → SUPPORT+CONSTRAINT → QUALIFICATION |
| 冲突处理 | ✅ 已实现 | CONFIRMED+REJECTED → UNRESOLVED |
| 缺失处理 | ✅ 已实现 | 必要条件缺失 → UNRESOLVED |
| 验证演示 | ✅ 已通过 | A+B+C+D+E+F → UNRESOLVED（支持与制约冲突） |
| 无 score/weight | ✅ 已验证 | 全程未使用数值评分 |
| 无 support_count | ✅ 已验证 | 未使用"支持证据数量"判断整体 |

### "算 → 辨 → 解"边界状态

| 层 | 状态 | 说明 |
|----|------|------|
| 算（Calculation） | 🟡 继续独立证明 | Fact 在代码中实现，需要完整测试覆盖 |
| Relation Engine | 🔴 缺失 | 34 条 Rule 应该迁移到这里 |
| Evidence Derivation | 🔴 严重不足 | 只有 2 条 Evidence 层的 Rule |
| **Judgment Logic Kernel** | ✅ **已设计并验证** | 符号推理执行器，已通过演示验证 |
| Judgment Strategy | 🟡 需要按体系实现 | 滴天髓/子平真诠/穷通宝鉴等 |
| "辨准" | 🟡 内核已立，策略待建 | Judgment Logic Kernel 已验证，但具体经典辨证策略还需要实现 |

---

## 九、下一步建议

### P0-2.7.1B：旺衰辨证策略实现（高优先级）

目标：基于 Judgment Logic Kernel，实现滴天髓和子平真诠的旺衰辨证策略，完成最小垂直切片。

步骤：
1. 实现 Relations：五行关系、阴阳关系、根气关系、十神关系
2. 实现 Evidence：旺衰证据推导（得令、得地、得势、受制等）
3. 实现 Judgment Rules：滴天髓旺衰辨证规则、子平真诠旺衰辨证规则
4. 端到端测试：BaziChart → Facts → Relations → Evidence → Judgment → State
5. 验证：全程无 score，UNRESOLVED 是合法结果

### P0-2.7.2：推广到其他辨证目标（高优先级）

- 格局辨证（子平真诠）
- 调候辨证（穷通宝鉴）
- 体用辨证（滴天髓）
- 关系转化辨证（三命通会）

### P0-2.7.3：迁移现有 Rule（中优先级）

- 34 条 RELATION 层 Rule → relations/
- 2 条 EVIDENCE 层 Rule → evidence/
- 94 条 JUDGMENT 层 Rule → Judgment Strategy
- 6 条 UNCERTAIN 层 Rule → 人工审查

### P0-3：Boundary Cases（高优先级）

### P0-4：Calculation Golden Dataset（高优先级）

---

## 十、审计总结

### 本次设计的核心成果

1. ✅ **定义了 Judgment Logic Kernel**：通用的符号推理执行器，不是命理知识，不是五部经典
2. ✅ **定义了 11 种逻辑操作符**：AND, OR, REQUIRED, SUFFICIENT, OPPOSE, BLOCK, OVERRIDE, TRANSFORM, QUALIFY, NEGATE
3. ✅ **定义了 8 种逻辑组**：REQUIRED, SUPPORT, CONSTRAINT, MODIFIER, BLOCK, OVERRIDE, TRANSFORM, QUALIFICATION
4. ✅ **实现了辨证执行流程**：OVERRIDE → BLOCK → REQUIRED → TRANSFORM → MODIFIER → SUPPORT+CONSTRAINT → QUALIFICATION
5. ✅ **实现了冲突处理**：CONFIRMED+REJECTED → UNRESOLVED
6. ✅ **实现了缺失处理**：必要条件缺失 → UNRESOLVED
7. ✅ **验证了 A+B+C → 整体辨识**：6 条证据（3 支持+2 制约+1 修改器）→ UNRESOLVED（支持与制约冲突）
8. ✅ **全程无 score/weight/threshold**：使用符号逻辑，不使用数值评分
9. ✅ **无 support_count > oppose_count**：不使用"支持证据数量"判断整体
10. ✅ **UNRESOLVED 是合法结果**：证据不足或冲突时输出 UNRESOLVED

### 核心原则

> 辨不是 Rule 的执行结果；辨是某一命理体系在共享的事实与关系空间中，对特定辨证目标进行证据组织、条件判断和状态归纳的过程。

> 同源事实，不同辨法；共享关系，不共享结论。

> 不使用 score/weight/threshold；不使用"支持证据数量"判断整体；使用符号逻辑；UNRESOLVED 是合法结果。

### 最重要的一句话

这次 P0-2.7.1A 真正解决了 19409d9 留下的核心问题："这些证据究竟按照什么命理规则组合，才能产生一个'辨'。"

Judgment Logic Kernel 提供了一个通用的符号推理执行器，通过 REQUIRED / SUFFICIENT / OPPOSE / BLOCK / TRANSFORM / QUALIFY 等操作符，以及 precedence / conflict / absence / exception 等机制，实现了 A+B+C → 整体辨识的符号逻辑，而不是靠 score/weight/threshold。

演示验证了：当支持条件（得令+得地+得势）与制约条件（官杀重）同时存在时，系统输出 UNRESOLVED，而不是强行用"支持数量 > 制约数量"来判断。这正是我们想要的行为。

现在 Judgment Logic Kernel 已经立住了，下一步就是基于它实现具体的经典辨证策略（旺衰、格局、调候等），完成最小垂直切片。

---

*本设计文档是 P0-2.7.1A Judgment Logic Kernel 的成果。通过定义通用的符号推理执行器（11 种逻辑操作符、8 种逻辑组、完整的辨证执行流程），并用人工构造的逻辑案例验证 A+B+C → Overall State（6 条证据：3 支持+2 制约+1 修改器 → UNRESOLVED），证明了传统命理的辨证过程可以被一个确定性、可审计、无评分、允许 UNRESOLVED 的符号逻辑系统真实表达出来。全程未使用 score/weight/threshold，未使用 support_count > oppose_count。*
