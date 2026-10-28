# PATCH-199 财格补"财逢七杀"blocked结构（SEALED）

## 原典授权
PZZQ-005-008："财透七煞，财格败也"
救应："逢煞而食神制煞以生财，或存财而合煞"

## 改动
财格 blocked 增加"财逢七杀"：
- 财格Candidate + 天干见七杀（ten_god_members, type=stem, ten_god=七杀）
- blocked结构 SATISFIED

## 边界锁死
- 财逢七杀=blocked结构，不是直接FAILED，state仍CANDIDATE
- 只查天干，七杀在藏干不触发（G3）
- 食神制杀/合杀存财=救应后续Rule，暂UNKNOWN
- 不碰旺衰/财太露/财逢劫/吉凶/岁运
- 财逢劫不做（涉"财轻比重"轻重语义，留200单独裁决）

## G1-G6 golden + 全量回归绿
