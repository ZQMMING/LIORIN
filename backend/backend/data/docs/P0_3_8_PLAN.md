# P0-3.8 工作计划：Local Judgment Engine 最小闭环

**目标**: 用 4 条 Authorized Primitive 证明 Local Judgment Engine 可稳定运行

---

## 一、背景

P0-3.7 结果：
- 4 条 CLASSICAL_EXPLICIT + VERIFIED
- 5 条 UNRESOLVED / 不授权

关键验证：
- Authorization Gate 阻止未授权项进入 Judgment ✅

---

## 二、核心验证链路

```
Authorized Primitive
↓
Condition Evaluation
↓
Local Judgment
↓
Evidence Trace
```

必须证明：
1. 有 Authorization 的 Primitive → 能产生 Local Judgment
2. 无 Authorization 的 Primitive → 无法产生 Local Judgment

---

## 三、具体任务

### Phase 1: 实现 Condition.Evaluation

```python
def evaluate_condition(
    condition: Condition, 
    features: D1FeatureResult
) -> bool:
    """评估单个 Condition 是否满足
    
    返回 True = 条件满足
    返回 False = 条件不满足
    返回 None = 条件无法评估（UNRESOLVED）
    """
    if condition.status == ConditionStatus.UNRESOLVED:
        return None
    
    # 检查 operator/value 来源
    if condition.operator and condition.value is not None:
        if not condition.source_documented:
            raise ValueError(f"Undocumented condition: {condition.evidence_ref}")
    
    # TODO: 实现具体评估逻辑
    return True
```

### Phase 2: 实现 Local Judgment Engine

```python
def generate_local_judgment(
    primitive: Primitive,
    features: D1FeatureResult
) -> Optional[str]:
    """从 Authorized Primitive 生成 Local Judgment
    
    约束：
    - 只有 VERIFIED 且授权的 Primitive 才能生成
    - 返回 None 表示无法生成（未授权或未满足）
    """
    if not primitive.is_authorized:
        return None
    
    # 评估所有条件
    all_conditions_met = True
    unmet_conditions = []
    
    for condition in primitive.conditions:
        result = evaluate_condition(condition, features)
        if result is False:
            all_conditions_met = False
            unmet_conditions.append(condition.text)
        elif result is None:
            # UNRESOLVED 条件不影响，但不算满足
            pass
    
    if not all_conditions_met:
        return f"[{primitive.evidence_id}] 条件未完全满足: {unmet_conditions}"
    
    # 生成 Local Judgment
    return f"[{primitive.evidence_id}] {primitive.primitive_name}: {primitive.source_text[:50]}..."
```

### Phase 3: 实现 Evidence Trace

```python
def get_evidence_trace(
    primitive: Primitive,
    judgment: str
) -> dict:
    """获取证据追溯信息
    
    返回：
    - evidence_id
    - source_text
    - conditions_evaluated
    - conditions_met
    - authorization_level
    """
    return {
        'evidence_id': primitive.evidence_id,
        'source_text': primitive.source_text,
        'conditions_evaluated': len(primitive.conditions),
        'conditions_met': sum(1 for c in primitive.conditions if c.status == ConditionStatus.RESOLVED),
        'authorization_level': primitive.authorization_level.value,
        'judgment': judgment,
    }
```

### Phase 4: 测试验证

对 4 条 Authorized Primitive 进行测试：
1. 传入典型 Chart 数据
2. 验证 Condition Evaluation
3. 验证 Local Judgment 生成
4. 验证 Evidence Trace 追溯

---

## 四、禁止事项

❌ 不要扩到 284 条 Primitive  
❌ 不要做综合身强身弱  
❌ 不要使用旧评分逻辑  
❌ 不要跳过 Authorization Gate

---

## 五、成功标准

✅ 4 条 Authorized Primitive 都能生成 Local Judgment  
✅ 5 条 UNRESOLVED Primitive 都不能生成 Local Judgment  
✅ Evidence Trace 完整可追溯  
✅ 测试通过

---

**开始执行**
