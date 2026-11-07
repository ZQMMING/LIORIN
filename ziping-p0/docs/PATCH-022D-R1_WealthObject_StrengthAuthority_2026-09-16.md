
## PATCH-022D-R1 Wealth Relation Objectification + Strength Output Authority（commit 待）

### R1-01 财多对象化
RULE-022C-01 触发判定废弃 cai_dizhi_count>=2（数量模型，违反 PATCH-005），改为 wealth_relation_state：
- wealth_structure（财星结构：地支戌未土=2 得地无透/天干无财透）
- daymaster_relation（日主关系：未断言）
- drain_relation（泄耗关系：UNDETERMINED，财不干透）
- condition_limits（身健/身弱未断言，CAND-RUO-001 PENDING）
- status=UNDETERMINED（财多不作数量结论）

### R1-02 strength_state 产出权限登记
authorized_rules=[]（0 条 ADMITTED 有 output=strength_state 权限）。禁止：relationship_result/context_marker/wang/shuai/qiang/single_factor/factor_count/中和→strength_state。解锁需：多因素+scope 匹配+无单因子+Golden 全过+Admission 登记产出权限。

### 引擎（multifactor_eval.py）
1983-11-03 重跑：wealth_relation_state=UNDETERMINED（结构登记）；strength_state=UNDETERMINED（FAIL_CLOSED 正确）。

### 结论
022D-R1 修正后，「经典关系概念≠统一状态枚举」边界再次锁死；可进入 PATCH-023 格局/用神 Rule Admission（届时沿用 wealth_relation_state 同构对象化，不再出现数量判定）。
