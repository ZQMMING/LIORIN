
## PATCH-024 Ziping Engine State Producer Architecture（commit 待）

### 七层依赖顺序冻结（子平引擎消费排盘输出后）
①对象识别（day_master_element/ten_god_type ENUM）→②事实Boolean（has_root/has_visible_*/has_clash/has_combination 等，只表达有没有）→③基础Enum（order_state/root_state/support_state）→④关系Enum（resource/wealth/authority_relation_state）→⑤旺衰（wang_state/shuai_state）→⑥强弱（strength_state）→⑦格局/用神（后续）。

### enum_registry v1.9.0（88 枚举）
注册 14 个引擎级枚举：对象 2 + 基础 Enum 3 + 关系 Enum 4 + 旺衰 2 + 强弱 2 + PENDING 2（trend/seasonal 值域待审计）。strength_state 六级沿用 004B-R1（RELATIONAL_RESULT）。

### engines/common/state_producer.py（七层实现）
1983-11-03 癸亥壬戌乙未壬午：
- L1 WOOD / 偏印正印比肩正印
- L2 has_root=true（亥甲中/未乙余）、印透、午未合、无冲
- L3 order=NOT_GET_ORDER / root=WEAK_ROOT（中余根无本气）/ support=PRESENT（印三透仅年癸通根）
- L4 关系层全 UNDETERMINED（规则未准入，正确）
- L5 wang=UNKNOWN（无得时）/ shuai=SHUAI（失令）
- L6 strength=UNDETERMINED（无授权）
- L7 NOT_STARTED

### 修复 2 个实现 bug
①日主自身比肩不计入帮扶（022B 规则）；②wealth_structure 天干透/地支得地分开登记。

### 关键
旺在第五层、强在第六层产生；Boolean 仅事实层；关系层/强弱层未断言=正确 FAIL_CLOSED。排盘引擎独立未动。
