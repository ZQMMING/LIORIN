# 🚨 P0 BLOCKER 隔离执行方案（待GPT裁决后启动）

**时间**: 2026-08-31  
**状态**: 待裁定 → STEP 3派发

---

## 执行清单

### TASK-001: 切断/admin shadow链路

**文件**: `src/tongshu/api/app.py:589-590`  
**操作**: 移除admin路由或添加feature flag  
**验收**: `/admin`不再调用legacy engine_adapters

---

### TASK-002: 标记legacy/assertion_v1为DEPRECATED

**文件**: 
- `src/tongshu/legacy/assertion_v1/engine_adapters.py`
- `src/tongshu/legacy/assertion_v1/environmental_fit.py`
- `src/tongshu/legacy/assertion_v1/systems.py`

**操作**: 
- 添加`# DEPRECATED: Use CanonicalState + Condition Evaluator`
- 移除import strength_engine
- 改为返回UNRESOLVED或TODO

**验收**: 不再产生verdict输出

---

### TASK-003: 移除wang_score阈值判定

**文件**: `src/tongshu/engines/strength_engine.py:75,396-397`  
**操作**: 
- 删除`_WANG_SCORE_THRESHOLD = 2.0`
- 删除`strong = wang_score >= _WANG_SCORE_THRESHOLD`
- 删除`verdict = "身强" if strong else "身弱"`
- 保留calculate逻辑作为RESEARCH参考

**验收**: strength_engine.py不再输出verdict字段

---

### TASK-004: 重写P0隔离计划

**文件**: `docs/audit/P0_ISOLATION_PLAN.md`  
**操作**: 
- 基于Claude审计结果修正路径
- 明确7个调用点实际位置
- 制定分阶段隔离方案

**验收**: 计划可执行，无路径错误

---

### TASK-005: 修复23个失败测试

**文件**: 
- `tests/test_m2_asset_*.py`
- `tests/test_flow_year_assertion.py`
- `tests/test_p6c_3c2_permanent_negative.py`

**操作**: 
- 替换硬编码dict为真实Canonical State fixture
- `return True`改为`assert True`
- DayYearRelationEvaluator完善五行生克计算

**验收**: pytest 1795 tests全部通过

---

### TASK-006: 统一双轨为Canonical唯一

**文件**: `src/tongshu/pipeline.py`, `src/tongshu/pipeline_stages/*.py`  
**操作**: 
- 确认pipeline消费CanonicalState
- 确认Condition Evaluator替代strength_engine
- 验证五经辨证链路连通

**验收**: `/api/reading`路径不使用strength_engine

---

## 执行顺序

```
STEP 3: 派发TASK-001 → OpenCode实现
STEP 4: Claude复审TASK-001
STEP 5: 派发TASK-002 → OpenCode实现
STEP 6: Claude复审TASK-002
...
STEP N: 三层验证 + GPT裁决
```

---

## 风险控制

| 风险 | 缓解措施 |
|------|---------|
| 误删生产代码 | Claude复审每步 |
| 测试回归 | 保持baseline记录 |
| Legacy功能丢失 | 保留代码注释说明 |
| 双轨切换中断 | 灰度切换+feature flag |

---

**等待GPT裁决后启动STEP 3**