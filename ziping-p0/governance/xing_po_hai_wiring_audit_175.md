# PATCH-175 刑破害 Relation->Rule 接线审计与契约

## 审计结论
163 L0 已建 combination_facts.{sanxing,liupo,liuhai}，但下游 0 消费；官格三桶"刑/破/害"仅为 unknown_pending 字符串占位，名实不符。

## 原典边界
- 滴天髓："支神只以冲为重，刑与害兮动不动" —— 结构存在 ≠ 发生作用
- 三命通会："冲破有吉有凶，不可概论"
- 因此刑/破/害存在 = UNKNOWN，不得升级 BLOCKED；只有官星受冲(155)直接 BLOCKED

## 175 接线契约
| 输入 | blocked 子项输出 |
|---|---|
| 有官星受冲 | BLOCKED（155 授权） |
| 有三刑 | 刑=UNKNOWN |
| 有六破 | 破=UNKNOWN |
| 有六害 | 害=UNKNOWN |
| 三者皆无 | 刑/破/害=CLEAR |
| 信息缺失 | UNKNOWN |

bundle：官星受冲=BLOCKED；刑/破/害存在=BLOCK_UNKNOWN；不存在=CLEAR。
CLEAR 仅表示"该结构阻塞未发现"，≠ 官格没问题。

## 禁止
刑/破/害→官格破；三刑计数；位置/力量；吉凶；旺衰；新增自刑；改163 L0；全局接线到其他格。
