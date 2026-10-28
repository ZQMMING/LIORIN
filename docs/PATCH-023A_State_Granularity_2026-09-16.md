
## PATCH-023A State Granularity Registry（commit 待）

### L2 状态强度描述层（补上粒度规范）
L0 排盘事实 → L1 关系状态 → L2 状态强度描述 → L3 Rule 裁决 → strength_state。缺 L2 则「印多/水多/根强」争议无解。

### 四组件
1. Relation Quantity：事实数量登记非评分（visible_stem/hidden_stem/root_branch/season_relation）；禁 water_strength=80%
2. Position Weight 位置权：VISIBLE(天干透)/SEASON(月令司令)/PALACE(日支)/HIDDEN(藏干)
3. Element Relation State：VISIBLE_SUPPORT/ROOTED_SUPPORT/SEASONALLY_SUPPORTED/EXCESS_CONDITION/UNKNOWN；EXCESS_CONDITION 不自动成立只等待 Rule
4. 「多」不进入 Enum：禁 water_many/wood_many/metal_many/印多=true；改 water_fact_collection 供各 Rule 消费

### 1983-1103 L2 输出（state_producer.py 新增 L2_granularity 层）
- 水：visible_water=3（癸壬壬）/hidden_water=1（亥藏壬）/water_root=亥/month_support=false → VISIBLE_SUPPORT+ROOTED_SUPPORT（禁水旺印旺水多）
- 木：root=亥藏甲(中)+未藏乙(余) → ROOT_RELATION_PRESENT（禁木强）
- 土：branches=戌未/hidden=戌戊未己午己 → WEALTH_RELATION_PRESENT（禁财多）

### 六经典消费规则
DTS→trend/气势/中和；QTBJ→seasonal/寒暖燥湿；PZZQ→month_order/格局。禁 DTS 见水3直判水旺。

### enum_registry v1.9.2（94）
element_relation_state 细化五值；新增 position_priority/relation_quantity。
