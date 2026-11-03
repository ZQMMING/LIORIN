# P0-8.9 人工裁决池

**Commit**: 396d359  
**状态**: 🔒 HOLD - 等待人工原典裁决  
**日期**: 2026-08-31

---

## 总览

总断言: 30条
- COMPLETE: 8条（可进入Authorization）
- PARTIAL: 21条（必须HOLD等待人工裁决）
- INSUFFICIENT: 1条（必须HOLD等待人工裁决）

**待裁决总数**: 22条

---

## 人工裁决四问

对每条Assertion，必须回答：

### 1. 原典到底说了什么？
- 回到五书原文
- 定位证据段（Evidence Span）
- 明确原始语义

### 2. 最小语义命题是什么？
- 能否进一步精简？
- 是否包含多个结论？
- 是否混入非原典内容？

### 3. 当前semantic_relation是否完整？
- subject-predicate-object-conclusion是否齐全？
- 语义方向是否正确？
- 是否有缺失的关键关系？

### 4. 当前Condition/Primitive是否忠实？
- Condition是否从Evidence Span合法推导？
- Primitive是否准确反映语义关系？
- 是否存在逆向污染？

---

## 裁决结果只能产生

- **COMPLETE**: 满足四问，进入Authorization
- **REJECT**: 不满足，移出资产库

---

## 裁决规则

1. 不得参考当前Primitive/Condition反向证明原典
2. 必须回到五书原典Evidence
3. 禁止无限产生新PARTIAL
4. 完成22条裁决前，禁止大规模扩张
5. 只允许两种结果：COMPLETE或REJECT

---

## PARTIAL条目（21条）

| # | Passage ID | Evidence Span | Semantic Relation | Audit Reason |
|---|------------|---------------|-------------------|--------------|
| 1 | YHZP-QICAI-001 | 财星旺者， riches naturally follows. | general | 缺少明确语义关系 |
| 2 | YHZP-ZHONGHE-001 | 中和为贵，偏枯为病。 | zhong_he_weigh | 语义不完整 |
| 3 | YHZP-GESU-002 | 格局者，命理之纲也。 | geju_nature | 缺少结论 |
| 4 | SMTH-TIAOHOU-001 | 调候者，平衡冷暖之用。 | tiaohou_nature | 语义关系不明确 |
| 5 | PZZQ-GEJU-001 | 正官格，以财印为辅。 | zheng_guan_ge | 条件层缺失 |
| 6 | PZZQ-GEJU-002 | 七杀格，喜制伏为吉。 | qi_sha_ge | 语义不完整 |
| 7 | PZZQ-GEJU-003 | 食神格，生财为美。 | shi_shen_ge | 条件层缺失 |
| 8 | PZZQ-GEJU-004 | 伤官格，喜财印。 | shang_guan_ge | 语义不完整 |
| 9 | PZZQ-GEJU-005 | 偏财格，喜比劫。 | pian_cai_ge | 条件层缺失 |
| 10 | PZZQ-GEJU-006 | 正财格，喜官杀。 | zheng_cai_ge | 语义不完整 |
| 11 | DTS-YONGSHEN-001 | 用神者，月令提纲之物也。 | yong_shen_source | 语义不完整 |
| 12 | DTS-TONGSHEN-001 | 通神论者，论命之枢机。 | tongshen_theory | 缺少证据定位 |
| 13 | DTS-SHUAIWANG-001 | 太过者反宜制之，不及者正宜生之。 | shuaiwang_balance | 语义关系不明确 |
| 14 | DTS-QIGANG-001 | 气刚者，刚而不过。 | qi_gang_nature | 条件层缺失 |
| 15 | DTS-QIROU-001 | 气柔者，柔而不弱。 | qi Rou_nature | 语义不完整 |
| 16 | QTBJ-TIAOHOU-001 | 调候用法，权衡轻重。 | tiaohou_method | 语义关系不明确 |
| 17 | YHZP-LIUHE-001 | 六合者，相合有情。 | liu_he_relation | 条件层缺失 |
| 18 | YHZP-LIUCHONG-001 | 六冲者，相冲无情。 | liu_chong_relation | 语义不完整 |
| 19 | YHZP-XINGCHONG-001 | 刑冲者，相刑相冲。 | xing_chong_relation | 条件层缺失 |
| 20 | YHZP-HECHOU-001 | 合抽者，合中有制。 | general | 语义不完整 |
| 21 | YHZP-ZHIHUA-001 | 制中有生，生中有制。 | zhi_hua_dialectic | 条件层缺失 |

---

## INSUFFICIENT条目（1条）

| # | Passage ID | Evidence Span | Audit Reason |
|---|------------|---------------|--------------|
| 1 | DTS-JUGE-001 | 格局有成有败。 | 证据不足，无法建立语义关系 |

---

## 裁决流程

```
PARTIAL/INSUFFICIENT
    ↓
人工原典裁决（四问）
    ↓
┌─────────────┬─────────────┐
│   COMPLETE  │   REJECT    │
│ 进入授权层  │ 移出资产库  │
└─────────────┴─────────────┘
```

---

**状态**: 等待GPT对22条HOLD的逐条裁决
