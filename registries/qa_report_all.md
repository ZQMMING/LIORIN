# 六部经典 Phase 3/4 正式化 QA 报告（V2.22 §62/§63）

**日期**：2026-09-15 · 分支 feature/ziping · 覆盖 pzzq/dts/qtbj/smth/sftk

## 正式化结果

| 引擎 | sources | rules | evidence | 断链 | operator 分布 |
|---|---|---|---|---|---|
| PZZQ 子平真诠 | 49 | 81 | 24 | 0 | emit 73 / require 8 |
| DTS 滴天髓 | 258 | 90 | 65 | 0 | emit 85 / suppress 3 / require 2 |
| QTBJ 穷通宝鉴 | 202 | 109 | 106 | 0 | require 109 |
| SMTH 三命通会 | 2,530 | 161 | 43 | 0 | emit 160 / suppress 1 |
| SFTK 神峰通考 | 2,461 | 18 | 9 | 0 | emit 18 |

## 6 项对齐执行

① evidence_grade（§78）✅ ② version=0.1.0 ✅ ③ has→exists、absent→not_exists（§46）✅
④ source_id→source_ids ✅ ⑤ operation→operator、outputs→output ✅ ⑥ evidence_requirement 保留 ✅

## 本批修复的工程问题（schema 多引擎兼容）

1. **id pattern 4 字母 → 3~4 字母**：DTS 是三字母缩写（CAND-DTS-001 / DTS-001-001 / SRC-DTS-001 等）
2. **scope 枚举 + decade**：数据实际值 natal(785)/decade(14)；V2.22 原文 scope 为 string，未锁死
3. **preconditions.conditions 允许空**：空 = 无条件恒真规则（pzzq 016「八字用神專求月令」、dts 026「八格論」）
4. **engine 标识笔误规范**（候选数据 → 正式化）：
   - `ZIPIN_ZHENQUAN` → `ZIPING_ZHENQUAN`（子平真诠）
   - `DI_TIAN_SUI` → `DITIANSUI`（滴天髓）

## 质量校验（全过）

- source_id / rule_id 唯一；无孤儿 Rule（§63）✅
- 全量通过 source/rule schema（Draft 2020-12）✅
- 五部 RuleEngine 加载编译 + Evidence 链 0 断链 ✅
- status 保留 CANDIDATE；审批不代行 ✅

## 遗留（待 Human）

- **SFTK 仅 18 条 Rule**（1,030 unformalizable 待裁定）——Phase 4 已过机械验收，但业务覆盖缺口最大
- 规则审批（去 CAND- 前缀、status=APPROVED）
- 各引擎 Calculation 字段映射（Phase 6 按引擎差异实现）
