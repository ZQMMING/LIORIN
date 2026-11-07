# PATCH-004C Rule Input Contract（规则输入输出协议）

- 日期：2026-09-16
- 状态：FROZEN_DRAFT（只定义 Rule Layer 输入输出协议，不定义任何命理判断规则）
- 依据：Human 裁决「004B-R1 通过，启动 PATCH-004C」
- 契约文件：`governance/patch_004c_rule_input_contract.json`

## 边界

**允许定义**：Rule 可读取什么 / 不可读取什么 / 输出什么格式 / 如何绑定六经典 Scope。
**禁止**：旺衰计算、强弱公式、用神取法、格局判定、喜忌输出。

## 4C-01 Rule Input State Whitelist（8 个）

| State | 产生者 |
|---|---|
| strength_state | Rule Layer 产生后可消费 |
| wang_state | 时令状态 |
| qiang_state | 关系结构 |
| order_state | 得令关系（对象化） |
| root_state | 通根关系（对象化） |
| support_state | 生扶关系 |
| trend_state | 气势趋势 |
| seasonal_state | 调候季节（QTBJ） |

**读取条件**：state 存在 ∧ scope 匹配 ∧ execution_mode 允许。不是所有 Rule 自动读取全部 State。

## 4C-02 Evidence 禁止直接输入

- 禁止模式：`if quote.contains('旺'): strength_state='STRONG'`
- 必须链路：Classical Evidence → Concept Mapping → State/Factor → Rule
- 黑名单 4 类：classical_quote（文本不是状态）/ case_reference（命例不能反推规则）/ shen_sha_reference（神煞已排除）/ ruling_schedule（时间记录≠权重）

## 4C-03 Rule Output Contract（三层）

1. **Rule Result**：rule_id / result_type / value（仅登记枚举值）
2. **Evidence Trace**：source_id / chapter_id / text_layer / classical_scope
3. **Confidence**：VERIFIED / SUPPORTED / PENDING / UNDETERMINED（禁 score:90、禁 percentage:85%）

## 4C-04 Classical Scope Binding

```
{ rule_id, classical_scope, allowed_sources[], excluded_sources[] }
```

- 用神域：允许 PZZQ_SCOPE；禁 QTBJ 调候替代用神、DTS 通关替代用神
- 调候域：允许 QTBJ_SCOPE + DTS 寒暖湿燥辅助；禁统一旺衰公式
- 通关域：允许 DTS_SCOPE；禁 YHZP 引化=通关

## 4C-05 三条硬规则

- **RULE-18**：Rule 不得直接消费 Evidence Text
- **RULE-19**：Rule 输入必须经过 State/Factor 层
- **RULE-20**：Rule Result 必须携带 Classical Scope

## 验收（6 项）

State 白名单 / Evidence 隔离 / 输出三层 / Scope 绑定 / 禁评分输出 / 禁跨经典借补。

## 下一步

PATCH-005 旺衰/强弱 Rule Modeling（契约齐备后启动）。
