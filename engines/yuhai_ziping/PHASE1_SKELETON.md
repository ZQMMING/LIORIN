# YHZP 渊海子平 Engine · Phase 1 Skeleton（§60）

**日期**：2026-09-15 · 分支 feature/ziping · engine=YUHAI_ZIPING

## 状态：Skeleton PASS（测试 10/10）

Phase 1 只建骨架，**未写任何业务 Rule**；calculation/rule/judgment/evidence/signal/golden/regression/provenance/production 为占位空目录（.gitkeep）。

## 交付物

```
engines/yuhai_ziping/
├── __init__.py     ENGINE_ID=YUHAI_ZIPING · ENGINE_VERSION=0.1.0 · CONTRACT_VERSION=0.1.0
├── result.py       §B-3 YHZPEngineResult：ten_god/six_relative/palace/basic_structure/geju_candidates/relation_facts
├── validator.py    输入：CanonicalGate G-001~024 + 禁止重排盘；输出：§70 Schema + §B-5 禁用字段
├── calculation/    （Phase 6+）
├── rule/           （Phase 4+）
├── judgment/       （Phase 7+）
├── evidence/       （Phase 5+）
├── signal/         （L5，Phase 9 域）
├── golden/         （Phase 8+）
├── regression/     （Phase 8+）
├── provenance/     （Phase 10+）
├── production/     （Phase 10+）
└── tests/test_skeleton.py   10 tests 全 PASS
```

## Phase 1 测试（test_skeleton.py，10/10）

| 测试 | 结果 |
|---|---|
| package 身份（engine/version） | ✅ |
| 骨架目录齐全（9 个业务占位目录） | ✅ |
| EngineResult 结构（§B-3 六组 facts + 统一字段） | ✅ |
| 输入校验接受合法 Frozen Chart | ✅ |
| 输入缺 canonical_input → FAIL_CLOSED | ✅ |
| 输入 recalculated=true → FAIL_CLOSED | ✅ |
| 输出校验接受空结果 | ✅ |
| 输出非法 status → FAIL_CLOSED | ✅ |
| 输出含 global_yongshen 等禁用字段 → FAIL_CLOSED | ✅ |
| Canonical Gate 24 项全过 / 缺字段 FAIL_CLOSED（Phase 0 套件） | ✅ |

## 契约锚点（§B-2/§B-5，Phase 2 落 contract.json）

- 输入：L0 core facts（pillars/hidden_stems/shishen/wuxing/yinyang/nayin/xunkong/changsheng/relations）+ L1 Knowledge Registry
- 禁止读取：L2B~L3（§K-1）
- 禁止输出：global_strength / global_yongshen / modern_signal / modern_conclusion / llm_judgment / cross_classic_priority

## 下一阶段（等待 Human Architect）

Phase 2：生成 `engines/yuhai_ziping/contract.json`（§K-11，Human-approved Contract 为依据），验收自动验证 contract.json matches approved Contract。
