
## PATCH-023 Ziping State Production Pipeline（commit 待）

### 六经典分域落地（DOMAIN_MATCH 非等级）
月令格局用神=PZZQ｜旺衰中和气势=DTS｜调候寒暖燥湿=QTBJ｜病药取用=SFTK｜十神神煞基础=YHZP｜岁运大运=SMTH（+五行精纪等须先取证）。六经典并行扫描分域落地，非先跑完一本书、非六本同写一算法。

### L0 Fact Layer
排盘输出（四柱/藏干/十神/五行分布/地支关系/大运流年）只提供输入，禁直接产身强身弱喜忌用神。

### Phase1 Boolean 白名单 6 项
has_root / has_support_relation / has_control_relation / has_drain_relation / has_month_order / has_transformation_condition——只答有没有。

### Enum 八层
order_state → root_state（对象化 root 列表）→ root_quality（STRONG/MEDIUM/WEAK/NO/UNKNOWN）→ support_state（SUPPORT_PRESENT 非 SUPPORT_STRONG）→ drain_state（泄+耗独立登记）→ control_state（制登记）→ seasonal_state（QTBJ_REQUIRED）→ trend_state（PENDING）。

### Element Relation Registry
印多/水多不得 count>=N；水=天干壬癸+地支亥子+藏干壬癸，状态 WATER_UNKNOWN，绑定 QTBJ/DTS 待审计。enum_registry v1.9.1（92 枚举：+root_quality/drain_state/control_state/element_relation_state；seasonal 加 QTBJ_REQUIRED、trend 加 PENDING）。

### 1983-11-03 Phase1 输出（state_producer.py 升级）
order=NOT_GET_ORDER / root=HAS_ROOT(亥甲、未乙)+WEAK_ROOT / support=SUPPORT_PRESENT(水透三仅年癸通根) / drain=DRAIN_PRESENT(戌丁泄+戌未戊己耗+午丁泄己耗) / control=CONTROL_PRESENT(戌辛制) / seasonal=QTBJ_REQUIRED / trend=PENDING / strength=UNDETERMINED（等待 Rule 裁决）。

### 强弱生产链（规则裁决非计算）
order+root+support+control+drain+trend+seasonal → Factor Matrix → Strength Rule → strength_state。禁 score/百分比/权重/count>=N。
