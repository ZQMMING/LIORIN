# STEP 3 P0隔离执行进度

**时间**: 2026-08-31  
**基线**: STEP0-FREEZE-20260831-054019

---

## 执行进度

| Task | 状态 | Commit | Claude复审 |
|------|------|--------|-----------|
| TASK-001: 切断Legacy调用 | ✅ 完成 | 62e80ac | ✅ APPROVED |
| TASK-002: LEGACY/RESEARCH_ONLY标注 | ✅ 完成 | 35c9f37 | ✅ APPROVED |
| TASK-003: 移除wang_score阈值 | ⏸️ 待执行 | - | 待复审 |

---

## 已完成变更

### TASK-001产出
- `strength_engine.py`: evaluate_strength返回UNRESOLVED stub
- 所有调用点添加DEPRECATED标记
- 生产调用链已切断

### TASK-002产出
- 文件头部大段LEGACY/RESEARCH_ONLY声明
- legacy/assertion_v1/*.py统一LEGACY警示块
- 全部import点添加DEPRECATED注释
- 13个文件AST语法验证通过

---

## 测试状态

| 测试文件 | 结果 | 说明 |
|---------|------|------|
| test_new_engines.py | 15 passed | V4隔离层正常 |
| test_strength_engine.py | 5 failed | 预期（验证旧verdict） |
| test_judgment_engine.py | 1 failed | 预期（climate为neutral） |
| 其他测试 | 未运行 | 等待TASK-003完成 |

---

## 下一步

### 选项A: 继续TASK-003
- 移除wang_score阈值判定
- 确保evaluate_strength不再输出verdict
- Claude复审后提交

### 选项B: 等待GPT裁决
- 汇总TASK-001/002成果
- 请求GPT对当前状态的裁决
- 再决定是否继续TASK-003

---

**建议**: 继续TASK-003，完成后汇总STEP 3所有TASK，请求GPT裁决是否进入测试迁移阶段（TASK-005）。

**等待用户指令。**