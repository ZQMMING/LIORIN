# STEP6_FLOW_YEAR_AUDIT.md — flow_year 模块治理身份确认

> 审计日期: 2026-08-31
> 审计者: OpenCode (TASK-006)
> 基线: baseline-v1.4-interim-20260823

---

## 1. 模块定位

### 1.1 文件结构

```
src/tongshu/assertion/flow_year.py          ← 向后兼容 shim（3行）
src/tongshu/legacy/assertion_v1/flow_year.py ← 实际实现（~150行）
tests/test_flow_year_assertion.py           ← 专项测试
```

### 1.2 代码内容

**`src/tongshu/assertion/flow_year.py`**（shim）:
```python
# -*- coding: utf-8 -*-
"""向后兼容 shim：直接从 legacy 重导出。"""
from tongshu.legacy.assertion_v1.flow_year import FlowYearAssertionProducer  # noqa: F401
__all__ = ["FlowYearAssertionProducer"]
```

**`src/tongshu/legacy/assertion_v1/flow_year.py`**（实际实现）:
- 类: `FlowYearAssertionProducer`
- subject: `"flow_year"`
- 依赖: `EventTopicEngine`, `RuleLoader`, `HeluoScorer`, `YiScorer`, `BlindBaziEngine`, `ZiweiEngine`
- 功能: 将 EVENT_TOPIC 多流年信号 → 结构化 Assertion

### 1.3 注册状态

| 位置 | flow_year 注册状态 |
|------|-------------------|
| `assertion/__init__.py:58` | 列入 `_submodules` 导入列表（try/except 静默失败） |
| `assertion/__init__.py:81` | `"flow_year": "tongshu.legacy.assertion_v1.flow_year"` 映射存在 |
| `AssertionEngine.subjects()` | **未注册** — `test_flow_year_in_engine` 确认返回空列表 |
| `pipeline.py` | 零引用 |
| `pipeline_stages/` | 零引用 |
| `api/` / `services/` | 零引用 |

---

## 2. 治理身份判定

### 2.1 候选身份对比

| 维度 | CANONICAL | RESEARCH_ONLY | DEPRECATED |
|------|-----------|---------------|------------|
| 生产调用方 | >0 | 0 | 0（曾>0，已移除） |
| 在 AssertionEngine 注册 | 是 | 否 | 否 |
| 测试是否验证生产行为 | 是 | 否 | 验证已弃用状态 |
| 迁移方向明确 | N/A | N/A | ✅ 有（CanonicalState + FiveClassics Corpus） |
| 当前可用性 | 完整 | 可用 | 可用但预期失效 |

### 2.2 判定证据

1. **零生产调用方**: 三重取证确认 `FlowYearAssertionProducer` 不在 pipeline 入口链上
2. **未注册**: `test_flow_year_in_engine` 断言 `flow_results == []`，确认未注册到 AssertionEngine
3. **测试验证弃用**: `test_flow_year_produces_timing_window` 验证 `FileNotFoundError`（缺少 rule.schema.json）
4. **迁移方向明确**: assertion 层文档明确指向 CanonicalState + FiveClassics Corpus Primitive 规则替代
5. **legacy 包裹**: 模块物理位置在 `legacy/assertion_v1/`，表明已被认定为遗留代码

### 2.3 判定结论

**治理身份: DEPRECATED**

理由:
- 曾有过生产调用（v1 assertion 架构），已迁移至新架构
- 当前以 shim 形式保留向后兼容
- 测试主动验证其弃用状态（FileNotFoundError）
- 迁移方向已在文档中明确

---

## 3. flow_year vs. event_topic 的区分

| 模块 | 状态 | 说明 |
|------|------|------|
| `reasoning/event_topic.py` | RESEARCH_ONLY | 计算流年时间变量（stem/branch/clash 等），供给规则匹配层消费 |
| `legacy/assertion_v1/flow_year.py` | DEPRECATED | 旧断言 Producer，依赖 RuleLoader + 外部 schema 文件 |
| `assertion/flow_year.py` | DEPRECATED shim | 3行转发，无实质逻辑 |

**关键区分**: `event_topic` 是数据计算层（RESEARCH_ONLY），产出 `flow_year_stem/branch` 等变量；`flow_year` Producer 是旧的断言封装层（DEPRECATED），已被新架构替代。

---

## 4. 验收确认

| 验收项 | 状态 |
|--------|------|
| flow_year 有明确治理身份 | ✅ DEPRECATED |
| 身份与零生产调用一致 | ✅ 通过 |
| 身份与测试断言一致 | ✅ 通过 |
| 未修改生产代码 | ✅ 遵守 |

---

## 5. 建议

1. **短期**: 保持 DEPRECATED 标注，现有 shim 不变
2. **中期**: 在 `AGENTS.md` 冻结清单中补充 flow_year 为 DEPRECATED 资产
3. **长期**: 待所有 legacy 引用清理后，可安全删除 `legacy/assertion_v1/flow_year.py` 及 shim
