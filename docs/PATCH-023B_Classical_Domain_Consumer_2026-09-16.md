
## PATCH-023B Classical Domain Consumer Contract（commit 待）

### 六经典消费边界（registry_schema）
PZZQ→[order/month/ten_god/structure/root_relation]禁[评分/百分比/温度分/神煞]｜DTS→[trend/support/control/drain/root/order]禁[water_many/element_score/直判强度]｜QTBJ→[seasonal/month/daymaster/climate]禁[strength/wang/qiang]（乙木戌月可看燥湿不能判乙木弱）｜SFTK→[problem/support/control/structure]禁[PZZQ_useful/DTS_strength]｜YHZP→[ten_god/element/root/season]禁[评分模型]｜SMTH→[time/luck/year]SUPPORTING 禁直接参与 strength_state。

### consumer_mode 五级
DIRECT（月令→order_state）/FACT_ONLY（神煞）/DISPLAY_ONLY/SUPPORTING（DTS中和辅助）/FORBIDDEN。

### concept_namespace
strength→[DTS.strength_relation/PZZQ.strength_condition/QTBJ.climate_condition]；旺/强/用/病/清/浊 全部按经典拆分（PZZQ清杂≠DTS清浊、SFTK病≠DTS病、PZZQ用神≠SFTK取用≠QTBJ调候用神）。

### 1983-1103 六经典消费视图（engines/common/consumer_contract.py 实跑）
六经典各读自己 allowed 状态；QTBJ 明确「strength_state/wang_state 命局存在但禁止读取」；全局禁令：水三透≠身强、乙木戌月≠乙木弱、禁跨域直判。

### 配置校验
六经典 allowed 与 forbidden 无交集（一致性通过）。

### 效果
023B 后架构具备进入 024 条件：024 的问题是「哪些经典条件组合有资格生产 strength_state」，而非「怎么算强弱」。
