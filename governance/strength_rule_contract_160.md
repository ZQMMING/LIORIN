# PATCH-160.1 旺衰综合Rule最小契约

## 1. Input
只消费现有L0 Fact, 禁Rule自排盘/调sxtwl/重算十神。
可用: 得令(month_supports_daymaster) / 根(root_facts) / target_root / 透干(month_transparent, any_stem) /
  十神 / 合冲关系 / 目标十神定位。
缺: 党众/全局气势/双方旺衰对比的量。

## 2. Rule
经典语义形式化。首批样例: SFTK-0001/0041/0058/0073/0076/0116(病药扶抑)。
不把"旺泄衰助"变成数学公式。

## 3. Output(不叫身强/身弱)
{
  relation_state: "",
  evidence: [], assertion_ids: [],
  direction: "", reason: "",
  provenance: "Rule->Assertion->Evidence->原文",
  status: ""
}
表达: 某十神与日主关系是否满足该经典规则。不宣布"此命身强"。

## 4. Three-state
SATISFIED / UNSATISFIED / UNKNOWN。UNKNOWN不降级。

## 5. 边界
L0 Fact -> Strength Rule -> 关系性Rule Result -> 后续Judgment。
不改157 Candidate State Machine。不重组架构。

## 160.2验证目标
SFTK病药扶抑组: 只验证现有L0够不够表达其输入。
够->进Rule实现; 不够->精确指出缺哪个原子事实; 原文是综合语义->保持UNKNOWN, 不制造Fact喂入。
