
## PATCH-026 Use-God Production Contract（commit 待）

### 三生产者冻结（独立 namespace）
use_god_state：PZZQ.use_god（USE_GOD，DIRECT，月令→用神 PZZQ-005-007）｜qu_yong_state：SFTK.qu_yong（QU_YONG，DIRECT，病药取用 SFTK-008-001）｜climate_use_state：QTBJ.climate_use（CLIMATE_USE，DIRECT，调候用神）。PZZQ.useful=SFTK.useful=QTBJ.tiaohou_useful 与 023C 命名等价。

### 禁止路径
strength_state→任何用神（身强弱不得决定用神）；pattern_state→use_god_state（格局成立不得自动生成用神）；用神→strength_state；三种用互不合并。

### 输入 namespace
PZZQ.use_god 禁 pattern/strength/wang/shuai/qiang（用神从月令入口直接生产，先于格局）；SFTK.qu_yong 禁 PZZQ_useful/DTS_strength/strength；QTBJ.climate_use 禁 strength/wang/qiang/pattern。

### 输出 schema
state/use_type/value/producer/sources/evidence_chain/namespace_source——use_type 必填防 Rule Matcher 合并。

### 1983-1103 实跑（engines/common/use_god_producer.py）
三用神独立 UNDETERMINED：PZZQ 财用候选（structure 待确认）/SFTK 病药未确认/QTBJ 调候规则未准入；use_type 集合 [USE_GOD, QU_YONG, CLIMATE_USE] 无合并。
