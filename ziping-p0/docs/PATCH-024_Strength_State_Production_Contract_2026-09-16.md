
## PATCH-024 Strength State Production Contract（commit 待）

### Producer 白名单冻结
- wang_state：YHZP.wang_expression(CAND-WANG-001 DIRECT) + DTS.wang_relation(CAND-WANG-002 SUPPORTING)
- shuai_state：YHZP.wang_expression(CAND-SHUAI-001 DIRECT)
- qiang_state：YHZP.wang_expression(CAND-QIANG-001 DIRECT)
- strength_state：综合生产（DTS.strength_relation + PZZQ.strength_condition + YHZP.support_relation + SMTH.time_modifier）——无单一经典直产，须经 024 登记资格后 Producer Layer 组合

### 输入四层
事实层(L0/L1) + 关系层(L2/L4) + 结构层(PZZQ structure_relation) + 时间修正层(SMTH time_modifier)；禁裸 surface 直判/数量评分/百分比权重。

### 输出 schema（全可追溯）
state/value/producer/sources/evidence_chain/namespace_source。任何身强身弱结论必须经 024 生产契约生成，不是某经典直接说。

### 1983-1103 Producer Layer 实跑（engines/common/strength_producer.py）
wang=UNKNOWN（无得时）/shuai=SHUAI（失令触发）/qiang=UNKNOWN（无比劫透）/strength=UNDETERMINED（综合生产条件未授权组合，FAIL_CLOSED 正确）；四状态 trace 字段验证全过。

### 注
024 编号重新定义为 Strength State Production Contract（原七层架构内容已并入 023 Pipeline）。
