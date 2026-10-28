# PATCH-198 官格补"伤官克官"blocked结构（SEALED）

## 原典授权
PZZQ-005-008："官逢伤克刑冲，官格败也"
官格成："官逢财印，又无刑冲破害，官格成也"

## 改动
官格 blocked 增加"伤官克官"：
- 官格Candidate + 天干见伤官（ten_god_members, type=stem, ten_god=伤官）
- blocked结构 SATISFIED

## 边界锁死
- 伤官克官=blocked结构，**不是直接OFFICER_FAILED**
- state仍CANDIDATE
- 财印救应（财旺生官不作伤官见官）=后续Rule，暂UNKNOWN
- 只查天干，伤官在藏干不触发（G3）
- 不碰旺衰/吉凶/岁运

## G1-G6 golden + 全量回归绿
