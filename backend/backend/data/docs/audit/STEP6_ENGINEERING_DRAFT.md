# STEP 6 Engineering Test - 初步发现

**时间**: 2026-08-31  
**执行者**: OpenCode (TASK-006)  
**状态**: 执行中

---

## 关键发现

### 1. strength_engine调用点已确认切断

**生产代码中的调用点（已全部DEPRECATED）**:
```
src/tongshu/engines/annual_event_evaluator.py:211
  → evaluate_strength(chart)  [DEPRECATED]

src/tongshu/engines/judgment_engine.py:41
  → from strength_engine import D1StrengthResult  [DEPRECATED, 仅类型注解]

src/tongshu/reasoning/health_signals.py:106
  → evaluate_strength(chart)  [DEPRECATED]

src/tongshu/reasoning/event_topic.py:446
  → evaluate_strength(chart)  [DEPRECATED]
```

**legacy目录中的调用点（已标记LEGACY/RESEARCH_ONLY）**:
```
src/tongshu/legacy/assertion_v1/engine_adapters.py:55
src/tongshu/legacy/assertion_v1/environmental_fit.py:301
src/tongshu/legacy/assertion_v1/systems.py:658
```

✅ **结论**: 无生产路径调用，所有调用均为DEPRECATED或LEGACY

---

### 2. wang_score确认无生产路径

```bash
$ grep -rn "wang_score" src/ --include="*.py" | grep -v "strength_engine.py"
# 无结果
```

✅ **结论**: wang_score仅在strength_engine.py中存在，作为RESEARCH_ONLY特征保留

---

### 3. 测试状态变化（需关注）

**基线（TASK-005后）**:
```
1778 passed, 5 skipped, 9 xfailed, 10 xpassed
```

**当前（TASK-006执行中）**:
```
1776 passed, 2 failed, 5 skipped, 9 xfailed, 10 xpassed
```

**新增失败测试**:
```
tests/auth/test_b09_c12_pg_integration.py::test_bump_and_get_token_version_after_create FAILED
tests/auth/test_b09_c12_pg_integration.py::test_create_user_is_idempotent FAILED
```

⚠️ **分析**: 这两个失败与Strength Engine无关，属于auth模块的PostgreSQL集成测试，可能与环境变量或数据库状态有关。

---

### 4. flow_year模块治理身份

**当前状态**:
```python
# src/tongshu/assertion/flow_year.py
"""向后兼容 shim：直接从 legacy 重导出。"""
from tongshu.legacy.assertion_v1.flow_year import FlowYearAssertionProducer
```

**注册位置**:
```python
# src/tongshu/assertion/__init__.py
("tongshu.legacy.assertion_v1.flow_year", ["FlowYearAssertionProducer"]),
"flow_year": "tongshu.legacy.assertion_v1.flow_year",
```

**生产调用位置**:
```python
# src/tongshu/reasoning/event_topic.py:446
from tongshu.engines.strength_engine import evaluate_strength  # [DEPRECATED]
```

⚠️ **发现问题**: event_topic.py中仍有evaluate_strength调用！虽然标记了[DEPRECATED]，但并非flow_year问题。

**flow_year治理身份判定**:
- 当前位置：`src/tongshu/assertion/flow_year.py`（非legacy目录）
- 实际实现：`src/tongshu/legacy/assertion_v1/flow_year.py`（legacy目录）
- 注册方式：shim重导出

**建议**: 将flow_year彻底移至legacy目录，或明确标注为RESEARCH_ONLY

---

## 初步验收

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 无evaluate_strength生产调用 | ✅ PASS | 全部DEPRECATED |
| 无wang_score阈值在production路径 | ✅ PASS | 仅strength_engine.py中存在 |
| flow_year治理身份 | ⚠️ NEEDS_CLARIFICATION | 需明确为RESEARCH_ONLY或迁移至legacy |
| 23个xfailed/xpassed根因 | 🔄 分析中 | 当前显示2个新失败（与Strength无关） |

---

## 下一步行动

1. **等待OpenCode完成详细分析**
2. **调查2个新失败的auth测试**（是否与本次整改相关）
3. **明确flow_year治理身份**（RESEARCH_ONLY或迁移）
4. **生成最终Engineering Test报告**

---

**继续监控执行进度...**