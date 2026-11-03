# P0-5.9 工作计划：Local Judgment Contract 冻结

**目标**: 冻结已验证的 Local Judgment，明确定义链路与约束

---

## 一、背景

已通过验证的两个 Primitive：
1. YHZP-LF-TSJX-5 "日犯岁君"
2. DTS-SZ-HZ-ZL "生克制化"（必要条件层）

现在需要冻结它们的完整链路，形成正式 Contract。

---

## 二、Contract 定义

### 1. Evidence（证据）
- 原典原文
- 出处（经典 + 章节 + 段落）
- 解析（如有）

### 2. Canonical Feature（规范特征）
- 从 Evidence 提取的可计算事实
- 必须是确定性计算，无歧义

### 3. Primitive（原语）
- 对 Canonical Feature 的逻辑表达
- 必须绑定 Evidence

### 4. Condition（条件）
- Primitive 的判定条件
- 必须明确标注授权等级

### 5. Authorization（授权）
- CLASSICAL_EXPLICIT：原典明确授权，可进入生产链
- CLASSICAL_IMPLICIT：原典隐含，暂不授权
- ENGINEERED_THRESHOLD：工程定义，禁止生产
- SEMANTIC_ONLY：纯语义，禁止计算
- UNRESOLVED：未决，禁止判断

### 6. Local Judgment（局部判断）
- **只回答**：该经典条件/状态是否成立
- **不负责**：综合命理结论、吉凶判断、强弱评分

---

## 三、约束

### ✅ 必须遵守
1. 每个 Local Judgment 必须有完整的 Evidence → Judgment 链
2. 只能使用 CLASSICAL_EXPLICIT 授权的条件
3. 明确标注 CURRENT IMPLEMENTATION 边界
4. 不引入 strength_score 或人为阈值
5. 不进入 Composite Judgment

### ❌ 禁止
1. 不得将 Local Judgment 的结果直接作为命理结论
2. 不得将 SEMANTIC_ONLY / UNRESOLVED 包装成确定性判断
3. 不得接回 strength_engine
4. 不得引入"太过/不及"等未定义概念

---

## 四、已冻结的 Local Judgment

### 1. YHZP-LF-TSJX-5 "日犯岁君"
```
Evidence: 渊海子平·论太岁吉凶
  "且如甲日见戊年，太岁是也，剋重者死"
  
Canonical Feature:
  - day_stem: 日柱天干
  - year_stem: 年柱天干
  - day_element: 日干五行
  - year_element: 年干五行
  
Primitive: DayMasterVsYearRelation
  - DAY_KEEPS_YEAR: 日干克年干
  
Condition:
  - day_element 克 year_element
  
Authorization: CLASSICAL_EXPLICIT
  
Local Judgment:
  - 返回: True/False
  - 含义: 日犯岁君条件是否成立
  - 不返回: 吉凶判断、灾殃程度
```

### 2. DTS-SZ-HZ-ZL "生克制化"
```
Evidence: 滴天髓·通神论
  "生克制化，须制中有生，生中有制"
  
Canonical Feature:
  - elements: 四柱五行集合
  - gen_pairs: 相生关系对列表
  - keeps_pairs: 相克关系对列表
  
Primitive: WuxingRelationChecker
  - check_gen_in_keeps(): 制中有生
  - check_keeps_in_gen(): 生中有制
  
Condition:
  - 存在至少一条制中有生 或 生中有制的关系链
  
Authorization: CLASSICAL_EXPLICIT
  
Local Judgment:
  - 返回: True/False
  - 含义: 生克制化条件是否成立
  - 不返回: 中和程度、旺衰判断
```

---

## 五、实现计划

### 1. 定义 Contract 数据结构
```python
@dataclass
class LocalJudgmentContract:
    primitive_id: str
    name: str
    evidence: str
    canonical_features: list
    primitive_logic: str
    condition: str
    authorization: str
    judgment_output: str
    current_implementation: str
    unresolved_parts: list
```

### 2. 实现 Frozen Contract 验证
```python
def validate_contract(contract: LocalJudgmentContract, chart) -> dict:
    # 1. 验证 Evidence 存在
    # 2. 验证 Canonical Feature 可计算
    # 3. 验证 Primitive 逻辑正确
    # 4. 验证 Condition 判定准确
    # 5. 验证 Authorization 合法
    # 6. 验证 Local Judgment 输出格式
    pass
```

### 3. 运行验证
- 使用现有命例验证 Contract
- 确保无 strength_engine 调用
- 确保无 Composite Judgment

---

## 六、关键约束重申

1. **Local Judgment ≠ 命理结论**
   - Local Judgment 只回答"条件是否成立"
   - 命理结论需要综合多个 Local Judgment
   - 综合判断属于 Composite Judgment（已冻结）

2. **CLASSICAL_EXPLICIT ≠ 完整定义**
   - 每个 Primitive 都可能只是 CURRENT IMPLEMENTATION
   - 需要持续验证原典完整性

3. **不引入新评分器**
   - 禁止新建 strength_score 类计算
   - 禁止引入人为阈值

---

**请 GPT 裁决是否批准此计划**
