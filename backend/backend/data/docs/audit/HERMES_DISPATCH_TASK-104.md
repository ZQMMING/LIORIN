# 📨 HERMES-DISPATCH: TASK-104 - TD-001技术债修复

---

## 基本信息

**Task ID**: TASK-104  
**Step**: STEP 3 - 技术债修复  
**Priority**: P1 (MEDIUM)  
**Owner**: OpenCode (Implementer)  
**Auditor**: Claude (Independent)  
**Requester**: Hermes (总调度)  
**依据**: GPT裁决 b241488

---

## WHY

GPT裁决 b241488 批准Phase 9完成后，明确指示：

> "先处理TD-001。先把之前Claude指出的技术债补掉，特别是：
> - Legacy/L4检查不能长期只是占位 return True
> - Registry必须有HOLD/REJECTED → APPROVED的反向保护
> - 增加直接调用拦截测试
> 
> 这属于治理基础设施，现在修成本最低。"

**黄金路径已经站稳，必须先把治理设施升级完成，再考虑扩大量。**

---

## WHAT

修复以下3项技术债：

### TD-001: validate_no_legacy() / validate_no_l4() 升级为AST/静态扫描

**现状**:
- `production_resolver.py` 中有 `validate_no_legacy()` 和 `validate_no_l4()` 函数
- 当前实现可能是占位符或简单字符串检查
- 无法真正拦截 Legacy/L4 代码注入

**目标**:
- 使用AST抽象语法树或静态分析工具（如`ast`模块）
- 实际扫描 Judgment 输出中是否包含 Legacy/L4 字段
- 返回明确的拦截结果，而非`return True`占位

### TD-002: Registry 反向保护机制

**现状**:
- Registry 只有 APPROVED → Production 的正向路径
- 缺少 HOLD/REJECTED → 禁止 APPROVED 的反向保护

**目标**:
- 添加 `validate_registry_consistency()` 函数
- 验证 APPROVED 集合不包含 HOLD/REJECTED 的 Judgment ID
- 添加单元测试覆盖此保护

### TD-003: 直接调用拦截测试

**现状**:
- 缺少测试验证"禁止直接调用 Legacy 函数"

**目标**:
- 添加测试：调用 `evaluate_strength()` 必须抛出 `DeprecationWarning` 或 `RuntimeError`
- 添加测试：直接访问 `wang_score` 必须被拦截

---

## CURRENT STATE

**Commit基线**: b241488 (Step 9 Phase 9完成)  
**测试基线**: 1865 passed, 5 skipped, 1 xfailed  
**Golden Path**: 4条APPROVED Judgment稳定运行  
**Registry**: 4 APPROVED / 2 HOLD / 2 REJECTED

---

## CANONICAL

依据文件：
- `docs/audit/BLOCKER_REGISTRY.md` B-01~B-03
- `docs/audit/STEP9_PHASE9_REPORT.md` 第133行TD-001
- `src/tongshu/assertion/judgment_production.py` Production Resolver
- `AGENTS.md` §2 三重取证纪律

---

## SCOPE

**允许修改**:
- `src/tongshu/assertion/production_resolver.py` - 升级验证逻辑
- `tests/test_production_resolver.py` - 添加拦截测试
- `tests/test_registry_protection.py` - 新增反向保护测试
- 文档注释更新

**允许搜索**:
- grep/ast扫描 Legacy/L4 调用点
- 确认测试覆盖范围

---

## BOUNDARY

**禁止修改**:
- ❌ Golden Dataset 期望值
- ❌ Canonical Rule / DB Schema
- ❌ 五经原典 Evidence
- ❌ 测试断言语义
- ❌ 冻结区资产（见 AGENTS.md §3）
- ❌ 现有测试文件结构

---

## INPUT

```python
# 现状示例（需升级）
def validate_no_legacy(output: dict) -> bool:
    """检查输出是否包含Legacy字段"""
    # TODO: 实现AST扫描
    return True  # 占位符，实际未检查

def validate_no_l4(output: dict) -> bool:
    """检查输出是否包含L4判定"""
    # TODO: 实现静态分析
    return True  # 占位符
```

---

## OUTPUT

**必须产出**:
1. 升级后的 `validate_no_legacy()` 使用AST扫描
2. 升级后的 `validate_no_l4()` 使用关键字匹配
3. 新增 `validate_registry_consistency()` 反向保护
4. 新增测试文件 `tests/test_registry_protection.py`
5. 扩展测试文件 `tests/test_production_resolver.py`

**验收标准**:
- 所有TD-001相关测试必须PASS
- 现有1865测试不能回归（除明确标记为expected-fail）
- `evaluate_strength()` 调用必须触发警告

---

## TEST

**必须通过的测试**:

```python
# test_production_resolver.py 新增
def test_validate_no_legacy_detects_wang_score():
    """验证能检测到wang_score字段"""
    output = {"verdict": "身强", "wang_score": 2.5}
    assert not validate_no_legacy(output)

def test_validate_no_legacy_passes_clean_output():
    """验证干净输出通过"""
    output = {"verdict": "身强", "evidence": ["DTS-001"]}
    assert validate_no_legacy(output)

def test_evaluate_strength_triggers_deprecation():
    """验证调用deprecated函数触发警告"""
    with pytest.warns(DeprecationWarning):
        evaluate_strength(chart)

# test_registry_protection.py 新增
def test_registry_blocks_hold_from_approved():
    """验证HOLD不能被加入APPROVED"""
    registry = create_test_registry()
    with pytest.raises(ValueError):
        registry.approve("DTS-JUDG-002")  # HOLD状态

def test_registry_blocks_rejected_from_approved():
    """验证REJECTED不能被加入APPROVED"""
    registry = create_test_registry()
    with pytest.raises(ValueError):
        registry.approve("DTS-JUDG-003")  # REJECTED状态
```

---

## REGRESSION

**必须保护**:
- ✅ Golden Path 18/18测试继续通过
- ✅ M2资产 86/86测试继续通过
- ✅ 现有Registry字段完整性测试继续通过

**不得引入**:
- ❌ 新的FAILED测试
- ❌ 修改现有测试断言
- ❌ 破坏Production Resolver API契约

---

## ROLLBACK

**失败恢复**:
```bash
git revert HEAD  # 回退TD-001修复
git checkout b241488 -- .  # 恢复到Phase 9完成状态
```

---

**生成时间**: 2026-08-31  
**调度方**: Hermes Agent (飞书自动桥接)  
**裁决引用**: b241488
