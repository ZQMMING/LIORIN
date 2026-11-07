# PATCH-158 Judgment Producer 阶段封板

## 链路
157 candidate_direction (只读)
  ↓ Judgment Producer
  ↓ Judgment (RECORDED/PENDING_REVIEW/fail-closed)

## 三路径
| direction | Judgment |
|---|---|
| SUPPORTED | RECORDED, 带provenance |
| NOT_SUPPORTED | RECORDED, 否定方向 |
| PENDING | PENDING_REVIEW, 不产确定 |

## Provenance 纪律
- Judgment → assertion_ids → source_evidence → 原文
- 无 evidence → NO_PROVENANCE_FAIL_CLOSED
- 同词多 assertion → AMBIGUOUS_PROVENANCE_FAIL_CLOSED

## Schema
judgment_id/subject/predicate/object/direction/state/evidence/assertion_ids/source/provenance/authorization/status 齐全
note 固定"非成格/吉凶"。

## 隔离区(禁入)
- 财太露语义研究
- 刑/破/害 Relation

## Golden
15/15 全过(含158.2 Schema完整性)。
不补 L0/Relation/Assertion; 不改157状态机。
SEALED。
