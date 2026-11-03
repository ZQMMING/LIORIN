# Step 9 技术债登记

**时间**: 2026-08-31  
**阶段**: Phase 8 Registry固化  
**依据**: GPT裁决 d87d562  
**状态**: 🟡 PENDING (不阻塞Phase 7关闭)

---

## 技术债清单

### 债务项1: validate_no_legacy()/validate_no_l4() 升级为AST/静态扫描

| 属性 | 值 |
|------|------|
| **优先级** | MEDIUM |
| **描述** | 当前validate_no_legacy回流()和validate_no_l4风险()为占位实现（直接返回True），依赖人工grep验证 |
| **建议方案** | 使用AST模块解析Python代码，静态扫描所有调用路径 |
| **预计工作量** | 2-3小时 |
| **触发条件** | CI门禁集成时执行 |
| **负责人** | 待分配 |
| **状态** | PENDING |

**代码位置**: `src/tongshu/assertion/judgment_production.py:288-313`

```python
def validate_no_legacy回流(self) -> bool:
    """验证无Legacy回流"""
    # 这里应该添加代码静态分析
    # 当前简化为True，表示通过验证
    return True

def validate_no_l4风险(self) -> bool:
    """验证无L4风险"""
    # 这里应该添加代码静态分析
    # 当前简化为True，表示通过验证
    return True
```

---

### 债务项2: _validate_registry() 补充反向校验

| 属性 | 值 |
|------|------|
| **优先级** | LOW |
| **描述** | 当前_validate_registry()仅正向校验APPROVED_FOR_PRODUCTION状态的judgment在APPROVED集合内，缺少反向校验 |
| **建议方案** | 增加HOLD/REJECTED状态的judgment不在APPROVED集合内的校验 |
| **预计工作量** | 30分钟 |
| **触发条件** | 下次Registry修改时执行 |
| **负责人** | 待分配 |
| **状态** | PENDING |

**代码位置**: `src/tongshu/assertion/judgment_production.py:94-110`

---

### 债务项3: 补充DTS-JUDG-004、ZPZQ-JUDG-001的直接调用拦截测试

| 属性 | 值 |
|------|------|
| **优先级** | LOW |
| **描述** | DTS-JUDG-004（PERMANENT REJECT）与ZPZQ-JUDG-001（HOLD）未通过producer.evaluate_judgment()直接调用测试 |
| **建议方案** | 补充test_dts_judg_004_raises_error与test_zpzq_judg_001_raises_error |
| **预计工作量** | 15分钟 |
| **触发条件** | 下次测试维护时执行 |
| **负责人** | 待分配 |
| **状态** | PENDING |

**测试位置**: `tests/test_judgment_semantic_validation.py`

---

## 技术债追踪矩阵

| ID | 描述 | 优先级 | 状态 | 负责人 | 截止日期 | 备注 |
|----|------|--------|------|--------|----------|------|
| TD-001 | validate_no_legacy()/validate_no_l4() 升级为AST/静态扫描 | MEDIUM | PENDING | 待分配 | 待定 | CI门禁集成时执行 |
| TD-002 | _validate_registry() 补充反向校验 | LOW | PENDING | 待分配 | 待定 | 下次Registry修改时执行 |
| TD-003 | 补充DTS-JUDG-004、ZPZQ-JUDG-001测试 | LOW | PENDING | 待分配 | 待定 | 下次测试维护时执行 |

---

## 处置原则

```
✅ 技术债记录完整，不阻塞当前发布
✅ 按优先级排序，MEDIUM优先处理
✅ 纳入后续迭代计划
✅ 定期回顾，跟踪处置进度
```

---

**技术债登记完成，等待后续迭代处置。**