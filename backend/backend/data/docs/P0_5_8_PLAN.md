# P0-5.8 工作计划：统一 Replay + Trace Audit

**目标**: 验证多个 Primitive 在同一命例上独立运行，互不污染

---

## 一、背景

P0-5.6 和 P0-5.7 分别实现了：
- YHZP-LF-TSJX-5 "日犯岁君"（日干克年干）
- DTS-SZ-HZ-ZL "生克制化"（制中有生，生中有制）

现在需要验证：
- 同一命例，多个 Primitive 独立运行
- 各自授权，各自产生 Local Judgment
- Trace 不串线
- 一个 Primitive 的成立不能帮助另一个满足 Condition

---

## 二、验证设计

### 测试命例
选择包含日犯岁君关系的命例：
- 公历：2018-06-01 12:00
- 四柱：戊戌年 丁巳月 甲子日 庚午时
- 日干：甲木
- 年干：戊土
- 关系：甲木克戊土 → 日犯岁君 ✅

### 预期结果
1. **日犯岁君**：
   - 日干甲木克年干戊土 → 犯岁君 ✅
   - 独立 Judgment
   
2. **生克制化**：
   - 检查四柱关系链
   - 制中有生、生中有制 ✅
   - 独立 Judgment

### 关键验证
- 日犯岁君的成立，不能帮助生克制化满足条件
- 生克制化的成立，不能帮助日犯岁君满足条件
- 每个 Primitive 的 Trace 独立，不交叉

---

## 三、实现计划

### 1. 定义多个 Primitive
```python
PRIMITIVES = {
    "YHZP-LF-TSJX-5": {
        "name": "日犯岁君",
        "condition": "日干克年干",
        "authorization": "CLASSICAL_EXPLICIT",
        "check_func": check_fan_sui_jun,
    },
    "DTS-SZ-HZ-ZL": {
        "name": "生克制化",
        "condition": "制中有生，生中有制",
        "authorization": "CLASSICAL_EXPLICIT",
        "check_func": check_sheng_ke_hua,
    },
}
```

### 2. 独立验证每个 Primitive
```python
def run_multi_primitive_replay(chart_data):
    results = []
    for primitive_id, primitive_config in PRIMITIVES.items():
        # 独立验证，不共享状态
        result = primitive_config["check_func"](chart)
        result["primitive_id"] = primitive_id
        result["trace"] = build_trace(primitive_id, result)
        results.append(result)
    
    # 验证不污染
    validate_no_cross_pollution(results)
    
    return results
```

### 3. Trace Audit
- 每个 Primitive 有独立的 Evidence Trace
- Trace 不包含其他 Primitive 的结果
- Trace 可追溯到原典

---

## 四、关键约束

### ✅ 必须遵守
- 每个 Primitive 独立验证
- 不共享状态
- 不互相引用
- Trace 独立

### ❌ 禁止
- 一个 Primitive 的结果影响另一个
- 跨规则借用 Evidence
- 混合 Authorization

---

## 五、验证用例

### 用例 1: 日犯岁君 + 生克制化同时成立
- 命例：2018-06-01（戊戌年 丁巳月 甲子日 庚午时）
- 预期：两个 Primitive 都 PASS
- 验证：各自独立，互不影响

### 用例 2: 只有日犯岁君成立
- 需要构造或找到此类命例
- 预期：日犯岁君 PASS，生克制化 FAIL
- 验证：生克制化的 FAIL 不是因为日犯岁君的 PASS

### 用例 3: 只有生克制化成立
- 需要构造或找到此类命例
- 预期：日犯岁君 FAIL，生克制化 PASS
- 验证：日犯岁君的 FAIL 不是因为生克制化的 PASS

---

**请 GPT 裁决是否批准此计划**
