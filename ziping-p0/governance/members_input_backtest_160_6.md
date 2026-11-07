# PATCH-160.6 成员事实->SFTK六条输入表达回测

## 结论
ten_god_members=必要输入, 携带完整位置provenance; 但不产生旺衰结论。
SFTK六条最终旺衰仍UNKNOWN, 不强行减少UNKNOWN。

| SFTK | 要求 | 160.5后能表达 | 结论 |
|---|---|---|---|
| 0001 | 日主vs财官谁旺谁弱 | 枚举成员, 不能判旺弱 | UNKNOWN |
| 0041 | 身弱+财多/旺 | 枚举财成员, 不能判多/旺/身弱 | UNKNOWN |
| 0058 | 比劫vs身强弱 | 完整枚举比劫, 不能判强弱 | UNKNOWN |
| 0073 | 杀轻重vs身强弱 | 枚举七杀, 不能判轻重 | UNKNOWN |
| 0076 | 身旺能任 | 相关成员就位, 身旺任仍是Rule | UNKNOWN |
| 0116 | 财多+身弱 | 枚举财, 不能判多/弱 | UNKNOWN |

## Golden锁死
- 财成员多根轻 vs 财成员少根重: count不同但系统不判财旺(PZZQ-0011b干多不如根重)
- L0无strength/daymaster_strong/wealth_strong字段
- 成员带pillar+本中余气provenance
- 同count不直判旺

## 下一研究点
众寡/气势/根重如何与成员集合发生关系(Strength Rule层)。
