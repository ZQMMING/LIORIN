# PATCH-158 PZZQ Judgment Producer 设计契约 v1

消费 157 已冻结 candidate_direction，产结构化 Judgment。不改状态机。

## 一、边界红线
- SUPPORTED ≠ "成格/吉/贵"，只是 candidate 方向
- Judgment 必须来自 Assertion + Evidence，Producer 不得自造"古人认为"
- NOT_SUPPORTED → 保留否定/未形成证据，不硬产肯定
- PENDING → 不得产确定性 Judgment
- 不改 157 任何输出；消费不了优先改 Producer，不回头污染状态机

## 二、Judgment Schema
```json
{
  "judgment_id": "",
  "subject": "",
  "predicate": "",
  "object": "",
  "direction": "SUPPORTED/NOT_SUPPORTED",
  "state": "",
  "evidence": [],
  "assertion_ids": [],
  "source": "子平真诠",
  "provenance": "Assertion->Evidence->原文",
  "authorization": "CLASSIC_DIRECT",
  "status": "RECORDED"
}
```

## 三、三态映射
| candidate_direction | Judgment Producer 动作 |
|---|---|
| SUPPORTED | 产 RECORDED Judgment（方向=SUPPORTED，非成格） |
| NOT_SUPPORTED | 产否定/未形成 Judgment |
| PENDING | 不产确定性 Judgment，记 PENDING_REVIEW |

## 四、Provenance 反查
Judgment → assertion_ids → source_evidence → 原文逐字
无 provenance 不产 Judgment。

## 五、隔离区（禁入 158）
- 专项A：财太露语义研究
- 专项B：刑/破/害 Relation
二者不得为多产 Judgment 偷补算法。

## 六、上游契约
14 套 golden 全为上游冻结输出。158 只读不写。
