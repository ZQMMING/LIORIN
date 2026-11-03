# 📨 HERMES-DISPATCH: TASK-105 - TD-001技术债修复执行

---

## 基本信息

**Task ID**: TASK-105  
**Step**: STEP 3 - 技术债修复  
**Priority**: P1 (MEDIUM)  
**Owner**: OpenCode (Implementer)  
**Auditor**: Claude (Independent Audit)  
**Dispatcher**: Hermes (编排与复核)  
**Created**: 2026-08-31T12:00:00+08:00  
**Status**: 🟡 DISPATCHED

---

## 背景

根据GPT裁决b241488，Phase 9 Golden Path已通过，但TD-001技术债需要优先修复：

> **TD-001: Legacy/L4检查不能长期只是占位return True**
> - Legacy/L4检查需要使用AST静态分析实现真实验证
> - Registry必须有HOLD/REJECTED → APPROVED的反向保护
> - 增加直接调用拦截测试

---

## 待修复项

### TD-001.1: validate_no_legacy回流()实现

**当前状态**: 占位符返回True

**要求**:
- 使用AST静态分析检查当前文件
- 检测对`evaluate_strength`、`infer_verdict`的调用
- 检测`wang_score`变量的赋值和使用
- 排除docstring中的字符串匹配（仅检查实际代码结构）

**验收标准**:
```python
assert producer.validate_no_legacy回流() is True  # 当前文件无legacy调用
```

---

### TD-001.2: validate_no_l4风险()实现

**当前状态**: 占位符返回True

**要求**:
- 使用AST分析检查当前文件
- 检测`evaluate_strength`、`infer_verdict`函数调用
- 检测`wang_score`、`body_strong`、`body_weak`变量赋值
- 检测这些变量的属性访问

**验收标准**:
```python
assert producer.validate_no_l4风险() is True  # 当前文件无L4风险
```

---

### TD-001.3: Registry状态变更保护

**要求**:
- 添加`prevent_unauthorized_status_change()`方法
- 阻止HOLD/PENDING状态变为APPROVED
- 阻止REJECTED状态变为APPROVED（永久保护）
- 允许相同状态的保持

**验收标准**:
```python
# HOLD → APPROVED 应该抛出异常
with pytest.raises(ValueError):
    producer.prevent_unauthorized_status_change("DTS-JUDG-002", "APPROVED_FOR_PRODUCTION")

# REJECTED → APPROVED 应该抛出异常
with pytest.raises(ValueError):
    producer.prevent_unauthorized_status_change("DTS-JUDG-003", "APPROVED_FOR_PRODUCTION")

# 相同状态应该允许
assert producer.prevent_unauthorized_status_change("DTS-JUDG-001", "APPROVED_FOR_PRODUCTION") is True
```

---

### TD-001.4: 直接调用拦截测试

**要求**:
- 在`test_judgment_production.py`中添加测试类
- 测试validate_no_legacy回流()的正确性
- 测试validate_no_l4风险()的正确性
- 测试Registry保护机制

---

## 目标文件

1. `src/tongshu/assertion/judgment_production.py`
   - 实现TD-001.1、TD-001.2、TD-001.3
   - 添加新方法
   - 不破坏现有功能

2. `tests/test_judgment_production.py`
   - 添加TD-001.4测试用例
   - 确保所有测试通过

---

## 执行约束

⚠️ **重要约束**:

1. **不得修改APPROVED Judgment逻辑**: DTS-JUDG-001, ZPZQ-JUDG-002, ZPZQ-JUDG-003, ZPZQ-JUDG-004的评估逻辑保持不变
2. **不得修改Registry数据**: judgment_registry_v2.json保持不变
3. **不得引入新的L4风险**: 不得使用旺衰判定、strength_engine调用
4. **必须保持向后兼容**: 现有测试必须继续通过

---

## 验收标准

### 功能验收
- [ ] TD-001.1: validate_no_legacy回流()使用AST分析，返回True
- [ ] TD-001.2: validate_no_l4风险()使用AST分析，返回True
- [ ] TD-001.3: prevent_unauthorized_status_change()正确阻止HOLD/REJECTED → APPROVED
- [ ] TD-001.4: 新增测试全部通过

### 回归验收
- [ ] test_judgment_production.py: 25/25 passed
- [ ] test_edition_registry.py: 全部passed
- [ ] test_production_golden_path.py: 18/18 passed
- [ ] 完整测试套件: 1865+ passed (无新失败)

### 代码审查
- [ ] Claude独立审计: PASS
- [ ] 无Legacy/L4风险
- [ ] 符合三层权威分离架构

---

## 交付物

1. 修改后的`judgment_production.py`
2. 修改后的`test_judgment_production.py`
3. 提交commit消息: `TD-001: 技术债修复 - AST静态分析验证 + Registry保护机制`
4. Push到GitHub

---

## 执行顺序

```
Hermes创建任务单 → OpenCode执行代码修改 → Claude独立审计 → Hermes核验结果 → 提交裁决
```

---

**请OpenCode按照本任务单执行TD-001技术债修复。**
