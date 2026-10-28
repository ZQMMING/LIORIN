
## PATCH-023C Conflict Namespace Registry（commit 待）

### concept_registry 落地（可执行）
strength→DTS.strength_relation(trend)/PZZQ.strength_condition(structure)/QTBJ.climate_condition(climate)；wang→DTS.wang_relation/YHZP.wang_expression/QTBJ(forbidden:wang_state)；qiang/用/病/清/浊 全按经典拆分（PZZQ清杂≠DTS清浊、SFTK病≠DTS病、PZZQ用神≠SFTK取用≠QTBJ调候用神）。

### Rule Matcher 前置校验（engines/common/namespace_registry.py）
- namespaced 输入（DTS.strength_relation）→ 反查 registry → 通过
- 裸 surface（strength/water_many/印多）→ REJECT（禁跨域串规则）
- 全局禁令：水三透=身强 REJECT；乙木戌月=乙木弱 REJECT（现象→结论未过 namespace 推理链）

### 1983-1103 namespace 解析
DTS.strength(trend) 读 support/control/drain/root/order；PZZQ.strength(structure) 读 order/month/ten_god/structure/root；QTBJ.strength(climate) 读 seasonal/month/daymaster/climate（禁 strength/wang/qiang 未消费）。

### QTBJ 修正逻辑（用户确认）
检查数据流：consumer→读取请求→namespace registry→allowed/forbidden；不检查命盘对象是否存在 strength。

### 效果
023C 完成后，024 才问「谁有资格生产 strength_state」（DTS relation+PZZQ structure+YHZP support+SMTH time context）。
