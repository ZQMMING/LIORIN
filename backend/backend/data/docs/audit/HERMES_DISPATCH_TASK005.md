# 📨 HERMES-DISPATCH: TASK-005 - 旧测试迁移

---

## 基本信息

**Task ID**: TASK-005  
**Priority**: P0 (跟随STEP 3)  
**Owner**: OpenCode (Implementer)  
**Auditor**: Claude (Independent)  
**Requester**: Hermes (总调度)  
**Deadline**: 立即执行  

---

## WHY

GPT裁决66eae55批准进入TASK-005。当前23个测试失败是已知问题，需要将其从"验证Legacy Strength行为"迁移到"验证真实Canonical State/新链路"。

---

## WHAT

迁移以下测试文件：

### 必须迁移的测试（23个失败）

**高优先级**:
1. `tests/test_judgment_engine.py` - 1 failure (climate为neutral)
2. `tests/test_strength_engine_yinyang.py` - 部分failure
3. `tests/test_p2_direction_golden.py` - 部分failure

**中优先级**:
4. `tests/test_m2_asset_enhanced_*.py` - 11 failures (TenGodMapper + RootEvaluator)
5. `tests/test_m2_asset_integration_v2.py` - 7 failures (DayYearRelation)
6. `tests/test_flow_year_assertion.py` - 3 failures (FileNotFoundError)

---

## BOUNDARY

### 允许修改
- ✅ 测试文件（替换硬编码dict为真实Canonical State fixture）
- ✅ 测试预期值（从旧verdict改为新行为验证）
- ✅ 添加新测试验证Canonical链

### 禁止修改
- ❌ 生产代码逻辑（除必要的fix外）
- ❌ 恢复wang_score阈值判定
- ❌ 修改Canonical State引擎
- ❌ 修改Condition Evaluator架构

---

## CANONICAL

依据:
- GPT裁决66eae55
- Claude独立审计报告
- `docs/audit/STEP3_COMPLETION_REPORT.md`
- `docs/audit/BLOCKER_REGISTRY.md` (B-07, B-08)

---

## SCOPE

### 测试迁移策略

**策略A: 重写测试**
- 删除依赖旧verdict的断言
- 添加验证新行为的测试（如：verdict为空、返回UNRESOLVED）
- 添加验证Canonical链的测试

**策略B: 修复生产代码**
- 如果测试失败是因为生产代码bug（非设计变更）
- 修复后重新验证

**策略C: 标记为xfail**
- 对于暂时无法迁移的测试
- 明确标注原因和TODO

---

## ACCEPTANCE CRITERIA

### 必须完成
1. ✅ 23个失败测试全部处理（迁移/修复/标记）
2. ✅ 无旧wang_score阈值恢复
3. ✅ 测试验证新行为（UNRESOLVED/RESEARCH_ONLY）
4. ✅ Claude独立复审APPROVED

### 验收标准
- pytest运行：23 failures → 0 failures（或明确的xfail）
- 无`assert verdict == "身强"`类断言
- 有`assert verdict == ""`或`assert verdict == "UNRESOLVED"`类断言

---

## TEST

### 执行顺序
1. 分析每个失败测试的原因
2. 分类：依赖旧verdict vs 生产bug
3. 按策略A/B/C处理
4. 运行相关测试组验证

### 关键检查点
```bash
# 检查是否有旧verdict断言
grep -rn '"身强"\|"身弱"\|"从强"\|"从弱"' tests/ --include="*.py"

# 检查是否有wang_score阈值使用
grep -rn 'wang_score.*>=\|_WANG_SCORE_THRESHOLD' tests/ --include="*.py"

# 运行全量测试
python -m pytest tests/ -q --tb=no
```

---

## REGRESSION

### 必须保护
- ✅ CanonicalState引擎正常
- ✅ Condition Evaluator正常工作
- ✅ evaluate_strength_features返回正确中间特征
- ✅ DEPRECATED标记清晰

### 禁止引入
- ❌ 新的wang_score阈值判定
- ❌ 新的verdict输出（除了UNRESOLVED）
- ❌ 新的硬编码dict替代真实Canonical State

---

## ROLLBACK

如果某测试迁移失败:
1. 立即停止该测试组的修改
2. git revert该测试文件
3. 分析根因（是测试问题还是生产问题）
4. 重新制定策略

---

## Gatekeeper

**Auditor**: Claude (独立复审，不是Hermes下属)  
**Approver**: GPT (最终裁决)  
**Notifier**: Hermes (总调度，不宣布PASS)

---

## Notes

**重要提醒**:
1. **铁律**: 不能为了1795全绿而恢复旧Strength行为
2. **分类处理**: 每个失败测试必须分析原因，不能一刀切
3. **证据充分**: 每个测试迁移必须有明确的Canonical依据
4. **逐步验证**: 按测试组逐步迁移，不一次性全部修改

**执行顺序**:
```
1. 分析失败原因
2. 高优先级测试迁移（test_judgment_engine, test_strength_engine_yinyang）
3. Claude复审
4. 中优先级测试迁移
5. Claude复审
6. 低优先级测试迁移
7. Claude复审
8. 全量测试验证
```

---

**Dispatch Time**: 2026-08-31  
**Status**: 🟢 GPT已批准 - 立即执行