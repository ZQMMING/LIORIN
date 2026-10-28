
## PATCH-029 Classical Evidence Binding Layer（commit 待）

### Evidence schema 冻结
evidence_id/classic/work/chapter/quotation/translation_layer/interpretation_layer/grade 八字段。

### 四层分离
原文A=ORIGINAL/ORIGINAL_AUTHOR；注解B=ANNOTATION(B1 原注/B2 任氏)；后世整理C=LATER_COMMENTARY；现代解释D=MODERN 禁入规则层。

### Rule 必须引用 evidence_id
禁 rule→自由文本；必须 rule_id→evidence_id→classic_source。evidence 注册表 14 条（EVID-001~014）。

### A/B/C/D 分级
A=原文明确/B=原文+传统注解/C=后世整理/D=现代解释。

### 12 条 ADMITTED 绑定校验（engines/common/evidence_binding.py）
全部 evidence 存在、grade≤B 无 D；缺口=0。域锚：PZZQ.use_god/pattern=EVID-011(A)、SFTK.qu_yong=EVID-012(A)、QTBJ.climate=EVID-013(B 混合未升格 FAIL_CLOSED)、DTS.climate=EVID-014(B)。
