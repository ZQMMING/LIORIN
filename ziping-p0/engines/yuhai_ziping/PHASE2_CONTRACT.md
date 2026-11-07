# YHZP 渊海子平 Engine · Phase 2 Contract（§61/§K-11）

**日期**：2026-09-15 · 分支 feature/ziping · engine=YUHAI_ZIPING

## 状态：Contract PASS（测试 11/11，全量 41/41）

## 交付物

```
engines/yuhai_ziping/
├── contract.json          Human-approved Contract（依据：V2.2.2 FINAL 附录 B + §K-1）
├── validator.py           Phase 2：以 contract.json 为单一权威来源
└── tests/test_contract.py 11 tests
```

## contract.json 契约要点（全部有 § 锚点）

| 项 | 内容 | 锚点 |
|---|---|---|
| input.allowed_fields | L0 core facts（pillars/hidden_stems/shishen/wuxing/yinyang/nayin/xunkong/changsheng/relations）+ L1 Registry 六项 | §B-2 |
| input.allowed_engines | `[]`（禁读其他引擎） | §K-1 |
| output.fact_groups | ten_god/six_relative/palace/basic_structure/geju_candidates/relation_facts | §B-3 |
| output.statuses | PASS/UNKNOWN/CLASSICAL_DIVERGENCE/FAIL/FAIL_CLOSED | §70/§M |
| forbidden_input | recalculate/rechart/sxtwl/llm/llm_judgment/score/confidence/probability/percentage/vote/consensus/charting_dependency + l2b~l3 | §3.4/§K-1/§105 |
| forbidden_output | FINAL_USE_SHEN/GLOBAL_USE_SHEN/UNIFIED_USE_SHEN/global_strength/global_yongshen/modern_signal/modern_conclusion/llm_judgment/cross_classic_priority/total_score/weighted_score/majority_vote/consensus | §B-5/§105 |
| dependency.reads | `[]`（YHZP 只读 L0+L1） | §K-1 |
| approved_by | Human Architect（V2.2.2 FINAL + 附录 B 封板） | §K-11 |

## 验收结果

- contract.json 符合 contract.schema.json（Draft 2020-12）✅
- ContractValidator.validate_contract_file(YUHAI_ZIPING) matches approved Contract ✅
- Input valid / Forbidden input rejected（sxtwl、l2b 存在即 FAIL_CLOSED；recalculated=True FAIL_CLOSED）✅
- Output valid / Forbidden output rejected（global_yongshen、未知 fact 组 → FAIL_CLOSED）✅
- validator 与 contract.json 单一来源一致（无硬编码双源漂移）✅
- 5 Validators + 全量 41 tests 全过 ✅

## 本阶段修的三处工程问题

1. contract.forbidden_input 区分布尔标志（recalculated/charting_dependency False 合法）与结构字段（sxtwl/l2b 存在即违规）
2. 3 个扫描器排除 tests 目录——测试构造违规反例是合法手段
3. 字符串级禁词表收窄为输出字段级全局禁词（FINAL_USE_SHEN 等）；sxtwl/llm 调用类禁词由标识符级检测，避免契约定义层自误报

## 下一阶段（等待 Human Architect）

Phase 3：YHZP Source 正式化——消费 `D:\顺天系统资料\豆包资料\六部经典校对版\SourceRegistry重建\yhzp\sources.jsonl`（340 条 Rule 候选），执行数据→正式 Schema 6 项对齐，写入正式 SourceRegistry。
