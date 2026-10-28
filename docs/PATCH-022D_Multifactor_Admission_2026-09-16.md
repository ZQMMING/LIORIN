
## PATCH-022D Multi-Factor Admission + Engine Wiring（commit 待）

### 8 条多因素规则全部 ADMITTED
6 CONDITIONAL_RELATION（财多生官须身健/身强杀浅/杀旺身旺两分支/七杀格喜忌/伤官财格双向/煞食均根轻）+1 PRINCIPLE_RELATION（DTS 中和）+1 CONTEXT_ANCHOR（月令入口）。019 更新：总规则 68、ADMITTED=12（4 单态+8 多因素）。

### 1983-11-03 条件评估矩阵（12 ADMITTED 全接入 engines/common/multifactor_eval.py）
- 触发：CAND-SHUAI-001（失令）✓ / RULE-022C-01（财多：地支戌未土=2）✓ / RULE-022C-05（中和原则登记）/ RULE-022C-08（月令入口锚）
- 不触发：CAND-WANG-001（非得令）/ CAND-QIANG-001（无天干比劫透）/ RULE-022C-02/03/04/06/07（官杀不透、伤官格未确认、需身强/身弱断言）
- strength_state=UNDETERMINED：身弱 PENDING（CAND-RUO-001 无单锚）+身旺未断言+六部无综合授权 → FAIL_CLOSED 正确行为

### 关键结论
12 条 ADMITTED 后引擎已可运行完整评估矩阵，但 strength_state 六级首产仍被治理正确拦截——身弱概念无单锚是核心缺口（005A Human 裁决），需未来从 PZZQ 格内身弱语境（如财旺身轻）反向建立多源身弱判定资格再议。
