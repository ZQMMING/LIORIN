# PATCH-207 七杀格杀混官 supported结构（SEALED）

## 原典授权
PZZQ-005-008七杀格；DTS官杀相混讨论。
"杀混官"=七杀格入口+天干见正官，纯结构存在性。

## 改动
七杀格 supported 增加"杀混官"：
- 七杀格入口 + 天干见正官（ten_god_members type=stem ten_god=正官）
- supported SATISFIED
- 正官≠七杀；只查天干

## 边界锁死
- 杀混官=supported结构，非混杂成立，非格败，state仍CANDIDATE
- DTS可混/不可混条件涉根/旺衰，后续HOLD
- 七煞逢财无制：逢财已授权，"无制"HOLD（合杀等制伏路径未授权），不定义成无食+无印
- HOLD：身强逢制、制杀成立、财党杀/财生杀、杀印相生

## G1-G6 golden + 全量回归绿
