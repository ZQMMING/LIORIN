# XPASS清理任务单

---

## 基本信息

**Task ID**: XPASS-CLEANUP  
**Priority**: P0（进入M3 Phase 3前必须完成）  
**Owner**: OpenCode  
**Auditor**: Claude  
**Requester**: Hermes  

---

## 任务目标

清理10个XPASS，确保进入V1.4基线时无意外通过的测试。

---

## XPASS列表（待确认）

当前测试状态：
```
1778 passed, 5 skipped, 9 xfailed, 10 xpassed
```

**需要定位**: 10个XPASS的具体测试名称和原因

---

## 执行步骤

### Step 1: 定位XPASS（预计10分钟）
```bash
python -m pytest tests/ -v --tb=line --ignore=scripts/ 2>&1 | grep "XPASS"
```

**输出格式**:
```
tests/some_test.py::test_something XPASS (...)
```

### Step 2: 根因分析（预计20分钟）

对每个XPASS分类：
- **类型A**: 功能已修复，xfail标记过期 → 移除xfail标记
- **类型B**: 测试标记错误 → 修正测试
- **类型C**: 真实问题被掩盖 → 深入调查并修复

### Step 3: 执行修正（预计20分钟）
- 修改测试文件
- 运行验证
- 确认0 xpassed

### Step 4: Claude复审（预计10分钟）
- 验证修正正确性
- 确认无回归
- 输出复审报告

---

## 验收标准

### 必须满足
- ✅ 10个XPASS全部定位
- ✅ 每个XPASS根因明确
- ✅ 修正后测试通过
- ✅ 0 xpassed（或明确说明保留原因）
- ✅ Claude复审通过

### 禁止行为
- ❌ 忽略XPASS直接入库
- ❌ 批量移除xfail不分析
- ❌ 修改生产代码掩盖问题

---

## 交付物

1. **XPASS_ANALYSIS.md**: 10个XPASS根因分析
2. **修正后的测试文件**
3. **验证报告**: 0 xpassed
4. **Claude复审报告**

---

## 时间节点

- **开始时间**: 立即
- **预计完成**: 60分钟
- **提交要求**: 完成后立即提交commit
- **后续**: 启动M3 Phase 3.1

---

**任务单创建完毕。请立即开始定位XPASS。**