# YHZP Rule Engine（Phase 4 · V2.22 §63 Source→Rule→Test）

**日期**：2026-09-15 · 分支 feature/ziping · engine=YUHAI_ZIPING

## 状态：Phase 4 PASS（测试 11/11，全量 51/51）

## 交付物

```
engines/yuhai_ziping/rule/
├── __init__.py
├── rule_engine.py     纯规则解释器（消费 registries/rule/rules.yhzp.jsonl）
└── tests/test_rule_engine.py   11 tests
```

## Rule Engine 语义（全部有 V2.22 § 锚点）

| 项 | 语义 | 锚点 |
|---|---|---|
| equals | chart[field] == value | §46 |
| in | chart[field] in value（枚举列表） | §46 |
| not_in | chart[field] not in value | §46 |
| exists | 字段存在且非 None/空串 | §46 |
| not_exists | 字段不存在或为空（缺失信息语义） | §46 |
| conjunction / disjunction | AND / OR，保持一层 | §46 |
| operator=emit | 匹配 → 输出 output fact | §45 |
| 编译期校验 | 重复 rule_id / 非法算子 / 非法 operator / 无 Source 绑定 → FAIL_CLOSED | §72 |
| Fact 证据链 | rule_id + source_ids + evidence_grade（取绑定 Source 最高级） | §64/§78 |

## 验收

- 340 条规则全量加载、编译、可执行（无坏数据、无孤儿 Rule）✅
- 全算子单测（equals/in/not_in/exists/not_exists + 两种聚合 + 点路径字段）✅
- 未知算子 / 无 Source 绑定 → FAIL_CLOSED ✅
- 每个 emit fact 带 rule_id + source_ids + evidence_grade（§64 链不断）✅
- 5 Validators + 全量 51 tests PASS ✅

## 边界声明

- 本引擎只做**通用规则匹配**，不写任何业务判断逻辑（Phase 6 Calculation 消费本引擎产物）
- status 保留 CANDIDATE，审批不代行；requiring/suppress 算子 Phase 7 Judgment 启用
- evidence_requirement → Phase 5 Evidence Registry 迁移（本阶段未动）
