# PATCH-159 Answer/Interpretation Layer 设计契约 v1

Judgment → Interpretation → 现代语言表达。冻结边界。

## 核心红线
- Judgment ≠ Interpretation
- Interpretation 不改 Judgment
- 经典原文与现代释义分离
- 释义必须反挂 judgment_id
- 释义层不新增任何命理事实/规则/判断
- PENDING_REVIEW 不得生成确定性释义
- 未来 LLM 只做表达润色，不补事实/规则/判断
- Provenance 继续向后可追溯

## Interpretation Schema
```json
{
  "interpretation_id": "",
  "judgment_id": "",
  "plain_text": "",
  "language": "zh-CN",
  "based_on": ["assertion_ids..."],
  "source_evidence": ["..."],
  "authorization": "RECORDED",
  "status": "",
  "note": "仅表达, 不新增判断"
}
```

## 边界
| Judgment | Interpretation |
|---|---|
| RECORDED(SUPPORTED) | 可产释义, 但只复述方向 |
| RECORDED(NOT_SUPPORTED) | 可产否定方向释义 |
| PENDING_REVIEW | 不产确定性释义, 标待判 |

## 隔离区
- 财太露专项独立
- 刑/破/害 Relation 隔离

## 上游
158 Judgment 只读消费, 不改 158。
