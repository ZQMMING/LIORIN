# XPASS清理深入分析报告

**时间**: 2026-08-31  
**状态**: ⚠️ 发现新问题

---

## 清理结果（修正版）

### 已清理
- ✅ test_p7_nfc_frontend.py: 4个xfail移除，测试通过
- ✅ test_p7c_frontend.py: 3个xfail移除，测试通过
- ⚠️ test_advice_optimizer.py: 1个xfail移除，3个测试失败
- ⚠️ test_ziping_assertion.py: 2个xfail移除，仍有2个XPASS

### 当前测试状态
```
FAILED tests/test_advice_optimizer.py::TestWeights::test_system_weight_career
FAILED tests/test_advice_optimizer.py::TestWeights::test_system_weight_marriage
FAILED tests/test_advice_optimizer.py::TestWeights::test_system_weight_health
3 failed, 1786 passed, 5 skipped, 6 xfailed, 2 xpassed
```

---

## 问题分析

### 问题1: advice_optimizer测试失败（3个）

**失败测试**:
- test_system_weight_career
- test_system_weight_marriage
- test_system_weight_health

**可能原因**:
- SYSTEM_WEIGHTS已删除（V13治理决策）
- 测试期望值与实际实现不匹配
- 需要重构测试逻辑

**建议处理**:
- 选项A: 恢复SYSTEM_WEIGHTS（不推荐，违反V13治理）
- 选项B: 重构测试，验证新的互补机制
- 选项C: 将测试标记为SKIP（明确说明原因）

### 问题2: ziping_assertion仍有2个XPASS

**XPASS测试**:
- test_audit_report_empty_no_conflicts
- test_audit_report_locates_suspect_engine

**可能原因**:
- AuditFlag功能已实现，但xfail标记未完全移除
- 需要检查是否还有其他xfail装饰器

**建议处理**:
- 检查是否有遗漏的xfail标记
- 确认功能是否真正可用

---

## 下一步行动

### 立即执行
1. 分析3个失败测试的具体错误信息
2. 决定处理策略（重构/SKIP/恢复）
3. 检查ziping_assertion是否有遗漏的xfail

### 预计完成
- 30分钟分析
- 15分钟修复

---

## 风险评估

### 高风险
- 如果恢复SYSTEM_WEIGHTS，会破坏V13治理决策
- 如果重构测试，可能引入新问题

### 中风险
- XPASS未完全清理，影响基线 cleanliness

### 建议
- 优先保持治理决策一致性（不恢复SYSTEM_WEIGHTS）
- 重构测试以适配新架构
- 彻底清理所有XPASS

---

**需要Claude复审后决定具体处理方案。**