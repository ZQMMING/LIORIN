# PATCH-160 封板状态（160-A FROZEN / 160-B NOT_AUTHORIZED）

## 160-A Daymaster Power Structure
状态：ACCEPTED / FROZEN
实现：engines/common/daymaster_power_structure.py build_power_structure(pillars)
HEAD：dc9dd658

已授权可输出的结构事实：
- seasonal_axis: in_season(纯得令) / month_supports(生我)
- root_axis: root_weight_class HEAVY/LIGHT/NONE
- support_group: BIJIE/YIN (stem/root present)
- drain_group: SHISHANG/CAI
- control_group: GUANSHA (方向 GUANSHA->DAYMASTER)
- DIRECT 边关系可记；传递链边(食伤->财->官杀->印)恒 C/UNAUTHORIZED
- judgment_status 恒 NOT_AUTHORIZED

## 160-B Strength Resolver
状态：NOT_AUTHORIZED / CLOSED / 禁止建立

六部经典交叉裁决：
- PZZQ: 双轴(得时/党众)，明写得时而不旺/失时而不弱，无收敛式
- DTS: 强众敌寡/强寡敌众=气势方向(去寡/成众)，非两端力量比较器
- SFTK: 旺/弱相参体系，非公式
- YHZP: 单句条件断语，非覆盖全盘的合成算法
- QTBJ/SMTH: 不参与强弱合成

## 永久禁止
- 评分/权重/阈值/数量统计
- support_side > opposing_side -> STRONG
- 把 DTS"强众/强寡"偷换成两端力量比较器
- 从格/专旺/从化窄线 -> HOLD，属后续气势专题，不反向喂给160-B

## 边界
结构存在 ≠ 两端可比较 ≠ 身强/身弱
160-A 算准"谁扶谁克各有根"，160-B 不合成二值结论。
