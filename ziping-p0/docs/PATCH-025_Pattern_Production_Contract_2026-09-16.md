
## PATCH-025 Pattern Production Contract（commit 待）

### 格局生产者冻结
pattern_state：PZZQ.pattern（DIRECT，PZZQ-005-007 專求月令，唯一主生产者）+ DTS.pattern（SUPPORTING 八格辅助）+ SFTK.pattern（CONTEXTUAL 从化顺序，不替代 PZZQ 定义）。

### 格局输入 namespace
PZZQ.pattern 允许 [order/month/ten_god/structure/root_relation]；禁 [strength/wang/qiang/shuai_state]——格局输入不含任何强弱状态。

### 循环依赖防护（双向禁止）
- strength_state → pattern_state：身强弱不得作取格依据
- pattern_state → strength_state：格局成立不得反推身强弱
- wang/shuai/qiang → pattern_state：旺衰不入格局输入

### 输出 schema
state/value/producer/sources/evidence_chain/namespace_source/month_order_entry。

### 成败/清浊独立 namespace
PZZQ.pattern_success/failure（成/败/救应）独立；qing_zhuo 按 023C 已拆 PZZQ.qing_za/DTS.qing_zhuo——成败不与清浊合并。

### 1983-1103 实跑（engines/common/pattern_producer.py）
pattern=UNDETERMINED：月令入口=戌月戊土用事→财格候选，structure_relation 未确认待透干会支；格局输入强弱检查无违规。
