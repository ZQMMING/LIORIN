# PATCH-201 印格官印双全 supported结构（SEALED）

## 原典授权
PZZQ-005-008："官印双全...印格成也"
YHZP："如带印绶，须带官星，谓之官印两全"
SMTH："喜官星，以官能生印"，官与官鬼分治

## 改动
印格 supported 增加"官印双全"：
- 印格入口 + 天干见正官（ten_god_members type=stem ten_god=正官）+ 印透
- supported SATISFIED

## 边界锁死
- 用正官，不混七杀（七杀+印=印化杀另路）
- 只查天干，藏干正官不触发（G3）
- state仍CANDIDATE，不判印格成
- blocked仍空，贪财破印保持UNKNOWN
- 不碰印轻/印重/身强弱/根气/位置/救应

## G1-G6 golden + 全量回归绿
