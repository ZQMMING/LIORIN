# YHZP Source/Rule 正式化 QA 报告（Phase 3 · V2.22 §62/§63）

**日期**：2026-09-15 · 分支 feature/ziping · engine=YUHAI_ZIPING

## 输入

- `D:\顺天系统资料\豆包资料\六部经典校对版\SourceRegistry重建\yhzp\sources.jsonl`（592 条）
- `...\yhzp\rules_candidate.jsonl`（340 条，status=CANDIDATE）

## 6 项对齐执行结果

| # | 对齐项 | 结果 |
|---|---|---|
| ① | source 补 evidence_grade（§78 映射） | ✅ A=353 / B=179 / C=56 / D=4 |
| ② | rule 补 version | ✅ 0.1.0（340/340） |
| ③ | 条件算子 has→exists / absent→not_exists | ✅ 数据已全部 equals(334)+in(60)，§46 白名单内，无需映射（脚本断言通过） |
| ④ | source_id(单) → source_ids(数组) | ✅ 340/340 |
| ⑤ | operation → operator；outputs → output | ✅ operator=emit 340/340；output 单对象 189 + 多输出数组 151（§45 最小结构扩展，schema 已放宽 output 为 object\|array） |
| ⑥ | evidence_requirement → Phase 5 Evidence Registry | ⏳ 字段保留（A/B/C/D），Phase 5 迁移（§39/§64） |

## 质量校验

- source_id 唯一 / rule_id 唯一 ✅
- 每条 Rule 的 source_ids 均存在于 SourceRegistry（§63 无 Source 的 Rule STOP）✅
- 无孤儿 Rule / 无嵌套 preconditions / 无 > < >= <= / 无跨经典字段 ✅
- source_text 未改动（沿用严格审计后文本，含已剥离校记/存疑注记）✅
- 全量通过 source.schema.json / rule.schema.json（Draft 2020-12）✅
- status 保留 CANDIDATE、rule_id 保留 CAND- 前缀——Human 审批不代行 ✅

## 输出

```
registries/
├── source/sources.yhzp.jsonl   592 条（正式化 + evidence_grade）
├── rule/rules.yhzp.jsonl       340 条（正式化，CANDIDATE）
└── qa_report.yhzp.md           本报告
```

## 遗留（不阻塞）

- 4 条 UNVERIFIED（evidence_grade=D）与 4 项用户存疑待裁定（2026-09-16 落实）
- 审批后去 CAND- 前缀、status=APPROVED 由 Human 执行（脚本不代行）
- 281 条 unformalizable 待 Human 分批裁定（Phase 4 前）
