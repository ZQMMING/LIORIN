# PATCH-160.10 结构可比较性Readiness Rule契约(160.8收窄)

## 收窄原因
SFTK-0001授权"须参看旺弱"方法论, 未给旺弱机器定义。
第一条Rule不判相对强弱, 只判"比较所需结构输入是否齐备"。

## 链路
L0(成员/根/qi_position/得令/关系)
  ↓ Structure Comparison Readiness Rule
  ↓ 日主方/目标十神方结构是否齐备可比较
  ↓ SATISFIED/UNSATISFIED/UNKNOWN
  ↓ (后续)Relative Strength Rule
  ↓ Judgment

## SATISFIED含义(硬)
仅=比较所需已授权结构输入齐备, 不是比较结果成立。
禁止: 结构完整->SAT->日主强。

## Readiness检查项
- 日主方成员可追溯(ten_god_members含日主类)
- 目标十神方成员可追溯
- 根气信息存在(root_facts/qi_position)
- 月令信息存在(month_supports_daymaster)
- 必要关系输入存在
- 缺项->UNKNOWN, 不补Fact

## 后续
旺=类聚气专/根重/得时/损益/众寡 如何组合, 回原典继续校对, 不凭工程直觉造算法。
