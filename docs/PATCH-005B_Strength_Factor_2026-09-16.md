
## PATCH-005B Strength Factor Model（commit 待）

### Human 复核裁决
005A PASS（概念边界层）：未生成身强身弱结论✅ / 未建旺→强映射✅ / 未用评分百分比✅ / 旺强衰弱拆分✅ / source_level 诚实标注✅。产物=Concept Registry/Evidence Binding，非 Rule Engine/Judgment Engine。

### 四概念边界冻结
- 旺：时令/气势/结构兴盛；禁 wang→strength/strong/favorable
- 强：关系条件形成的结构性强（日干无气+遇劫=强条件之一）；禁 has_root→STRONG
- 衰：失令退气结构不足；禁 shuai→weak（衰≠弱）
- 弱：**PENDING**（六部无单源等价：弱≠失令/无根/衰），005B 前禁止冻结

### 005A 硬规则 4 条
RULE-005A-01 旺强隔离（FAIL_CLOSED）/ 02 得令隔离（GET_ORDER→order_factor 允许）/ 03 根对象隔离（必须带 object）/ 04 source 不升级（QTBJ-018-001 保持 CANDIDATE）

### 7 Factor Registry（全部 source 可回查）
| Factor | 子因子 | 禁 |
|---|---|---|
| GET_ORDER | month_order/seasonal_condition/ruling_schedule | 合并=旺；→STRONG |
| ROOT | existence/quality/relation | has_root→STRONG；root→favorable |
| SUPPORT | 印比/同类/结构 | support_count→score |
| CONTROL | 关系登记 | 量化减弱 |
| DRAIN | 关系登记 | 量化减弱 |
| TREND | 五阳从气 | trend→strength |
| SEASONAL | 当权/失令/寒暖燥湿 | ⚠️018 CANDIDATE 级 需升格或换 060/109 |

### 风险审计 5 项
得令拆三 / 根拆三 / 扶助拆三 / 泄耗只登记不量化 / 势独立

### 产物
governance/patch_005b_strength_factor_model.json（7 factors + 4 硬规则 + 5 风险审计 + 7 验收）
