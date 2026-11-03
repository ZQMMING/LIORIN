# P0-2.7.1A-R Judgment Logic Kernel Contract Hardening — 辨证逻辑内核契约加固

> **设计时间**：2026-08-29
> **基于 commit**：`1ab18c1`
> **目标**：修复 1ab18c1 中发现的 7 个工程问题，将 Judgment Logic Kernel 从"Prototype / Contract Proof"加固为"Production-Ready Contract"
> **验证状态**：✅ 7 个 KERNEL_TEST 全部通过，演示验证通过

---

## 一、修复背景

### 1ab18c1 的裁决

1ab18c1（P0-2.7.1A）已证明"工程上可以做一个无评分的符号辨证执行器"，但还没有证明"这个执行器已经正确表达命理辨证"。

裁决：P0-2.7.1A 可以 PASS 为"Kernel Prototype / Contract Proof"，但不能 PASS 为"Judgment Kernel Production-Ready"。

### 发现的 7 个必须修复的问题 + 1 个后续发现的问题

| 编号 | 问题 | 严重程度 |
|------|------|---------|
| R1 | Evidence 可变（TRANSFORM 直接修改原 Evidence 对象的 polarity） | 🔴 P0 必修 |
| R2 | numeric confidence（confidence: float = 1.0） | 🔴 P0 必修 |
| R3 | CONSTRAINT ≠ REJECT（OPPOSE 自动代表强制约，Kernel 越界解释命理语义） | 🔴 P0 必修 |
| R4 | SUFFICIENT 拥有内建命理语义（Kernel 解释"什么叫充分条件"） | 🟡 需明确 |
| R5 | AND/OR 太简单（需要 Expression Tree，而不是扁平 group list） | 🟡 需演进 |
| R6 | Kernel 内建命理优先级（固定执行顺序 OVERRIDE→BLOCK→REQUIRED→...） | 🟡 需明确 |
| R7 | Kernel vs Classical Validation 边界不清（测试混在一起） | 🟡 需明确 |
| **R8** | **规则聚合过于简单（confirmed[0] 直接拿第一条，precedence 只是排序不是裁决机制）** | **🔴 P0 必修（后续审核发现）** |

---

## 二、7 个修复的详细说明

### R1 — Evidence 不可变

#### 问题

1ab18c1 的代码中，TRANSFORM 操作直接修改原 Evidence 对象：

```python
# 错误：直接修改原始 Evidence
if e.polarity == Polarity.SUPPORT:
    e.polarity = Polarity.CONSTRAINT  # 原地修改！
```

这违反了一个非常重要的原则：Evidence 应该是事实推导结果，不应该被 Judgment Engine 原地改写。

**风险**：
- 同一个 Evidence 在不同 Judgment Engine 之间可能产生污染
- 滴天髓修改 E001 后，子平真诠读取已经修改后的 E001
- 可审计性丧失：无法追溯原始 Evidence 是什么

#### 修复方案

使用 **EffectiveEvidence（有效证据视图）**，不修改原始 Evidence：

```python
@dataclass(frozen=True)  # R1: frozen=True 保证不可变
class Evidence:
    """辨证证据（不可变）"""
    evidence_id: str
    judgment_target: str
    evidence_type: str
    polarity: Polarity
    # ... 其他字段
    # 注意：没有任何方法可以修改这些字段

@dataclass
class EffectiveEvidence:
    """R1: 有效证据视图
    
    不修改原始 Evidence，而是在 EvaluationContext 中表达
    "在某个辨证规则下，这个 Evidence 的有效解释是什么"。
    """
    original_evidence: Evidence         # 原始 Evidence（不可变）
    evaluation_context: EvaluationContext  # 评估上下文
    effective_polarity: Polarity        # 有效极性（可能与原始不同）
    effective_status: EvidenceStatus     # 有效状态
    transform_reasons: List[str]        # 转化原因
    is_modified: bool = False            # 是否被修改
```

#### 验证结果

```
[测试 5] R1 Evidence 不可变（使用 EffectiveEvidence）
  ✓ EffectiveEvidence 极性改变为 CONSTRAINT，原始 Evidence 仍为 SUPPORT（不可变）
```

演示中也验证了：
```
R1: E-S-004 有效极性=constraint, 原始极性=support (不可变)
```

---

### R2 — 删除 numeric confidence

#### 问题

1ab18c1 的代码中：

```python
confidence: float = 1.0  # 置信度（证据确定性，不是力量评分）
```

虽然解释是"证据确定性，不是力量评分"，但仍然存在风险：

- 以后任何人都很容易变成 `0.7 × evidence`、`0.9 × evidence`
- 最终重新产生隐性加权
- "这个证据确定不确定"应该由上游 Evidence Derivation / Provenance 决定，不是 Judgment Kernel 自己判断

#### 修复方案

使用**离散确定性状态 CertaintyState**，替代 numeric confidence：

```python
class CertaintyState(Enum):
    """R2: 证据确定性状态（离散，替代 numeric confidence）
    
    注意：这不是力量评分，是证据推导的确定性。
    由上游 Evidence Derivation / Provenance 决定，不是 Judgment Kernel 自己判断。
    """
    DERIVED = "derived"        # 已从确定的 Fact/Relation 推导出来
    QUALIFIED = "qualified"    # 有条件推导（需要额外条件）
    UNKNOWN = "unknown"        # 未知（无法确定）
    UNRESOLVED = "unresolved"  # 未解决（存在冲突或证据不足）
```

Evidence 数据结构：

```python
@dataclass(frozen=True)
class Evidence:
    # ... 其他字段
    certainty_state: CertaintyState = CertaintyState.DERIVED  # R2: 离散确定性状态
    # 注意：没有 confidence: float 字段
```

#### 验证结果

```
[测试 6] R2 离散确定性状态（替代 numeric confidence）
  ✓ 使用 certainty_state（DERIVED），没有 numeric confidence
```

---

### R3 — CONSTRAINT ≠ REJECT

#### 问题

1ab18c1 的代码逻辑：

```python
has_strong_constraint = any(
    condition.operator == LogicOperator.OPPOSE
    for ...
)
# 然后：
if has_strong_constraint and not has_sufficient_support:
    base_result = JudgmentOutcome.REJECTED  # 错误！自动 REJECTED
```

这在纯逻辑系统里没问题，但在命理里：

> "有制约关系"不等于"足以否定整个辨证结论"。

例如：
- 官杀本身是"克日主"，这是 Relation
- 然后在某个辨证目标里，官杀对日主形成制约，可以成为 Evidence
- 但"制约是否足以推翻偏强"，必须由具体经典规则决定
- 不能由通用 Kernel 的 `OPPOSE = strong_constraint` 提前决定

#### 修复方案

1. **Kernel 只知道条件是否满足，不知道"制约是否足以推翻结论"**
2. **只有 Rule 明确声明 BLOCK 才会导致规则不适用（NOT_APPLICABLE）**
3. **CONSTRAINT 本身不会自动导致 REJECTED**

```python
# R3: 检查 BLOCK（Rule 明确声明 BLOCK → 规则不适用，NOT_APPLICABLE）
# 注意：BLOCK 不是 REJECTED，而是"这个规则不适用"
if self.block_expression:
    block_result = self.block_expression.evaluate(effective_evidences)
    if block_result.satisfied:
        return RuleEvaluationResult(
            rule_id=self.rule_id,
            outcome=JudgmentOutcome.NOT_APPLICABLE,  # R3: BLOCK → NOT_APPLICABLE
            output_state=None,
            blocked=True,
            reasoning=f"阻断规则成立，此规则不适用",
            ...
        )

# R3: 主表达式满足 → CONFIRMED（不会因为有 CONSTRAINT 就自动 REJECT）
if main_result.satisfied:
    base_outcome = JudgmentOutcome.CONFIRMED
else:
    base_outcome = JudgmentOutcome.UNRESOLVED
```

在 FinalJudgment 综合处理时，过滤掉 NOT_APPLICABLE 的规则：

```python
# R3: 过滤掉 NOT_APPLICABLE（被 BLOCK 的规则不参与综合）
applicable_results = [r for r in rule_results if not r.is_not_applicable()]
```

#### 验证结果

```
[测试 4] BLOCK 逻辑（R3: CONSTRAINT ≠ REJECT）
  ✓ BLOCK(B) 成立 → NOT_APPLICABLE（Rule 明确声明 BLOCK，规则不适用）
```

演示中也验证了：
```
J-DTS-WEAK-001: not_applicable → N/A
  推理: 阻断规则成立，此规则不适用
```

最终结果正确：
```
[DITIANSUI] DAY_MASTER_STRENGTH: confirmed = 偏强
推理: 1 条规则确认：偏强
```

（偏弱规则被 BLOCK，不适用，所以只有偏强规则适用，最终结果是偏强，而不是之前的 UNRESOLVED）

---

### R4 — SUFFICIENT 不得拥有内建命理语义

#### 问题

1ab18c1 中：

```python
ROOT_MAIN_QI_SUPPORT operator = SUFFICIENT
# 然后 Kernel 解释：
has_sufficient_support = any(
    condition.operator == LogicOperator.SUFFICIENT
    for ...
)
# 这意味着 Kernel 在解释"什么叫充分条件"
```

"充分条件"不是一个通用命理事实，它必须是某一具体命理规则授权的。

例如：
- 本气根能不能成为"偏强"的充分条件？
- 这不是 Logic Kernel 可以回答的
- 这是滴天髓某条规则或者子平真诠某条规则才能回答的问题

#### 修复方案

明确 **SUFFICIENT / OPPOSE 等只是 Rule-local operator**，Kernel 不解释其命理含义：

```python
class LogicOperator(Enum):
    """
    逻辑操作符
    
    R4: SUFFICIENT / OPPOSE 等只是 Rule-local operator，Kernel 不解释其命理含义。
    Kernel 只知道：Rule 声明了某个条件使用了某个 operator。
    """
    AND = "and"
    OR = "or"
    NOT = "not"
    REQUIRED = "required"    # Rule-local 语义
    SUFFICIENT = "sufficient"  # Rule-local 语义，Kernel 不解释命理含义
    OPPOSE = "oppose"        # 注意：OPPOSE ≠ REJECT，只是制约
    BLOCK = "block"          # Rule 明确声明
    OVERRIDE = "override"    # Rule 明确声明
    TRANSFORM = "transform"  # 转化证据解释
    QUALIFY = "qualify"      # 降低结论等级
    NEGATE = "negate"
```

在 JudgmentExpression 中添加 `rule_local_semantics` 字段，明确这是 Rule-local 的：

```python
@dataclass
class JudgmentExpression:
    operator: LogicOperator
    # ... 其他字段
    
    # R4: Rule-local 语义（Kernel 不解释其命理含义）
    rule_local_semantics: Dict[str, Any] = field(default_factory=dict)
```

#### 验证结果

Kernel 不再解释 SUFFICIENT 的命理含义，只是把它作为 Rule 声明的一个操作符来执行。主表达式的评估只检查条件是否满足，不解释"充分"的命理含义。

---

### R5 — Expression Tree（表达式树）

#### 问题

1ab18c1 中使用扁平的 group list：

```python
required_groups: List[LogicGroup]
support_groups: List[LogicGroup]
constraint_groups: List[LogicGroup]
modifier_groups: List[LogicGroup]
...
```

AND/OR 只是 `all()` / `any()`，这对于第一版 Demo 没问题。

但是命理真正复杂的是：

```
A + B + C 并不是所有情况下都是 A AND B AND C
而可能是：
(A AND B) OR C
或者：
A REQUIRED + (B OR C) + D NOT BLOCKED
甚至：
A ↓ 如果 B 成立 ↓ A 的意义发生改变
```

所以真正需要的是**表达式树**，而不是 group list。

#### 修复方案

创建 **JudgmentExpression（辨证表达式树）**，支持嵌套表达式：

```python
@dataclass
class JudgmentExpression:
    """
    R5: 辨证表达式树
    
    替代 required_groups / support_groups / constraint_groups 等扁平 group list。
    支持嵌套表达式：AND(REQUIRED(A), OR(B, C), NOT(BLOCK(D)))
    
    这才真正可以表达传统辨证的条件组合。
    """
    operator: LogicOperator             # 逻辑操作符
    description: str = ""               # 表达式描述
    
    # 叶子节点：引用 Evidence
    evidence_type: Optional[str] = None
    evidence_id: Optional[str] = None
    expected_status: EvidenceStatus = EvidenceStatus.PRESENT
    
    # 组合节点：子表达式
    sub_expressions: List['JudgmentExpression'] = field(default_factory=list)
    
    # R4: Rule-local 语义
    rule_local_semantics: Dict[str, Any] = field(default_factory=dict)
    
    def evaluate(self, effective_evidences: Set[EffectiveEvidence]) -> 'ExpressionResult':
        """评估表达式（支持递归）"""
        if self.sub_expressions:
            # 组合节点
            sub_results = [se.evaluate(effective_evidences) for se in self.sub_expressions]
            if self.operator == LogicOperator.AND:
                satisfied = all(r.satisfied for r in sub_results)
            elif self.operator == LogicOperator.OR:
                satisfied = any(r.satisfied for r in sub_results)
            elif self.operator == LogicOperator.NOT:
                satisfied = not all(r.satisfied for r in sub_results)
            # ...
        else:
            # 叶子节点：检查 Evidence 是否存在
            # ...
```

在 JudgmentRule 中使用表达式树：

```python
@dataclass
class JudgmentRule:
    # R5: 表达式树（替代扁平 group list）
    main_expression: JudgmentExpression = field(
        default_factory=lambda: JudgmentExpression(operator=LogicOperator.AND)
    )
    block_expression: Optional[JudgmentExpression] = None
    override_expression: Optional[JudgmentExpression] = None
    qualify_expression: Optional[JudgmentExpression] = None
```

演示中的表达式树：

```python
main_expression=JudgmentExpression(
    operator=LogicOperator.AND,
    description="得令 + 得地 + 得势",
    sub_expressions=[
        JudgmentExpression(
            operator=LogicOperator.REQUIRED,
            evidence_type="SEASONAL_SUPPORT",
            description="得令（必要条件）"
        ),
        JudgmentExpression(
            operator=LogicOperator.AND,
            evidence_type="ROOT_MAIN_QI_SUPPORT",
            description="得地（本气根）"
        ),
        JudgmentExpression(
            operator=LogicOperator.AND,
            evidence_type="RESOURCE_SUPPORT",
            description="得势（透印）"
        ),
    ]
)
```

#### 验证结果

演示中成功使用了表达式树：
```
R5 ✓ 使用 Expression Tree（AND(REQUIRED(A), AND(B), AND(C))）
```

---

### R6 — Kernel 不规定命理优先级

#### 问题

1ab18c1 中定义了固定的执行顺序：

```
OVERRIDE → BLOCK → REQUIRED → TRANSFORM → MODIFIER → SUPPORT + CONSTRAINT → QUALIFICATION
```

这作为一个通用执行器的默认流程可以，但是不能写成"所有命理体系永远必须按这个顺序辨"。

因为：
- 滴天髓、子平真诠、穷通宝鉴、三命通会、渊海子平
- 它们的规则结构不一定都符合这个统一优先级

因此 Kernel 应该提供"执行机制"，而不是规定"命理优先级"。

#### 修复方案

1. **优先级来自 JudgmentRule 的声明（precedence 字段）**，不是 Kernel 默认决定
2. **执行流程由 Rule 的表达式树和声明决定**，不是 Kernel 固定顺序

```python
@dataclass
class JudgmentRule:
    # ... 其他字段
    
    # R6: 优先级（来自 Rule 声明，不是 Kernel 默认）
    precedence: int = 0
    
    # 冲突与缺失策略（来自 Rule 声明）
    conflict_policy: str = "unresolved"
    absence_policy: str = "unresolved"
```

在 JudgmentEngine 中按 Rule 声明的 precedence 排序执行：

```python
class JudgmentEngine:
    def add_rule(self, rule: JudgmentRule):
        """添加辨证规则（按 system 和 target 过滤，按 precedence 排序）"""
        if rule.system == self.system and rule.target == self.target:
            self.rules.append(rule)
            self.rules.sort(key=lambda r: -r.precedence)  # R6: 按 Rule 声明排序
    
    def evaluate(self, evidence_set: Set[Evidence]) -> 'FinalJudgment':
        # R6: 按 Rule 声明的 precedence 排序执行
        rule_results = []
        for rule in self.rules:  # 已经按 precedence 排序
            result = rule.evaluate(applicable_evidence)
            rule_results.append(result)
```

#### 验证结果

```
R6 ✓ 优先级来自 Rule 声明（precedence），不是 Kernel 默认决定
```

演示中：
- J-DTS-STRONG-001 precedence=10
- J-DTS-WEAK-001 precedence=5
- 按 precedence 排序执行

---

### R7 — Kernel vs Classical Validation 边界

#### 问题

1ab18c1 中，Kernel 测试和经典辨证测试混在一起，没有明确边界。

这会导致一个非常危险的混淆：
- "程序可以根据预先写好的逻辑产生 UNRESOLVED"
- 被误认为
- "滴天髓面对这个命例真的应该这样辨"

这两个是完全不同的验证目标。

#### 修复方案

创建 **TestCategory（测试分类枚举）**，明确两套测试的边界：

```python
class TestCategory(Enum):
    """
    R7: 测试分类边界
    
    KERNEL_TEST：验证逻辑执行器本身（AND/OR/NOT/BLOCK/TRANSFORM/UNRESOLVED 等）
    CLASSICAL_JUDGMENT_TEST：验证某条经典 + 某个命例 + 某组 Evidence = 原典授权的 Judgment
    
    两套测试绝对不能混。
    """
    KERNEL_TEST = "kernel_test"
    CLASSICAL_JUDGMENT_TEST = "classical_judgment_test"
```

在 JudgmentRule 中声明测试分类：

```python
@dataclass
class JudgmentRule:
    # ... 其他字段
    test_category: TestCategory = TestCategory.CLASSICAL_JUDGMENT_TEST  # R7: 测试分类
```

实现两套测试：

```python
def run_kernel_tests():
    """
    R7: KERNEL_TEST — 验证逻辑执行器本身
    
    只验证：AND/OR/NOT/BLOCK/TRANSFORM/UNRESOLVED 等逻辑操作是否正确执行。
    不验证：某条经典 + 某个命例 + 某组 Evidence = 原典授权的 Judgment。
    
    两套测试绝对不能混。
    """
    # 测试 1: AND 逻辑
    # 测试 2: OR 逻辑
    # 测试 3: NOT 逻辑
    # 测试 4: BLOCK 逻辑（R3: CONSTRAINT ≠ REJECT）
    # 测试 5: R1 Evidence 不可变
    # 测试 6: R2 离散确定性状态
    # 测试 7: UNRESOLVED 是合法结果
```

```python
def demo_strength_judgment():
    """
    演示：旺衰辨证（使用 R1-R7 修复后的版本）
    
    这是 CLASSICAL_JUDGMENT_TEST，验证某条经典 + 某个命例 + 某组 Evidence。
    注意：这只是 Demo，不是完整的经典辨证验证。
    完整的经典辨证验证需要原典授权的规则和命例。
    """
```

#### 验证结果

```
R7 ✓ 测试分两套 KERNEL_TEST 和 CLASSICAL_JUDGMENT_TEST
```

KERNEL_TEST 结果：
```
KERNEL_TEST 结果：7 通过，0 失败
```

---

### R8 — 规则聚合与互斥组（precedence 成为真正的裁决机制）

#### 问题

b0b8322 审核时发现：JudgmentEngine 的最终规则聚合仍然过于简单。

```python
# 错误：直接拿第一条
if confirmed:
    final_outcome = JudgmentOutcome.CONFIRMED
    output_state = confirmed[0].output_state  # 直接拿第一条！
```

这有一个危险：

假设两个不同 Rule：
- Rule A → CONFIRMED = 偏强（precedence=10）
- Rule B → CONFIRMED = 偏弱（precedence=5）

现在：
- confirmed = [A, B]
- 最后：output_state = confirmed[0].output_state = 偏强

这不行。因为：
1. precedence 目前只是 execution order，不是真正的 semantic precedence
2. 没有区分"同一 Target 的互斥结果"和"不同 Target 的互补结果"
3. 没有 state_space, exclusivity, compatibility, resolution_policy

#### 修复方案

1. **给 JudgmentRule 添加三个新字段**：

```python
# R8: 结论空间与互斥性
state_space: List[str] = field(default_factory=list)  # 结论空间
exclusivity_group: str = "default"  # 互斥组（同一组内结论互斥）
resolution_policy: str = "unresolved"  # 冲突解决策略
```

2. **resolution_policy 三种策略**：
   - `precedence_override`: 高 precedence 覆盖低 precedence
   - `unresolved`: 冲突 → UNRESOLVED（默认最保守）
   - `parallel`: 并行输出（仅适用于非互斥组）

3. **修复 JudgmentEngine 的聚合逻辑**：
   - 按 exclusivity_group 分组
   - 同一互斥组内，如果有多个 CONFIRMED，按 resolution_policy 处理
   - 不同互斥组的结果可以并行（互补不比较）

4. **FinalJudgment 支持多组并行输出**：

```python
group_outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
```

#### 验证结果

```
[测试 8] R8 规则聚合与互斥组（precedence_override）
  ✓ 同一互斥组多规则 CONFIRMED → precedence_override 选高优先级 STATE_A

[测试 8b] R8 规则聚合（unresolved 策略：冲突 → UNRESOLVED）
  ✓ 同一互斥组多规则 CONFIRMED + unresolved 策略 → UNRESOLVED
```

演示中也验证了：
```
[DITIANSUI] DAY_MASTER_STRENGTH: confirmed = 偏强
推理: 互斥组[STRENGTH_LEVEL] 确认：偏强
```

---

## 三、验证结果总览

### KERNEL_TEST（9 项全部通过）

| 测试编号 | 测试内容 | 结果 |
|---------|---------|------|
| 测试 1 | AND 逻辑 | ✓ 通过 |
| 测试 2 | OR 逻辑 | ✓ 通过 |
| 测试 3 | NOT 逻辑 | ✓ 通过 |
| 测试 4 | BLOCK 逻辑（R3: CONSTRAINT ≠ REJECT） | ✓ 通过 |
| 测试 5 | R1 Evidence 不可变 | ✓ 通过 |
| 测试 6 | R2 离散确定性状态 | ✓ 通过 |
| 测试 7 | UNRESOLVED 是合法结果 | ✓ 通过 |
| 测试 8 | R8 规则聚合（precedence_override） | ✓ 通过 |
| 测试 8b | R8 规则聚合（unresolved 策略） | ✓ 通过 |

### 演示验证（CLASSICAL_JUDGMENT_TEST）

**场景**：甲日主，寅月
- A = 得令（临官）→ SUPPORT
- B = 得地（本气根）→ SUPPORT
- C = 得势（透印）→ SUPPORT
- D = 官杀重 → CONSTRAINT
- E = 财旺 → CONSTRAINT
- F = 根被冲 → MODIFIER

**结果**：
```
[DITIANSUI] DAY_MASTER_STRENGTH: confirmed = 偏强
推理: 1 条规则确认：偏强

详细规则结果：
  J-DTS-STRONG-001: confirmed → 偏强
    推理: 主条件成立; 匹配证据：E-S-001, E-S-004, E-S-006
    R1: E-S-004 有效极性=constraint, 原始极性=support (不可变)
  J-DTS-WEAK-001: not_applicable → N/A
    推理: 阻断规则成立，此规则不适用
```

**关键验证点**：
- R1 ✓ Evidence 不可变（E-S-004 有效极性改变，原始极性不变）
- R2 ✓ 使用 certainty_state，没有 numeric confidence
- R3 ✓ CONSTRAINT ≠ REJECT（BLOCK → NOT_APPLICABLE，偏弱规则不适用）
- R4 ✓ SUFFICIENT/OPPOSE 等只是 Rule-local operator
- R5 ✓ 使用 Expression Tree
- R6 ✓ 优先级来自 Rule 声明
- R7 ✓ 测试分两套
- ✓ 未使用 score/weight/threshold
- ✓ 未使用 support_count > oppose_count
- ✓ UNRESOLVED 是合法结果
- ✓ A+B+C+D+E+F 通过符号逻辑组合得到整体状态

---

## 四、当前状态

### Judgment Logic Kernel 状态

| 项目 | 1ab18c1（修复前） | 1ab18c1-R（修复后） |
|------|-------------------|---------------------|
| Evidence 可变性 | 🔴 可变（TRANSFORM 原地修改） | ✅ 不可变（frozen + EffectiveEvidence） |
| 确定性表示 | 🔴 numeric confidence | ✅ 离散 CertaintyState |
| CONSTRAINT vs REJECT | 🔴 OPPOSE 自动 REJECTED | ✅ CONSTRAINT ≠ REJECT，BLOCK → NOT_APPLICABLE |
| SUFFICIENT 语义 | 🟡 Kernel 内建命理含义 | ✅ Rule-local operator，Kernel 不解释 |
| 条件表达 | 🟡 扁平 group list | ✅ Expression Tree（支持嵌套） |
| 优先级 | 🟡 Kernel 固定执行顺序 | ✅ 来自 Rule 声明（precedence） |
| 测试边界 | 🟡 混在一起 | ✅ KERNEL_TEST vs CLASSICAL_JUDGMENT_TEST |
| KERNEL_TEST | N/A | ✅ 7/7 通过 |
| 演示验证 | N/A | ✅ 通过 |

### 裁决更新

| 项目 | 1ab18c1 裁决 | 1ab18c1-R 裁决 |
|------|-------------|----------------|
| Kernel Prototype / Contract Proof | ✅ PASS | ✅ PASS |
| Judgment Kernel Production-Ready | ❌ NOT PASS | 🟡 Contract Ready（逻辑内核已加固，但具体经典辨证策略还需实现） |
| 可以直接做真实旺衰 | ❌ 暂缓 | 🟡 可以开始 Evidence Derivation Vertical Slice（极小目标） |

---

## 五、下一步建议

### P0-2.7.1B — Evidence Derivation Vertical Slice（高优先级）

**注意**：第一刀不是"做完整旺衰"，而是做一个真实的 Evidence Derivation 垂直切片。

**只选一个极小目标：日主根气**

完整走：
```
BaziChart
    ↓
Canonical Facts
    ↓
Relation: DM 甲 + 寅 contains 甲
    ↓
Evidence: ROOT_PRESENT
    ↓
某一经典明确授权的局部判断
    ↓
Judgment Logic Kernel
    ↓
Root State
```

然后再扩展：
- 得令
- 得地
- 得势

最后才：
- A+B+C ↓ 整体旺衰

### P0-2.7.2 — 推广到其他辨证目标（高优先级）

- 格局辨证（子平真诠）
- 调候辨证（穷通宝鉴）
- 体用辨证（滴天髓）
- 关系转化辨证（三命通会）

### P0-2.7.3 — 迁移现有 Rule（中优先级）

- 34 条 RELATION 层 Rule → relations/
- 2 条 EVIDENCE 层 Rule → evidence/
- 94 条 JUDGMENT 层 Rule → Judgment Strategy
- 6 条 UNCERTAIN 层 Rule → 人工审查

### P0-3 — Boundary Cases（高优先级）

### P0-4 — Calculation Golden Dataset（高优先级）

---

## 六、总结

### 本次修复的核心成果

1. ✅ **R1 Evidence 不可变**：使用 frozen dataclass + EffectiveEvidence，不修改原始 Evidence
2. ✅ **R2 删除 numeric confidence**：使用离散 CertaintyState（DERIVED/QUALIFIED/UNKNOWN/UNRESOLVED）
3. ✅ **R3 CONSTRAINT ≠ REJECT**：只有 Rule 明确声明 BLOCK 才会 NOT_APPLICABLE，CONSTRAINT 不会自动 REJECTED
4. ✅ **R4 SUFFICIENT 无内建命理语义**：只是 Rule-local operator，Kernel 不解释其命理含义
5. ✅ **R5 Expression Tree**：支持嵌套表达式 AND(REQUIRED(A), OR(B, C), NOT(BLOCK(D)))
6. ✅ **R6 Kernel 不规定命理优先级**：优先级来自 Rule 声明（precedence）
7. ✅ **R7 Kernel vs Classical Validation 边界**：测试分两套 KERNEL_TEST 和 CLASSICAL_JUDGMENT_TEST

### 核心原则（更新版）

> 辨不是 Rule 的执行结果；辨是某一命理体系在共享的事实与关系空间中，对特定辨证目标进行证据组织、条件判断和状态归纳的过程。

> 同源事实，不同辨法；共享关系，不共享结论。

> Evidence 不可变；CONSTRAINT ≠ REJECT；Kernel 提供执行机制，不规定命理优先级；UNRESOLVED 是合法结果。

### 最重要的一句话

这次 P0-2.7.1A-R 真正把 Judgment Logic Kernel 从"Prototype / Contract Proof"加固为"Contract Ready"。7 个工程问题全部修复，7 个 KERNEL_TEST 全部通过，演示验证通过。

现在逻辑内核已经立住了，下一步就是用一个真实、可追溯到原典的最小辨证垂直切片（日主根气）去证明：不是我们发明了一套逻辑，而是我们真的把经典原有的"辨法"准确翻译成了代码。

这才符合一直要求的：先知道是什么 → 做什么 → 缺什么 → 改什么 → 再裁决。

---

*本设计文档是 P0-2.7.1A-R Judgment Logic Kernel Contract Hardening 的成果。通过修复 1ab18c1 中发现的 7 个工程问题（R1 Evidence 不可变、R2 删除 numeric confidence、R3 CONSTRAINT≠REJECT、R4 SUFFICIENT 无内建命理语义、R5 Expression Tree、R6 Kernel 不规定命理优先级、R7 Kernel vs Classical Validation 边界），将 Judgment Logic Kernel 从"Prototype / Contract Proof"加固为"Contract Ready"。7 个 KERNEL_TEST 全部通过，演示验证通过。下一步是用一个真实、可追溯到原典的最小辨证垂直切片（日主根气）去证明经典原有的"辨法"被准确翻译成了代码。*
