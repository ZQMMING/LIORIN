
# PATCH-032 Rule Construction（阶段 D 第一批）— 2026-09-16

## 状态：RULE_CONSTRUCTED

## 里程碑意义
阶段 D（规则构造）第一块砖——引擎首次对 1983-11-03 命局产出「非 UNDETERMINED」的用神判定。

## 关键纠错
**QTBJ-018-001 不是九月乙木**——018 是五月乙木（丁火司權禾稼俱旱）。九月乙木的正确 A 级源是 **QTBJ-022-001**（「九月乙木根枯葉落必賴癸水滋養……若見癸水又遇辛金發水之源定主科甲」）。此前「QTBJ-018-001 升格」路径作废，直接换源绑定。

## 证据绑定（全 A 级）
| EVID | 源 | 原文要点 |
|---|---|---|
| EVID-015 | PZZQ-005-009 | 月令所藏不一，用神遂有变化 |
| EVID-016 | PZZQ-007-006 | 辰戌丑未杂气，透干会支 |
| EVID-017 | PZZQ-007-021 | 财为我克使用之物，财喜根深 |
| EVID-018 | QTBJ-022-001 | 九月乙木必赖癸水；癸+辛发水源定主科甲；壬多水难生乙 |

## 规则
- **RULE-032-01**（PZZQ.use_god）：月令戌本气戊土=日主所克=财 → 用神=财（顺用）；戌为杂气财库，成格待 structure 确认 → use_god=CANDIDATE(财)、pattern=CANDIDATE(财格)
- **RULE-032-02**（QTBJ.climate_use）：九月乙木端用癸水；本命癸透年干+戌中辛发水源 → climate_use=DETERMINED(癸水)；壬透二登记「四柱壬多水難生乙」限制（断语层待综合）

## 1983-1103 输出升级
use_god: UNDETERMINED → **CANDIDATE(财)**
pattern: UNDETERMINED → **CANDIDATE(财格)**
climate_use: UNDETERMINED → **DETERMINED(癸水)**
qu_yong: UNDETERMINED（SFTK 病药未接线，留 033）
strength: UNDETERMINED（无授权综合，不变）

## 验证
Golden 回归全部通过（GC-001 预期已更新 FROZEN v2）；枚举测试 22/22 缺口=0。

## 产物
- governance/patch_032_rule_construction_usegod.json
- engines/common/use_god_rules.py（RULE-032-01/02）
- engines/common/golden_cases.py（GC-001 预期 v2）
- governance/patch_032_rule_construction_report.txt
