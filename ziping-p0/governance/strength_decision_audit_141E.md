# PATCH-141E-A 旺衰条件可判定性审计

## 目的
盘点当前 L0 事实，哪些旺衰条件能被机器事实直接判定，哪些必须 UNKNOWN。
不实现旺衰算法。

## 当前 L0 已有事实
- day_stem / month_branch
- hidden_stems（各支藏干）
- month_hidden_stems / month_transparent
- stem_relations（各天干 vs 日干十神）
- root_facts（日干是否在各支有根）
- combination_facts（liuhe/liuchong）

## 审计表
| 旺衰条件 | L0 可否直接判 | 依据 |
|---|---|---|
| 有根 | ✅ 已由141B判 | root_facts |
| 无根 | ✅ 已由141B判 | root_facts |
| 根深 | ❌ UNKNOWN | 无root_depth事实 |
| 根浅 | ❌ UNKNOWN | 无root_depth事实 |
| 得令 | ⚠️ 缺month_supports_daymaster事实 | L0无月令生扶日主五行事实 |
| 失令 | ⚠️ 同上 | 同上 |
| 党众 | ❌ UNKNOWN | 无生扶计数事实 |
| 助寡 | ❌ UNKNOWN | 同上 |
| 无气 | ❌ UNKNOWN | qi_state未建 |
| 官杀旺 | ❌ UNKNOWN | 无官杀力量事实 |
| 食伤泄气 | ❌ UNKNOWN | 无泄秀力量事实 |
| 财多耗身 | ❌ UNKNOWN | 无财星力量事实 |
| 身强 | ❌ 禁止直接输出 | 非单条件, 是综合定性 |
| 身弱 | ❌ 禁止直接输出 | 同上 |

## 关键边界（六经旺衰原则）
- 有根 ≠ 身强；无根 ≠ 身弱
- 得令 ≠ 身强；失令 ≠ 身弱
- 不数值阈值、不加权、不五经投票
- 五经分工：YHZP基础事实/PZZQ旺≠强/DTS全局气势/QTBJ调候/SMTH组合/SFTK外围
- 神峰通考不进141E核心Resolver

## 141E-B 结论
当前 L0 能直接判的旺衰条件 = 有根/无根（已由141B完成）。
得令/失令需先建 month_supports_daymaster 事实（这本身要回到L0层，不是Condition Evaluator层）。
其余全部 UNKNOWN。

=> 141E 暂不开放新Predicate; 需先补L0事实, 而非写Evaluator。
