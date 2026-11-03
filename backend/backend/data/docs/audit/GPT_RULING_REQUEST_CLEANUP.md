# GPT裁决请求 - V1.4基线清理问题

**请求时间**: 2026-08-31  
**请求者**: Hermes (总调度)  
**状态**: 等待裁决

---

## 问题概述

在清理XPASS过程中，发现8个测试失败（非回归，而是历史遗留问题）。

### 当前状态
```
8 failed, 1788 passed, 5 skipped, 1 xfailed
```

### 失败测试分类

#### A. test_advice_optimizer.py（3个）
**问题**: SYSTEM_WEIGHTS已删除（V13治理），但测试未更新
```
- test_system_weight_career: 期望ziwei>heluo，实际都是0.5
- test_system_weight_marriage: 期望ziwei==0.90，实际0.5
- test_system_weight_health: 期望ziping==0.85，实际0.5
```

#### B. test_ziping_assertion.py（5个）
**问题**: 测试引用不存在的API
```
- ImportError: cannot import name '_detect_conflict'
- ImportError: cannot import name '_aggregate_directions_weighted'
```

---

## 根因分析

### 这些测试的历史背景
1. **test_advice_optimizer.py**: 
   - V13治理决策删除SYSTEM_WEIGHTS
   - 测试被标记为xfail，但代码未更新
   - 移除xfail后暴露失败

2. **test_ziping_assertion.py**:
   - V13治理决策冻结AuditFlag
   - 测试被标记为xfail，但引用的函数可能已被删除或迁移
   - 移除xfail后暴露ImportError

### 是否属于"修复"范围？
- ❌ 不是P0问题（不影响生产链）
- ❌ 不是V1.4基线必须解决的问题
- ⚠️ 但是GPT要求"清理XPASS，不能带入基线"

---

## 处理选项

### 选项A: 重构测试（推荐）
- 修改test_advice_optimizer.py验证新行为（统一权重0.5）
- 检查test_ziping_assertion.py引用的函数是否已迁移
- 预计: 30分钟
- 风险: 低

### 选项B: 标记为SKIP
- 将这些测试标记为SKIP，明确说明原因
- 记录为已知问题
- 预计: 10分钟
- 风险: 中（可能掩盖问题）

### 选项C: 回滚xfail移除
- 恢复这些测试的xfail标记
- 保持8个failed状态
- 预计: 5分钟
- 风险: 高（违反GPT要求）

---

## 对M3 Phase 3的影响

### 如果选择A或B
- ✅ 可以继续启动M3 Phase 3.1
- ✅ V1.4基线相对干净
- ⚠️ 有8个测试不通过或SKIP

### 如果选择C
- ❌ 违反GPT"清理XPASS"的要求
- ❌ 无法干净进入M3 Phase 3
- ⚠️ 保留10个XPASS

---

## 建议

**建议选择选项A（重构测试）**

理由:
1. GPT明确要求"清理XPASS"
2. 这些问题是历史遗留，不是新引入的
3. 重构测试成本最低，风险最小
4. 可以干净进入M3 Phase 3

---

## 待裁决问题

1. 是否授权重构这8个测试？
2. 是否接受1788 passed + 8 failed/skipped的基线状态？
3. 是否可以启动M3 Phase 3.1？

---

**等待GPT裁决。**