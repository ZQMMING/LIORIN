
## PATCH-028 Rule Admission Layer（commit 待）

### 规则状态机冻结
DRAFT→CANDIDATE→ADMITTED/REJECTED；DRAFT→CANDIDATE 门槛=证据绑定完整；CANDIDATE→ADMITTED 门槛=11门槛+namespace/producer绑定+Golden；ADMITTED=资格层≠自动执行（golden_pass 未过不得进引擎）。

### 绑定 schema 七字段
rule_id/classic_source/namespace/producer/input_contract/output_state/evidence_chain。

### 禁止链
经典原文→状态 FORBIDDEN（原文命中只是 Evidence）；必须 原文→规则解析→namespace→producer→state。

### 12 条 ADMITTED 绑定登记（engines/common/rule_admission.py）
基于已裁决 governance 推导绑定（非新规则）：CAND-WANG-001/002、SHUAI-001、QIANG-001、RULE-022C-01~08 全部完整绑定，缺口=0。

### QTBJ-018-001 政策（用户点名）
保持 CANDIDATE_RULE 不先升格——先完成 028 框架再走正常准入通道，防规则先通过架构后补。

### 1983-1103 匹配演示
CAND-SHUAI-001→shuai=SHUAI；QIANG 未触发（无比劫透）；strength=UNDETERMINED（FAIL_CLOSED 正确）。
