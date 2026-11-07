
## PATCH-022B Strength State Rule 接线（commit 待）

### 022B-01 Factor 输入接线
1983-11-03 真实命局：order_state=NOT_GET_ORDER（乙木戌月失令）/root_state=HAS_ROOT（亥未通根）/support_state=印比生扶（印三透+日支乙根）→ factor_collection（GET_ORDER/ROOT/SUPPORT + evidence_trace）。只验证数据流。

### 022B-02 Rule Match（真实命局）
- CAND-SHUAI-001 触发：失令 → shuai_state=SHUAI
- CAND-WANG-001 不触发（非得时；修复 NOT_GET_ORDER 子串误触发 bug）
- CAND-QIANG-001 不触发：失令（无气）成立但天干无比劫透（遇劫不成立，日主自身不算）
- strength_state=UNDETERMINED（无 ADMITTED 综合规则，FAIL_CLOSED 正确行为，不编造综合算法）

### 6 个 Golden 边界案例（全 UNDETERMINED）
得令但无根 / 有根但失令（真实命局）/ 旺但受制 / 强杀无根 / 身旺遇印 / 旺中有衰（DTS 辅助 CONTEXT_ONLY）。禁得令→强、禁失令→弱自动、禁根→强、禁单因子触发。

### 关键发现
strength_state 六级产出需「多因素综合规则」——当前 4 条 ADMITTED 均为单态（wang/shuai/qiang），无任何规则授权 factor_collection→strength_state 映射。下一步 PATCH-022C 候选：从六部原文提取多因素综合规则（如身旺印多喜财/财多身弱等）走准入；在此之前引擎对任何命局恒 UNDETERMINED。
