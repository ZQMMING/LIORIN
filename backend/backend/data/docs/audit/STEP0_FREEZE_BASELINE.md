# STEP 0 Freeze Baseline

**时间**: 2026-08-31  
**Commit基线**: aa35031  
**Tag**: STEP0-FREEZE-20260831-054019

---

## 冻结内容

### 生产架构
- ✅ Git captured
- ✅ Dirty files accounted
- ✅ Untracked files logged

### 断言资产
- M2资产验证: 86/86 completed (100%)
- 结构性条件: TenGod✅ PowerComparison✅ Negation✅ DayYearRelation✅ Root✅
- StrengthEvaluator: 暂缓

### Legacy Strength Engine
- 生产调用路径: annual_event_evaluator.py:37, judgment_engine.py:41
- wang_score阈值: 已移除（TASK-003）
- 必须隔离，不得继续作为最终verdict依据

---

## 基线数据

| 指标 | 值 |
|------|-----|
| Dirty files | 6 |
| Untracked files | 3 |
| Pytest total | 1871 tests |
| Pytest passed | 1804 |
| Pytest failed | 22 |
| Pytest skipped | 5 |
| Pytest xfailed | 1 |
| Test duration | ~79s |

---

## 已知问题

### B-01 ~ B-03 (P0) — 已修复
- ✅ B-01: wang_score阈值已移除（strength_engine.py:78注释）
- ✅ B-02: canonical/state.py黑名单已添加wang_score
- ✅ B-03: /admin路由已添加feature flag（TONGSHU_ADMIN_ROUTER_ENABLED）

### B-06 ~ B-07 (P0) — 已确认无影响
- M2测试全部通过（86/86）
- yinyang测试使用stub模式，验证DEPRECATED标记

### B-10 ~ B-11 (P1) — 正在修正
- 本文件已更新为真实数据
- dispatch文档将在后续修正

---

## 下一步

进入STEP 1: Claude独立12域审计
