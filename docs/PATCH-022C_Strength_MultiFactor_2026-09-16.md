
## PATCH-022C Strength Multi-Factor Rule Extraction（commit 待）

### 8 条多因素关系候选（全 PENDING_GOLDEN，source 可回查）
- RULE-022C-01 YHZP-078-024（A）：財多生官須要身健 / 財多盜氣本身自柔——双分支关系链，禁财多→弱单因子
- RULE-022C-02 YHZP-079-022（A）：身強殺淺假殺為權——双条件缺一不可
- RULE-022C-03 YHZP-076-104/109（A）：殺旺運純身旺→官清貴 vs 七殺全彰身旺→極貧——BY_CONDITION 分支（運純/全彰），禁合并
- RULE-022C-04 YHZP-082-001（A）：七杀格喜身旺制伏、忌身弱财生无制——格内条件关系
- RULE-022C-05 DTS-017-001/002：中和（A 总纲+B1 病药展开）——多因素综合原则，DTS 域禁跨书统一
- RULE-022C-06 PZZQ-007-030（A）：傷官用財 財旺身輕→利印比 / 身旺財淺→喜財運——格内双向条件
- RULE-022C-07 PZZQ-007-028（A）：煞食均日主根輕→助身——根轻为条件之一禁单因子
- RULE-022C-08 YHZP-063-001（A）：身旺身弱=月令判断入口——语境锚禁 Boolean 化

### 禁止
印多=强/财多=弱/官杀多=弱 单因子直推；PZZQ 格局身强弱不扩展统一旺衰算法；跨书合并。

### 冲突
2 类（杀旺身旺两分支 BY_CONDITION / DTS 中和 vs PZZQ 格内身强弱 BY_SCOPE）。

### 状态
全部 PENDING_GOLDEN；strength_state 产出仍需这些多因素规则准入+引擎接线（022D 候选）。
