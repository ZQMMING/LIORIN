
## PATCH-005C Strength State Rule Admission（commit 待）

### Human 整体裁决
005B PASS：Factor Evidence Registry ≠ Strength Rule ≠ Strength Judgment；005B 只完成 原文证据→Factor→Relation，未越权进入 Factor→strength_state，符合 004C 契约。

### 005C 三层治理
**① Rule Predicate 层**：rule_condition_set schema（rule_id/input_factor/relation/classical_scope/condition/output_state）；禁「得令+有根=身强」式自编组合；4 条候选规则全部 PENDING_GOLDEN：
- RULE-S-001 得时俱为旺论→wang_state=WANG（不越层 STRONG）
- RULE-S-002 失令便作衰看→shuai_state=SHUAI（衰≠弱）
- RULE-S-003 四柱无根得时为旺→wang_state=WANG
- RULE-S-004 日干无气遇劫为强→qiang_state=QIANG

**② Conflict Resolver**：冲突≠错误；禁相加/评分胜/平均权重；流程=登记冲突→经典范围匹配→UNDETERMINED 或六级。

**③ Golden Case 4 个**：G01 得令无根（禁得令=强）/ G02 失令根旺（禁失令=弱）/ G03 旺而日主关系不足（禁旺=强）/ G04 势成（禁势=强弱）。

### 输出限制
允许：strength_state+evidence_trace+factor_used+conflict_status+classical_scope。禁止：分数/权重/百分比/旺衰指数/强弱等级计算表（月令40%+根气30%+帮扶20%+克泄10% 直接 BLOCK——六经典无数学权重依据）。

### 产物
governance/patch_005c_strength_state_rule.json（4 Predicate + Conflict + 4 Golden + BLOCK + 6 验收）

### 下一步
PATCH-006 用神 Rule Modeling（中间不再停小 PATCH，除非：六经典直接冲突无法治理/缺原文依据/需选不同算法架构）。
