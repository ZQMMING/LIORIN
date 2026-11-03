# P0-8 验证报告：Assertion Pipeline - 五经断言资产生产流水线（整改版）

**日期**: 2026-08-31  
**状态**: 🟢 通过（整改后）

---

## 一、问题修复

### 原问题（a15da44 🔴）

1. **cases=0 / scenarios=0 被判定为PASS**
   - 生克制化Negative Test scenarios=0，却显示passed=true
   - Golden Replay cases=0，却显示passed=true

2. **AUTHORIZED_PARTIAL进入Production**
   - 两个断言都被发布到JudgmentLibrary
   - 违反"PARTIAL只能进入Evidence层"原则

3. **raw_texts为空**
   - 声称完成五经原典流水线，但raw_texts={}
   - 没有真正加载原典Evidence

---

## 二、修复措施

### 修复1: 强制cases/scenarios > 0

```python
# NegativeTester阶段
if result['scenarios'] == 0:
    result['passed'] = False
    result['validation_error'] = 'No_negative_test_scenarios_defined'

# GoldenReplayer阶段
if result['cases'] == 0:
    result['passed'] = False
    result['validation_error'] = 'No_golden_cases_defined'
```

### 修复2: Production发布门禁

```python
# 硬规则:
# 1. 必须有有效的Negative Test (scenarios > 0)
# 2. 必须有有效的Golden Replay (cases > 0)
# 3. AUTHORIZED_PARTIAL只能进入Evidence层，不能进入Production

can_publish_to_production = (
    neg_valid and 
    golden_valid and 
    auth_level == 'AUTHORIZED_COMPLETE'
)

can_publish_to_evidence = (
    neg_valid and 
    golden_valid and
    auth_level in ['AUTHORIZED_COMPLETE', 'AUTHORIZED_PARTIAL']
)
```

### 修复3: 真实加载原典数据

```python
# 使用Windows原生路径
path_str = r'D:\today\Canonical-Mining\五部经典完整数据'

# 提取关键段落作为Evidence
for f in os.listdir(path_str):
    if f.endswith('.md'):
        # 读取原文，提取包含关键术语的段落
        key_passages = [...]
        texts[work_name] = {
            'file': full_path,
            'length': len(content),
            'passages': key_passages[:10],
            'raw_content': content[:2000]
        }
```

---

## 三、验证结果

### 原典数据加载 ✅

```
raw_texts keys: ['DTS', 'PZZQ', 'QTBJ', 'SMTH', 'YHZP']
evidence_sources: ['DTS', 'PZZQ', 'QTBJ', 'SMTH', 'YHZP']
DTS passages count: 10
```

### 断言处理结果 ✅

| 断言 | 授权等级 | Negative Test | Golden Replay | 目标层 | 状态 |
|------|---------|---------------|---------------|--------|------|
| 日犯岁君 | AUTHORIZED_PARTIAL | 4/4通过 | 4/4通过 | EVIDENCE | EVIDENCE_LAYER |
| 生克制化 | AUTHORIZED_PARTIAL | 0 scenarios | 0 cases | NONE | HELD |

### 门禁验证 ✅

- 无原典Evidence → 不能进入Production ✅
- CANDIDATE状态需要双源核验 ✅
- 负向测试未通过 → 不发布 ✅
- Golden Replay未通过 → 不发布 ✅
- 授权等级决定可发布性 ✅

---

## 四、核心原则确认

### Authorization Monotonicity

```
AUTHORIZED_COMPLETE → Production Judgment ✅
AUTHORIZED_PARTIAL → Evidence/Research Layer ✅
UNRESOLVED → HELD (不得发布) ✅
```

### Evidence Isolation

- 每个断言有独立的Evidence引用
- 原典数据真实加载，非空占位

### Validation Gate

- cases=0 → FAIL ✅
- scenarios=0 → FAIL ✅
- 任何一项未通过 → 不得发布 ✅

---

## 五、下一步建议

1. ⏸️ P0-8.1: 为生克制化补充Negative Test和Golden Replay场景
2. ⏸️ P0-9: 批量断言生产测试
3. ⏸️ 保持跨体系聚合 🔒

---

**请 GPT 裁决下一步方向**
