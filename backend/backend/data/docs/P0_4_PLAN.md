# P0-4 工作计划：Local Judgment 多条件语义验证

**目标**: 验证多 Condition 的逻辑语义（AND/OR/blocking/prerequisite）

---

## 一、背景

P0-3.9 通过，但发现语义局限：
- 当前是简单模型：所有 Condition 满足 → Judgment
- 实际五经会遇到复杂逻辑

需要验证：
```
多个 Condition
↓
AND / OR / blocking / prerequisite
↓
Local Judgment
```

---

## 二、Condition 逻辑类型

### 1. AND（全部满足）
```
A AND B → 只有 A 和 B 都满足才产生 Judgment
```

### 2. OR（任一满足）
```
A OR B → A 或 B 满足即可产生 Judgment
```

### 3. Blocking（阻断条件）
```
A 满足，但 B 阻断 → 不产生 Judgment
```

### 4. Prerequisite（前提条件）
```
A 是 B 的前提 → A 不满足则 B 不评估
```

### 5. UNRESOLVED（未解析）
```
无法确定是否满足 → 不产生 Judgment
```

---

## 三、Condition 类型定义

```python
class ConditionType(str, Enum):
    SUPPORTING = "SUPPORTING"      # 支持条件（AND 逻辑）
    OPTIONAL = "OPTIONAL"          # 可选条件（OR 逻辑）
    BLOCKING = "BLOCKING"          # 阻断条件
    PREREQUISITE = "PREREQUISITE"  # 前提条件
```

---

## 四、多条件评估逻辑

```python
def evaluate_conditions(conditions: List[Condition], features: D1FeatureResult) -> tuple:
    """评估多个 Condition，返回 (can_judge, reason)
    
    逻辑：
    1. 检查所有 BLOCKING 条件 → 如果有阻断，返回 False
    2. 检查所有 PREREQUISITE 条件 → 如果不满足，返回 False
    3. 检查所有 SUPPORTING 条件 → 必须全部满足
    4. 检查所有 OPTIONAL 条件 → 至少满足一个
    """
    blocking_failed = []
    prerequisite_failed = []
    supporting_met = []
    supporting_failed = []
    optional_met = []
    optional_failed = []
    
    for cond in conditions:
        result, status = evaluate_condition(cond, features)
        
        if cond.type == ConditionType.BLOCKING:
            if not result:
                blocking_failed.append(cond.text)
        elif cond.type == ConditionType.PREREQUISITE:
            if not result:
                prerequisite_failed.append(cond.text)
        elif cond.type == ConditionType.SUPPORTING:
            if result:
                supporting_met.append(cond.text)
            else:
                supporting_failed.append(cond.text)
        elif cond.type == ConditionType.OPTIONAL:
            if result:
                optional_met.append(cond.text)
            else:
                optional_failed.append(cond.text)
    
    # 判断是否可以产生 Judgment
    if blocking_failed:
        return False, f"阻断条件: {blocking_failed}"
    
    if prerequisite_failed:
        return False, f"前提条件不满足: {prerequisite_failed}"
    
    if supporting_failed:
        return False, f"支持条件未满足: {supporting_failed}"
    
    if not optional_met and not optional_failed:
        return False, "无可选条件满足"
    
    return True, f"满足条件: supporting={len(supporting_met)}, optional={len(optional_met)}"
```

---

## 五、测试场景

### 场景 1: 简单 AND
- Condition A: de_ling=True
- Condition B: support_count > drain_count
- 预期: 两个都满足才产生 Judgment

### 场景 2: OR 逻辑
- Condition A: de_ling=True
- Condition B: de_di >= 2
- 预期: 任一满足即可

### 场景 3: Blocking
- Condition A: de_ling=True (支持)
- Condition B: climate=="extreme" (阻断)
- 预期: climate 极端时不产生 Judgment

### 场景 4: Prerequisite
- Condition A: de_ling=True (前提)
- Condition B: support_count > 2 (支持)
- 预期: de_ling 不满足时不评估 B

### 场景 5: UNRESOLVED
- Condition: feature_ref 不存在
- 预期: 不产生 Judgment

---

## 六、验证链路

```
真实 Chart → Feature → Primitive（多Condition）→ 条件评估 → Local Judgment → Trace
```

---

## 七、成功标准

✅ 多条件逻辑正确执行  
✅ AND/OR/blocking/prerequisite 语义正确  
✅ UNRESOLVED 不产生 Judgment  
✅ 未授权不产生 Judgment  
✅ 使用真实 BaziEngine 数据

---

**等待 GPT 裁决后开始执行**
