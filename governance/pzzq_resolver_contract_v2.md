# PATCH-139 PZZQ Resolver v2 设计（契约，不写代码）

## 目标
pattern_candidate + PZZQ Assertion → pattern_condition_state
只"挂条件"，不判成格/破格。

## 流程
```
pattern_candidate(正财, from L0)
  + pzzq_pattern_type_registry_v1 (正财 ↔ 财格/财格成局/财格取运)
  + PZZQ Assertion (subject=财格, predicate=supports/blocks/activates)
  ↓
pattern_condition_state
```

## 输出 Schema（两状态分离）
```json
{
  "pattern": "正财",
  "candidate_status": "CANDIDATE",
  "resolution_status": "CONDITION_ATTACHED",
  "conditions": {
    "required": ["财根深一位清"],
    "blocked": ["比劫夺财", "透杀"],
    "supported": ["财旺生官"]
  },
  "evidence": ["月支/藏干/透干/日干"],
  "source_assertions": ["PZZQ-xxx"]
}
```

## 三类条件挂载规则
| Assertion predicate | 挂到 |
|---|---|
| requires / supports / activates | required / supported |
| blocks / rejects | blocked |
| changes | 留 resolution（本版不判） |

## 冻结边界
- ❌ 不输出成格/破格 final conclusion
- ❌ candidate→格名不硬映射散落代码（走 PatternTypeRegistry）
- ❌ 不做 condition evaluator（不判"财是否根深"）
- ✅ resolution_status 与 candidate_status 分离
- ✅ evidence/source_assertion 保留

## 后续
PATCH-140 才进 condition evaluator（财根深=？需L0根事实+岁运）。
