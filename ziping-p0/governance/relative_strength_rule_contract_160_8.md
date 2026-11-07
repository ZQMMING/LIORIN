# PATCH-160.8 第一条Strength Rule契约: 日主↔目标十神相对强弱

不叫身强身弱Rule。输出相对强弱关系三态。

## Input(只读现有L0)
ten_god_members / root_facts / month_supports_daymaster /
target_root_facts / 已授权合冲结构。

## 试点: SFTK-0001
"财官太旺日主太弱不能任, 须财官与日主参看旺弱"
拆成: 日主 vs 财官, 谁相对强谁相对弱。

## Output
{
  relation_state: SATISFIED/UNSATISFIED/UNKNOWN,
  subject: 日主,
  target: 某十神,
  direction: 相对强/相对弱(相对target),
  evidence: [], assertion_ids: [],
  provenance: Rule->Assertion->Evidence->原文,
  reason: "", status: ""
}

## 禁止
- 财成员多+日主成员少=财旺身弱
- 强=多少/弱=多少(无数值阈值)
- count->旺
- 直出身强/身弱/财旺布尔
- 改157-159

## 验收
UNKNOWN不降级; provenance完整; 六条仍按原文关系拆, 不压成布尔。
