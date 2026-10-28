# PATCH-141 Condition Evaluator 设计契约

## 定位
事实层(L0) → Fact Predicate Layer → Condition Evaluator → condition_status
把"财根深"这类古文条件，翻译成对 L0 事实谓词的判断，不写死阈值。

## 分层
```
L0 facts (藏干/透干/十神/根/合冲)
  ↓ Fact Predicate Layer (事实谓词, 纯查询)
  {has_root, root_type, transparent_count, ...}
  ↓ Condition Evaluator
  condition_status: SATISFIED / UNSATISFIED / UNKNOWN
```

## 关键分离
- Fact Predicate Layer：只描述事实（有几根、根在哪、何干透），不下结论
- Condition Evaluator：把古文条件词映射到谓词组合；缺谓词=UNKNOWN

## 输出 Schema（三态，禁 boolean）
```json
{
  "pattern": "正财",
  "condition_status": {
    "required": [
      {"condition": "财根深", "status": "UNKNOWN", "checked_predicates": []}
    ],
    "blocked": [...],
    "supported": [...]
  }
}
```

## 三态
| 状态 | 含义 |
|---|---|
| SATISFIED | 谓词足以支持条件成立 |
| UNSATISFIED | 谓词明确不支持 |
| UNKNOWN | 缺谓词/谓词不足，不猜 |

## 冻结
- ❌ 不写 root_count>=2 这类阈值硬编码
- ❌ 不用 true/false
- ❌ 不一次打开根/透/合/冲/旺衰全部（逐个实现）
- ✅ 每个 condition 的判断走 predicate registry，不散落
- ✅ UNKNOWN 必须保留，不为了完整强行填

## 实施顺序
PATCH-141B 逐个：根 → 透 → 合 → 冲 → 旺衰。
