# Rule Condition Provenance Contract v1

状态：FROZEN / 施工范围=契约层，不改 Rule 判定逻辑，不碰 L0/L1/L2 主链。

## 1. Rule 结构

```
Rule
├─ rule_id          稳定逻辑ID（如 ZP-RULE-CAI）
├─ bucket           required / blocked / supported / premise / unknown_pending
├─ conditions[]
│   ├─ condition_id     稳定逻辑ID（见 §2）
│   ├─ condition_name   人类可读语义
│   ├─ evidence_refs[]  复用现有 evidence_id（见 §3）
│   └─ authorization    required/blocked/premise/supported/unknown_pending
├─ state            CANDIDATE（不升级成格成）
└─ boundary_note    文本说明
```

## 2. condition_id 规则

格式：`ZP-RULE-{格缩写}-{条件}`

- 稳定、可 Git diff、可版本控制
- 不依赖 dict 顺序
- 禁止运行时随机 ID
- 禁止 condition_001/002 这类顺序号
- 格局缩写统一：
  - CAI 财格 / GUAN 官格 / YIN 印格 / SHISHEN 食神格 / SHANGGUAN 伤官格
  - JIANLU 建禄月劫 / YANGREN 阳刃格
  - WAIGE-JINGLAN 井栏叉 / WAIGE-LIUYIN 六阴朝阳 / WAIGE-XINGHE 刑合 / WAIGE-HELU 合禄
- 条件名用英文短词（ROOT/TRAN/QISHA/XIANGGUAN 等），全大写下划线

示例：
- ZP-RULE-CAI-ROOT        财有根
- ZP-RULE-CAI-TRAN        财透
- ZP-RULE-GUAN-ROOT       官有根
- ZP-RULE-WAIGE-XINGHE    刑合

## 3. evidence_refs[]

- 值只能是现有 `evidence_id`（registries/evidence/*.jsonl 中已存在的 ID）
- 复用现有 Evidence Registry，不新建第二套
- 不复制 Evidence 内容进 Rule
- cardinality：
  - Condition 1 ── N Evidence（一个条件可由多条经典支撑）
  - Evidence   1 ── N Condition（一条 Evidence 可支撑多条件）
- 空 evidence_refs[] = 未授权，不得被默认为"有证据"
- Judgment gate 已有 NO_PROVENANCE fail-closed，空 refs 在接口处继续挡住

## 4. 不变项

- 不改现有 Rule 三态判定逻辑
- 不改 L0 Fact / L1 Signal / L2 Judgment
- 不改 evidence_id 命名
- 不新建 Evidence Registry

## 5. 施工顺序

1. condition_id 规则（本文件）
2. evidence_refs[] schema（本文件）
3. schema 校验脚本
4. 迁一个 Rule 样板
5. 全量迁 11 类
6. provenance regression
7. Judgment gate 同步
