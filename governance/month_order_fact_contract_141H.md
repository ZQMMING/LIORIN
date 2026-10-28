# PATCH-141H Month-Order Fact 语义契约

## 三层不可等同（钉死）
| 概念 | 层级 | 能否直接等同 |
|---|---|---|
| month_supports_daymaster | L0 月令五行关系事实 | ❌ |
| 得令 / 失令 | PZZQ 语义判断 | ❌ |
| 身强 / 身弱 | 综合旺衰判断 | ❌ |

supports=true ≠ 得令 ≠ 旺 ≠ 强。

## month_supports_daymaster 精确定义
仅回答：**月令本气五行，对日主五行，是否存在"生扶/同类"基础五行关系？**
- 生扶：月令五行生日主五行（印）
- 同类：月令五行=日主五行（比劫）
- 这是纯五行生克关系事实，不是命局结论。

## 输入边界（只用已冻结 L0）
- month_qi_stem = ZHI_HIDDEN_STEMS_V1[month_branch][0]（本气=注册表首藏干，**不另建第二套十二支本气表**）
- month_qi_element = WUXING[month_qi_stem]
- daymaster_element = WUXING[day_stem]
- 不看：透干、根、合冲、全局党势。

## 判断关系
month_supports_daymaster =
  month_qi_element == daymaster_element            (同类)
  OR month_qi_element 生 daymaster_element          (生我)
输出 true/false，仅此。

## false 的语义
false = **不存在生我/同我关系**。不编码具体是克我/我克/我生（那是未来 month_relation_to_daymaster 枚举的事，本 fact 不承担）。
false ≠ 失令，false ≠ 身弱。

## 下游授权
- L0 **只**输出 month_supports_daymaster 这个布尔事实。
- L0 **不**输出"得令"。
- "得令/失令"语义由未来 PZZQ Rule/Resolver 消费此 fact 时定义。
- "身强/身弱"是综合判断，任何单 fact 都不直接推出。

## 禁止
- 禁止 L0 把此 fact 命名/注释成"得令"
- 禁止 Condition Evaluator 直接读此 fact 判身强
- 禁止加权（月令权重>其他）
