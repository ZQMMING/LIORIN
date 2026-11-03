# P0-6 工作计划：Local Judgment Aggregation Contract

**目标**: 设计多 Local Judgment 的上层聚合 Contract，禁止投票机制

---

## 一、背景

P0-5.x 已冻结两个 Local Judgment Contract：
- YHZP-LF-TSJX-5 "日犯岁君"
- DTS-SZ-HZ-ZL "生克制化"

现在需要设计如何聚合多个 Local Judgment，形成更高层级的语义判断。

---

## 二、核心原则

### ✅ 允许
1. **互补组合**：多个 Local Judgment 从不同维度描述同一状态
2. **层级组合**：多个 Local Judgment 形成递进关系
3. **证据叠加**：多个 Independent Evidence 支持同一结论

### ❌ 禁止
1. **投票机制**：A 说吉 + B 说凶 → 投票决定
2. **CONFLICTED 作为最终状态**：冲突必须解决，不能停留
3. **跨体系互相否定**：子平 ≠ 盲派 ≠ 紫微，各自独立
4. **简单加权平均**：不得将 Local Judgment 结果转化为分数

---

## 三、Aggregation Contract 设计

### 1. 数据结构

```python
@dataclass
class LocalJudgment:
    """单个 Local Judgment"""
    primitive_id: str
    judgment: bool  # True = 条件成立
    evidence: str
    authorization: str
    unresolved_parts: list

@dataclass
class AggregationResult:
    """聚合结果"""
    judgments: List[LocalJudgment]
    aggregation_type: str  # "complementary" or "hierarchical"
    conclusion: str  # 综合结论，非投票结果
    conflicts: List[dict]  # 冲突记录，必须解决
    resolution: str  # 冲突解决方式
```

### 2. 聚合类型

#### 类型 A: 互补组合（Complementary）
- 多个 Local Judgment 描述同一状态的不同方面
- 所有 Judgment 都成立时，形成完整描述
- 示例：
  - Local Judgment 1: 日犯岁君成立
  - Local Judgment 2: 生克制化成立
  - 综合: 命局同时存在岁君犯剋和生克失衡

#### 类型 B: 层级组合（Hierarchical）
- 多个 Local Judgment 形成递进关系
- 上层 Judgment 依赖下层 Judgment
- 示例：
  - Local Judgment 1: 得令（月令支持日主）
  - Local Judgment 2: 得地（日支支持日主）
  - Local Judgment 3: 综合身强（需要前两个都成立）

### 3. 冲突处理

#### 冲突类型
1. **事实冲突**：两个 Judgment 基于同一事实，得出矛盾结论
2. **语义冲突**：两个 Judgment 描述不同事实，但结论矛盾

#### 解决方式
1. **补充 Evidence**：寻找更多原典证据
2. **明确边界**：区分适用场景
3. **降级处理**：标记为 UNRESOLVED，不强制解决

#### 禁止
- 不得将冲突标记为 CONFLICTED 后结束
- 不得通过投票解决冲突
- 不得忽略冲突

---

## 四、Golden Validation

### 1. Golden Cases

#### 案例 1: 互补组合（应 PASS）
- 命例：2018-06-01（戊戌年 丁巳月 甲子日 庚午时）
- Local Judgment 1: 日犯岁君成立
- Local Judgment 2: 生克制化成立
- 预期: 两个 Judgment 都成立，形成互补描述

#### 案例 2: 层级组合（应 PASS）
- 需要构造命例，使多个 Primitive 形成层级关系
- 预期: 下层 Judgment 成立是上层 Judgment 的前提

#### 案例 3: 冲突案例（应标记并解决）
- 需要构造或找到存在冲突的命例
- 预期: 冲突被识别并记录，不通过投票解决

---

## 五、实现计划

### Phase 1: Contract 定义
- 定义 AggregationContract 数据结构
- 实现互补组合逻辑
- 实现层级组合逻辑

### Phase 2: Golden Validation
- 设计 Golden Cases
- 运行验证
- 修正实现

### Phase 3: 冲突处理
- 实现冲突识别
- 实现冲突解决逻辑
- 验证冲突处理正确性

---

## 六、关键约束重申

### ✅ 必须遵守
1. 禁止投票机制
2. 禁止 CONFLICTED 作为最终状态
3. 禁止跨体系互相否定
4. 每个 Aggregation 必须有完整的 Evidence 链

### ❌ 禁止
1. 不得引入 strength_score
2. 不得引入人为阈值
3. 不得将 Local Judgment 结果转化为数值
4. 不得进入 Composite Judgment

---

**请 GPT 裁决是否批准此计划**
