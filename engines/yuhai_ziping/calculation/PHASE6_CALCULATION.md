# YHZP Calculation / Facts Builder（Phase 6 · V2.22 §65/§B-3/§B-5）

**日期**：2026-09-15 · 分支 feature/ziping · engine=YUHAI_ZIPING

## 状态：Phase 6 PASS（引擎 42/42，全量 65/65）

## 交付物

```
engines/yuhai_ziping/calculation/
├── __init__.py
├── l0_adapter.py      L0 Chart → 基础 rules view + 求值上下文生成
├── facts_builder.py   Rule Engine → 六组 facts → evidence attach → YHZPEngineResult
└── tests/test_facts_builder.py   7 tests
```

## 架构

```
L0 Chart（§B-2）
  → l0_adapter.build_base_view()   只映射不计算（禁重排盘）
  → build_contexts()               5 类求值上下文：
      day_pillar / ten_god（日干 vs 各干+藏干）/ branch_pair（支对）/
      branch_single（单支）/ year|month|hour_pillar
  → RuleEngine.run(ctx)            每条规则对每个上下文求值
  → 阶段 B：十神派生回填            ten_god 值注入 → liu_qin 等依赖规则
  → 按 output 字段分六组（§B-3）    ten_god/six_relative/palace/basic_structure/geju_candidates/relation
  → EvidenceRegistry.attach()       §64 证据链
  → YHZPEngineResult（§70）
```

## 验收

- 六组 facts 结构齐全（§B-3），实测样例：ten_god 21 / palace 28 / basic_structure 273 / relation 19
- 十神派生回填：甲日干命盘 → 偏财→父、食神→子(男)、伤官→女 六亲链触发 ✅
- 每个 fact 带 rule_id + source_ids + evidence_ids + evidence_grade（§64 链完整）✅
- 输出过 §70 Schema + §B-5 禁用字段扫描（global_yongshen 等 0 命中）✅
- 缺 canonical_input → FAIL_CLOSED ✅
- 5 Validators + 全量 65 tests PASS ✅

## 边界声明

- 只消费 L0 字段，**不重排盘、不计算命盘**（§3.4）
- 不复制其他 Engine 判断代码（§65 禁止项）✅
- 规则字段覆盖度受知识工程提取范围限制（如十神规则仅覆盖甲/乙日干），属于数据侧候选覆盖，引擎侧不臆造
- geju_candidates 预留空组（YHZP 规则暂无直接格局输出；格局主域在 PZZQ）
