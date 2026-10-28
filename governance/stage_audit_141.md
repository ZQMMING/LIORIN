# 阶段审计：Condition Evaluator 层 141B~141H-D

## 已完成闭环
```
L0 Fact Builder(藏干/透干/十神/根/合冲/月令生扶)
  ↓ 原子条件 Evaluator
  ├─ 141B Root: 有根/无根可判; 根深/财有根/无气=UNKNOWN
  ├─ 141C Transparent: 财官杀印食伤透可判
  ├─ 141D Combination: 6合6冲pair精确匹配
  └─ 141H-A/B 得令: month_supports_daymaster->得令/失令
  ↓ 141F Condition Router (统一接线)
  ↓ 141G Resolver evaluate_conditions (逐项三态)
  ↓ 141H-C Bundle aggregate (全SAT/任一UNSAT/有UNK)
  ↓ 141H-D Resolver required_bundle
```

## 可判 vs UNKNOWN（当前事实边界）
| 可判 | UNKNOWN |
|---|---|
| 有根/通根/无根 | 根深/根浅 |
| 财官杀印食伤透 | 财有根/官有根/身有根(target_root) |
| 6合6冲 | 合化/刑害破穿 |
| 得令/失令 | 党众/助寡/官杀旺/食伤泄/财多耗 |
| | 身强/身弱(综合定性, 禁止直出) |

## 守住的铁律
- 三态 SATISFIED/UNSATISFIED/UNKNOWN，禁 boolean、禁评分、禁多数决
- 有根≠身强；得令≠身强；supports≠得令
- 财有根不冒充日主根；false≠身弱
- bundle SATISFIED ≠ 成格
- 神峰通考外围，不进核心 Resolver
- 全 golden 回归通过

## 待决/技术债
1. bundle 无非法状态 fail-closed 校验（非阻塞）
2. WUXING/五行生表在多文件重复，未来抽 shared registry
3. 141D 测试 case 命名小瑕疵
4. blocked/supported bundle 未做（按裁决不机械扩）

## 下一阶段待选
- 真成格条件串：选一个 PZZQ 格（如正财）把 required 真词接上 router
- 或补 L0 target_root（财有根）事实
