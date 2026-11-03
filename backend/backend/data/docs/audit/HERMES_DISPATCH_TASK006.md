# 📨 HERMES-DISPATCH: TASK-006 - Engineering Test

---

## 基本信息

**Task ID**: TASK-006  
**Step**: STEP 6 - 三层验证  
**Priority**: P0 (跟随GPT裁决58f1de3)  
**Owner**: OpenCode (Implementer)  
**Auditor**: Claude (Independent)  
**Requester**: Hermes (总调度)  

---

## 任务描述

执行STEP 6的第一层验证：**Engineering Test**

目标：验证代码结构完整性，确认Canonical链为唯一生产路径。

---

## 具体任务

### 1. 静态分析
```bash
# 检查strength_engine.py的所有调用点
grep -rn "evaluate_strength\|strength_engine" src/ --include="*.py"

# 检查是否有隐性调用
grep -rn "wang_score\|_WANG_SCORE_THRESHOLD" src/ --include="*.py"

# 检查flow_year模块调用
grep -rn "flow_year\|flowyear" src/ --include="*.py"
```

### 2. 调用链完整性验证
验证以下路径是否畅通：
- CanonicalState → Condition Evaluator → Judgment ✅
- Legacy Strength Engine → Production ❌ (应已切断)

### 3. xfailed/xpassed分析
```bash
# 列出所有预期失败和意外通过的测试
python -m pytest tests/ --tb=line -q | grep -E "xfailed|xpassed"
```

**要求**:
- 分析每个xfailed/xpassed的根因
- 判断是测试质量问题还是真实缺陷
- 输出分类报告

### 4. flow_year模块治理身份确认
**必须明确**flow_year属于以下三者之一：
- CANONICAL（五经原典授权）
- RESEARCH_ONLY（历史研究，不生产）
- DEPRECATED（已废弃，不应存在）

**禁止**：
- 无明确身份的遗留模块
- 被生产代码直接调用的未标记模块

---

## 交付物

1. **STATIC_ANALYSIS.md**: 调用链静态分析结果
2. **XFails_Analysis.md**: 23个xfailed/xpassed根因分析
3. **FLOW_YEAR_AUDIT.md**: flow_year模块治理身份确认
4. **ENGINEERING_TEST_REPORT.md**: 完整Engineering Test报告

---

## 验收标准

### 必须通过
- ✅ 无evaluate_strength生产调用
- ✅ 无wang_score阈值判定在production路径
- ✅ flow_year有明确治理身份（CANONICAL/RESEARCH_ONLY/DEPRECATED）
- ✅ 23个xfailed/xpassed根因明确且分类

### 禁止行为
- ❌ 恢复evaluate_strength生产调用
- ❌ 恢复wang_score阈值判定
- ❌ 让flow_year保持"灰色身份"

---

## 注意事项

1. **本TASK只涉及Engineering Test，不涉及Golden或Validation**
2. **如果发现生产路径被污染，立即STOP并汇报**
3. **不得为了通过测试而修改生产代码**
4. **所有发现必须记录在审计文档中**

---

## 时间节点

- **开始时间**: 立即
- **预计完成**: 30分钟
- **提交要求**: 完成后立即提交commit并通知Hermes
- **复审要求**: Claude独立复审后请求GPT裁决

---

**任务单创建完毕。请立即开始执行。**