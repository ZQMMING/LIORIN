
## PATCH-017~019 连续推进（commit 待）

### PATCH-017 Golden Validation Layer
Golden Case Registry：60 条 cases（每 Rule 至少 rule_id/source_id/condition/counter_example/conflict_case/expected_boundary/validation_status）+ 5 条全局必测反例（旺≠强/得令≠强/有根≠强/调候≠旺衰/病药≠用神）。反例由 excluded_transition 机械派生不编造；全部 PENDING_VALIDATION。

### PATCH-018 Conflict Resolver
8 类已解决冲突：YHZP得时旺 vs DTS旺中有衰（BY_SCOPE）/PZZQ清杂 vs DTS清浊（BY_SCOPE）/SFTK病药 vs DTS病药（BY_SCOPE）/QTBJ调候 vs PZZQ格局（BY_SCOPE）/DTS通关 vs YHZP引化（BY_SCOPE）/印轻逢煞工程文本（BY_CONDITION）/十二宫定名互证（BY_CONDITION）/人元用事 schedule 差异（BY_SCOPE，VARIANT 并存）。UNRESOLVED=0。人工裁决门槛：同 scope+对象+关系直接冲突 / Golden 无法唯一确定边界。

### PATCH-019 ADMITTED_RULE Registry
60 条规则骨架（rule_id/classical_scope/input_state/condition/output/evidence_trace/golden_pass=false/status=PENDING_ENGINE_VALIDATION）。ADMITTED=0——引擎未接线前禁止任何规则 ADMITTED。

### 全链状态
Evidence → Concept Scope → State/Factor → Rule Candidate（60）→ Golden Validation（017）→ Conflict Resolver（018）→ ADMITTED_RULE（019，全 PENDING）→ Engine Execution（未开始）。
