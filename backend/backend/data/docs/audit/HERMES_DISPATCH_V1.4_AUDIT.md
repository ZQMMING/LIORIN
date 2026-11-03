# 📨 HERMES-DISPATCH: V1.4 FREEZE独立审计

---

## 基本信息

**Task ID**: V1.4-AUDIT  
**Priority**: P0 (跟随GPT最终裁决1624892)  
**Owner**: Claude (Independent Auditor)  
**Requester**: Hermes (总调度)  
**目标**: 验证V1.4 FREEZE完整性

---

## 审计范围

### 1. Legacy回流检测
- [ ] 检查所有生产代码是否仍有evaluate_strength调用
- [ ] 检查wang_score阈值是否被任何生产路径使用
- [ ] 检查shadow调用路径是否已完全切断

### 2. 测试可重现验证
- [ ] Fresh checkout后运行完整测试套件
- [ ] 验证1778 passed结果可重现
- [ ] 检查xfailed/xpassed是否稳定

### 3. V1.4 BASELINE确认
- [ ] 验证Tag V1.4-BASELINE-20260831绑定正确commit
- [ ] 确认测试基线与审计文档一致
- [ ] 检查是否有未记录的修改

### 4. 治理身份完整性
- [ ] 确认flow_year已明确为LEGACY/RESEARCH_ONLY
- [ ] 确认所有legacy模块有明确治理身份
- [ ] 确认无"灰色身份"模块

---

## 审计方法

### 静态分析
```bash
# Legacy调用检测
grep -rn "evaluate_strength\|wang_score" src/ --include="*.py" | grep -v "strength_engine.py" | grep -v "LEGACY" | grep -v "RESEARCH"

# Shadow路径检测
grep -rn "from.*strength_engine import" src/tongshu/api/ src/tongshu/services/ src/tongshu/pipeline.py --include="*.py"

# 测试可重现
python -m pytest tests/ -q --tb=no
```

### 动态验证
```bash
# API端点验证
curl -X POST http://localhost:8000/api/chart/judgment -d '{"birth_date":"..."}'

# Admin/Legacy路径验证
curl -X POST http://localhost:8000/admin/legacy/strength/evaluate
```

---

## 交付物

1. **V1.4_INDEPENDENT_AUDIT_REPORT.md**: 完整审计报告
2. **COMMIT_HASH**: 审计完成commit
3. **VERDICT**: APPROVED / APPROVED_WITH_ISSUES / REJECTED

---

## 验收标准

### 必须通过
- ✅ 无evaluate_strength生产调用
- ✅ 无wang_score阈值生产路径
- ✅ 测试可重现（1778 passed）
- ✅ flow_year治理身份明确
- ✅ 无Legacy回流

### 禁止行为
- ❌ 修改生产代码以"改善"审计结果
- ❌ 放宽测试标准
- ❌ 隐藏发现的问题

---

## 时间要求

- **开始时间**: 立即
- **预计完成**: 20分钟
- **提交要求**: 完成后立即提交commit并通知Hermes
- **后续**: Hermes整理报告后请求GPT Final Ruling

---

**任务单创建完毕。请立即开始执行。**