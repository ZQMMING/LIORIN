# STEP 6 执行计划 - 三层验证

**时间**: 2026-08-31  
**依据**: GPT裁决 58f1de3  
**目标**: 验证Canonical链为唯一生产路径

---

## STEP 6 范围

### 核心验证目标
1. **Engineering Test**: 验证代码结构完整性
2. **Golden Test**: 验证原典Evidence链正确性
3. **Validation Test**: 验证端到端生产路径

### 重点检查项
- [ ] CanonicalState → Condition Evaluator → Judgment链路
- [ ] evaluate_strength是否仍有隐性生产调用
- [ ] 23个xfailed/xpassed根因分析
- [ ] flow_year模块治理身份确认（CANONICAL/RESEARCH_ONLY/DEPRECATED）
- [ ] Legacy模块是否被生产代码直接调用

---

## 执行顺序

### TASK-006: Engineering Test
验证代码结构、依赖关系、调用链完整性。

**具体任务**:
1. 静态分析：检查strength_engine.py的生产调用链
2. 依赖图：绘制Canonical链完整路径
3. xfailed/xpassed分析：定位23个问题根因
4. flow_year模块审计：确认治理身份

### TASK-007: Golden Test
验证原典Evidence链正确性。

**具体任务**:
1. 抽样验证：随机抽取5个Canonical Assertion
2. 交叉验证：对比五部经典原文定位
3. Condition Evaluator逻辑验证：TRUE/FALSE/UNRESOLVED语义正确性

### TASK-008: Validation Test
验证端到端生产路径。

**具体任务**:
1. API端点测试：/api/chart/judgment是否走Canonical链
2. Admin端点测试：/admin/legacy路径是否已禁用
3. Shadow调用检测：查找所有隐性入口
4. 集成测试：完整Chart→Evidence→Condition→Judgment流程

---

## 验收标准

### Engineering Test
- ✅ 无evaluate_strength生产调用
- ✅ 无wang_score阈值判定
- ✅ flow_year有明确治理身份
- ✅ 23个xfailed/xpassed根因明确

### Golden Test
- ✅ 抽样Assertion与原典一致
- ✅ Condition Evaluator语义正确
- ✅ 无工程阈值冒充Canonical

### Validation Test
- ✅ API返回Canonical链结果
- ✅ Admin/Shadow路径已禁用
- ✅ 端到端流程无Legacy残留

---

## 交付物

1. docs/audit/STEP6_ENGINEERING_REPORT.md
2. docs/audit/STEP6_GOLDEN_REPORT.md
3. docs/audit/STEP6_VALIDATION_REPORT.md
4. Claude独立复审报告

---

**等待OpenCode执行TASK-006...**