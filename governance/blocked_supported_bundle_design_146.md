# PATCH-146 blocked/supported Bundle 设计审计

## 现状
required 已有 bundle：全SAT→SAT / 任一UNSAT→UNSAT / 有UNKNOWN→UNKNOWN / 空→UNKNOWN。

## 三类条件语义（PZZQ）
| 桶 | 语义 | 对成格影响 |
|---|---|---|
| required | 成立必须 | 缺一不可，任一缺→不成 |
| blocked | 破坏因素 | 出现即破格 |
| supported | 辅助加强 | 有更好，无不成 |

## 设计原则
- 三类**不做加权/多数决**
- blocked 是"禁止项"，命中=破格方向
- supported 不参与 required 式硬判定，只记录

## 候选聚合规则
### blocked_bundle
- 任一 blocked 条件 SATISFIED（破坏因素成立）→ BLOCKED
- blocked 全 UNSATISFIED → CLEAR
- 有 UNKNOWN → BLOCK_UNKNOWN（不猜是否有破坏）

### supported_bundle
- 只计数/列出，不决定成格
- 不做"supported多=成"

## 格状态合成（仍不命名"成格"）
仅在 required_bundle × blocked_bundle：
- required=SAT 且 blocked=CLEAR → 只记 candidate_strong 倾向，不输出"成格"
- 任一 required UNSAT 或 blocked SAT → 不成立方向
- 有 UNKNOWN → 待判

## 冻结
- ❌ 不输出"成格/破格"布尔
- ❌ supported 不参与硬判定
- ❌ 不评分/不加权
- ✅ blocked 命中即 BLOCKED
- ✅ UNKNOWN 不降级

## 待你裁决
1. blocked_bundle 三态（BLOCKED/CLEAR/BLOCK_UNKNOWN）是否认可
2. supported 是否纯记录、不参与合成
