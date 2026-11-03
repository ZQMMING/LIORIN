# 📨 HERMES-DISPATCH: STEP 3 - TASK-001/002/003 P0隔离执行

---

## 基本信息

**Task ID**: STEP3-P0-ISOLATION-20260831  
**Priority**: P0 BLOCKER  
**Owner**: OpenCode (Implementer)  
**Auditor**: Claude (Independent, 复审每步)  
**Requester**: Hermes (总调度)  
**Deadline**: 立即执行  

---

## WHY

GPT裁决2e2d9bc批准启动STEP 3 P0隔离。Legacy Strength Engine仍在生产链运行，必须立即切断。

---

## WHAT

执行3个TASK，每步完成后等待Claude复审：

### TASK-001: 切断所有Production/Admin/Shadow Legacy调用

**目标文件**:
- `src/tongshu/api/app.py:589-590` (admin路由)
- `src/tongshu/legacy/assertion_v1/engine_adapters.py:42` (shadow链路)
- `src/tongshu/legacy/assertion_v1/environmental_fit.py:294`
- `src/tongshu/legacy/assertion_v1/systems.py:651`
- `src/tongshu/reasoning/event_topic.py:445`
- `src/tongshu/reasoning/health_signals.py:99`

**操作**:
1. 移除admin路由或添加feature flag
2. legacy/assertion_v1添加DEPRECATED标记
3. 移除evaluate_strength调用
4. 改为返回UNRESOLVED或TODO注释

**验收**: grep确认0个生产调用

---

### TASK-002: 明确LEGACY/RESEARCH_ONLY

**目标文件**:
- `src/tongshu/engines/strength_engine.py` (头部docstring)
- 所有调用点添加明确注释

**操作**:
1. 修改docstring为`LEGACY / RESEARCH ONLY - NOT FOR PRODUCTION VERDICT`
2. 添加`# WARNING: This engine must not be used for production judgment`
3. 所有export函数添加DEPRECATED装饰器或注释

**验收**: 代码审查确认LEGACY标注清晰

---

### TASK-003: 移除wang_score→身强/身弱授权

**目标文件**:
- `src/tongshu/engines/strength_engine.py:75,396-397`

**操作**:
1. 删除`_WANG_SCORE_THRESHOLD = 2.0`
2. 删除`strong = wang_score >= _WANG_SCORE_THRESHOLD`
3. 删除`verdict = "身强" if strong else "身弱"`
4. 保留calculate逻辑作为RESEARCH参考
5. 修改return类型为D1FeatureResult（无verdict字段）

**验收**: strength_engine.py不再输出verdict字段

---

## CURRENT STATE

```
Commit基线: aa35031 (STEP 0冻结)
Tag: STEP0-FREEZE-20260831-054019
Pytest baseline: 1795 tests, 23 failed
P0 BLOCKER: 8项 (双轨系统、wang_score阈值、23测试失败)
GPT裁决: 2e2d9bc (批准STEP 3)
```

---

## CANONICAL

依据:
- GPT裁决2e2d9bc
- Claude独立审计五件套
- `docs/audit/GPT_RULING_STEP02.md`
- `docs/audit/BLOCKER_REGISTRY.md` (B-01/B-02/B-03)

---

## SCOPE

**允许修改**:
- src/tongshu/api/app.py (admin路由)
- src/tongshu/legacy/assertion_v1/*.py (添加DEPRECATED)
- src/tongshu/engines/strength_engine.py (移除verdict逻辑)
- src/tongshu/reasoning/*.py (移除调用)

**禁止修改**:
- ❌ 测试文件 (等待TASK完成后单独处理)
- ❌ Canonical State引擎
- ❌ Condition Evaluator架构
- ❌ 五经辨证逻辑
- ❌ DB schema
- ❌ API contract

---

## BOUNDARY

- 每完成一个TASK必须停下来等待Claude复审
- 不得同时执行多个TASK
- 不得修改测试文件
- 只切断生产调用，不删除历史代码
- 保留RESEARCH参考代码

---

## INPUT契约

```python
class TaskDeliverable:
    task_id: str              # TASK-001/002/003
    files_modified: list[str] # 修改的文件列表
    changes_summary: str      # 变更摘要
    evidence: list[str]      # 验收证据 (grep结果、代码片段)
    reviewer: str            # Claude复审人
    verdict: str             # APPROVED/REJECTED/NEEDS_REVISION
```

---

## OUTPUT契约

**每个TASK必须产出**:
1. 代码修改 (git diff)
2. 验收证据 (grep/调用图)
3. Claude复审报告 (APPROVED/REJECTED)
4. Commit message

**最终产出**:
- 3个commit (每TASK一个)
- Claude复审报告汇总
- P0隔离状态确认

---

## ACCEPTANCE CRITERIA

### TASK-001验收:
- [ ] grep确认0个生产调用strength_engine.evaluate_strength
- [ ] admin路由不再调用legacy engine_adapters
- [ ] /api/reading路径不使用strength_engine

### TASK-002验收:
- [ ] strength_engine.py头部明确标注LEGACY/RESEARCH ONLY
- [ ] 所有export函数有DEPRECATED注释
- [ ] 代码审查确认标注清晰

### TASK-003验收:
- [ ] strength_engine.py不再计算wang_score阈值
- [ ] 不再输出"身强"/"身弱"verdict
- [ ] return类型为D1FeatureResult (无verdict字段)

### 整体验收:
- [ ] 3个TASK全部完成
- [ ] 每步有Claude复审
- [ ] pytest不要求1795全绿 (允许23失败待后续处理)
- [ ] 结构验证通过 (生产链已切断)

---

## TEST

**不需要**:
- 不运行完整pytest (23失败是已知问题)
- 不修改测试文件

**需要**:
- 每个TASK完成后运行相关单元测试
- Claude复审代码质量
- 确认无回归破坏Canonical链

---

## REGRESSION

**必须保护**:
- ✅ CanonicalState引擎正常
- ✅ Condition Evaluator正常工作
- ✅ 五经辨证链路不受影响
- ✅ /api/reading基础功能正常

**禁止引入**:
- ❌ 新的wang_score引用
- ❌ 新的threshold判定
- ❌ 新的verdict输出

---

## ROLLBACK

如果某TASK失败:
1. 立即停止后续TASK
2. git revert该TASK commit
3. 通知Hermes和Claude
4. 分析根因后重新执行

---

## Gatekeeper

**Auditor**: Claude (独立复审，不是Hermes下属)  
**Approver**: GPT (最终裁决)  
**Notifier**: Hermes (总调度，不宣布PASS)

---

## Notes

**重要提醒**:
1. 每完成一个TASK必须停下来等待Claude复审
2. 不得为了测试通过而恢复旧行为
3. 23个失败测试是已知问题，等待后续处理
4. 核心目标是切断生产链，不是修复所有测试
5. Claude复审报告必须明确APPROVED/REJECTED

**执行顺序**:
```
TASK-001 → Claude复审 → TASK-002 → Claude复审 → TASK-003 → Claude复审汇总
```

---

**Dispatch Time**: 2026-08-31  
**Status**: 🚨 P0 BLOCKER - 立即执行