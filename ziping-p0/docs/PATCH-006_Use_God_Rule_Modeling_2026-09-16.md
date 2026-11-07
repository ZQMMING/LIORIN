
## PATCH-006 用神 Rule Modeling（commit 待）

### 定位
用神非单概念，五体系独立登记禁合并：PZZQ 月令格局用神（PZZQ-005-007 专求月令，A/CORE 多域锚）/ SFTK 病药用神（SFTK-008-001 从重者论）/ QTBJ 调候用神（060/109 寒冻取丙）/ DTS 通关·真神（019-001 DTS_SCOPE_ONLY）/ 相神（PZZQ-007-004 PZZQ_ONLY）。

### 6 条 Rule Candidate（全 PENDING_GOLDEN）
RULE-Y-001 专求月令→use_god_candidate / Y-002 顺逆用（财官印食顺煞伤刃劫逆）→方向 / Y-003 病药（害神为病去之为药）→medicine_candidate / Y-004 调候→tiaohou_candidate / Y-005 通关→tong_guan_candidate（DTS域）/ Y-006 相神→xiang_shen_candidate。

### Conflict Resolver 3 类
格局vs调候（各自登记禁合并）/ SFTK病药vs DTS病药表述（禁 if DTS_bing: use_SFTK_bingyao()）/ DTS通关vs YHZP引化（禁引化=通关）。

### Golden 4 个
冬生寒局（禁调候替代格局）/ 印格透煞印轻逢煞（禁直接吉凶，须过成败救应）/ 病药与调候并存（禁跨书套用）/ 通关场景（仅 DTS 域）。

### BLOCK
单一通用用神算法 / 用神评分表 / 用神权重 / 调候替代格局 / 通关替代格局 / 病药=通用算法。

### 产物
governance/patch_006_use_god_rule_modeling.json（6 Candidate + 5 概念边界 + 3 Conflict + 4 Golden + 6 验收）
