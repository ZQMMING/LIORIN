
## PATCH-021 Engine Execution Contract（commit 待）

### 四层契约（零算法）
1. 输入层：四柱干支/藏干/月令（用事分段 SCHEDULE_VARIANT 并存）/时间（真太阳时·节气边界）——仅登记不产状态
2. State Producer：允许 8 态（order/root/support/wang/qiang/shuai/trend/seasonal）；DIRECT_OUTPUT 仅结构态（order/root/support），RULE_REQUIRED 4 态（wang/qiang/shuai/trend/seasonal）；禁一切 state→strength_state/favorable/useful
3. Factor Collector：7 Factor（GET_ORDER/ROOT/SUPPORT/CONTROL/DRAIN/TREND/SEASONAL）；输出仅 factor_collection/evidence_trace/relation_record；禁身强身弱喜忌格局成败
4. Rule Matcher：三门槛 ADMITTED+golden_pass+Conflict PASS，缺一 FAIL_CLOSED；输出三层（Rule Result/Evidence Trace/Confidence 四态禁评分）

### 硬规则
RULE-21-01~06（输入零判断/禁三态直出/只产证据/三门槛/无 ADMITTED 恒 UNDETERMINED/置信度四态）。

### 状态
契约 FROZEN_DRAFT 零算法；Engine Execution 计算逻辑仍未启动；ADMITTED=0。下一步=PATCH-022 首批 Rule Admission（旺/强/衰/弱）。
