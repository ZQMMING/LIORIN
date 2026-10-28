
## PATCH-027 Climate Production Contract（commit 待）

### 调候生产者冻结
climate_state：QTBJ.climate（DIRECT，穷通宝鉴十干逐月寒暖燥湿主体系）+ DTS.climate（SUPPORTING，寒温湿燥论 DTS-026 系 B1 原注仅辅助）。

### 调候输入五域
month_order / daymaster / seasonal_state / temperature_condition / dryness_wetness；禁 strength/wang/shuai/qiang/pattern/use_god_state。

### 禁止路径
climate→strength（寒暖≠旺衰）；climate→pattern；climate_use→use_god（调候用≠格局用）；climate_use→qu_yong（调候用≠病药取用）；climate→climate_use 自动。

### 概念边界
寒暖≠旺衰；燥湿≠强弱；调候用≠格局用。

### 输出 schema
state/value/producer/sources/evidence_chain/namespace_source + climate_type/season_source/temperature_source。

### 1983-1103 实跑（engines/common/climate_producer.py）
climate=UNDETERMINED：QTBJ-018-001 仍 CANDIDATE_RULE 未升格→FAIL_CLOSED（可换 QTBJ-060-001/109-001 待核验）；season_source=戌月寒露后；temperature_source 无量化依据禁编阈值；水透三仅事实证据禁自动转调候结论。

### 024-027 四大生产契约收官
strength(024)/pattern(025)/use(026)/climate(027) 全部独立生产链，互相禁读强弱点。

## PATCH-027 Climate Production Contract（commit 待）

### 调候生产者冻结
climate_state：QTBJ.climate（DIRECT 主体系）+ DTS.climate（SUPPORTING，DTS-026 寒温湿燥论 B1 原注仅辅助）。

### 输入 namespace
QTBJ.climate 允许 [month_order/daymaster/seasonal_state/temperature_condition/dryness_wetness]；禁 [strength/wang/shuai/qiang/pattern/use_god]——调候输入不含强弱与格局。

### 禁止路径
climate→strength（寒暖≠旺衰）；climate→pattern（调候≠格局）；climate_use→use_god/qu_yong（调候用≠格局用/取用）；climate→climate_use（调候状态不自动产生调候用神，由 026 另行生产）。

### 概念边界
寒暖≠旺衰；燥湿≠强弱；调候用≠格局用。

### 输出 schema
state/value/producer/sources/evidence_chain/namespace_source/climate_type/season_source/temperature_source。

### 1983-1103 实跑（engines/common/climate_producer.py）
climate=UNDETERMINED（QTBJ-018-001 仍 CANDIDATE_RULE 未升格，FAIL_CLOSED）；climate_type=UNKNOWN；season_source=戌月寒露后；temperature_source 禁编数字阈值；水透三仅登记寒湿事实证据不转结论。
