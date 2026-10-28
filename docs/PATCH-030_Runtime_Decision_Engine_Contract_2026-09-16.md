
## PATCH-030 Runtime Decision Engine Contract（commit 待）

### 执行管线冻结
排盘输入→L0 Fact→State Producer(023-027)→ADMITTED_RULE Match(028+029)→Conflict Resolver→State 输出（带 evidence trace）。

### ADMITTED_RULE 加载四门槛
binding 七字段完整 / evidence_id 存在且 grade≤B / producer 在 whitelist / golden_pass 登记（当前全 false）。加载≠执行：golden_pass=false 匹配后仅登记 match 不产出注册结论。

### Conflict Resolver
同 state 多规则命中输出不同 → scope 匹配优先；无法判定→UNDETERMINED+conflict 登记；禁评分最高/平均权重/投票/自动合并。

### 四态机制
REJECT=门槛拒绝（D级/引用不实）｜ABSTAIN=条件不完整候选不成立｜UNKNOWN=无授权综合｜UNDETERMINED=冲突/综合条件未满足。输出带 match_result/conflict/evidence_chain。

### 核心禁令（用户点名）
多规则命中→模型自行综合→未经注册结论 FORBIDDEN。Result=单规则登记输出或 UNDETERMINED/UNKNOWN。

### 1983-1103 实跑（engines/common/runtime_engine.py）
CAND-SHUAI-001 MATCHED→shuai=SHUAI（EVID-001）；WANG/QIANG ABSTAIN（条件不完整）；RULE-022C-01 ABSTAIN（财多结构未确认）；RULE-022C-05 仅 context_marker 不产 strength；无未经注册结论。
