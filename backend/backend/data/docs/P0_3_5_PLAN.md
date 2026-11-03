# P0-3.5 下一阶段工作计划：Primitive/Condition 结构化

**目标**: 将 9 条 C 类 Primitive/Condition 真正结构化并跑通验证链路

---

## 一、当前状态

| 任务 | 状态 |
|------|------|
| T2 strength isolation | 🟢 PASS |
| T3 primitive validation | 🟢 PASS (70%) |
| P0-3.4 semantic attribution | 🟢 PASS |
| Feature boundary | 🟢 基本验证 |
| Primitive/Condition | 🟡 下一阶段 |
| Composite Judgment | 🔒 暂缓 |

---

## 二、C 类 9 条明细

保持语义边界，由辨证层处理：

1. 滴天髓_生克制化_总论
2. 滴天髓_理法_气势
3. 滴天髓_理法_生扶克泄耗
4. 三命通会_强弱_旺极从势
5. 渊海子平_论法_论五行生克制化_2
6. 渊海子平_论法_论月令_4
7. 渊海子平_论法_论太岁吉凶_5
8. 渊海子平_论法_论征太岁_6
9. 渊海子平_论法_论大运_7

---

## 三、验证链路

```
原典 → Evidence → Primitive → Condition → Local Judgment
```

每个环节需要：
- 可执行（代码实现）
- 可回溯（追溯回原典）
- 可测试（自动化测试）

---

## 四、具体任务

### Phase 1: 定义 Primitive Schema
```python
@dataclass(frozen=True)
class Primitive:
    """Primitive 最小验证单元"""
    evidence_id: str           # 来源证据ID
    source_text: str          # 原典原文
    subject: str              # 判断主体
    domain: str               # 辨证域
    primitive_name: str       # Primitive名称
    conditions: List[Condition]
    scope: Scope              # PRIMITIVE/COMPOSITE/LOCAL
    authorization_level: str  # CLASSICAL_EXPLICIT/IMPLICIT/UNRESOLVED
```

### Phase 2: 定义 Condition Schema
```python
@dataclass(frozen=True)
class Condition:
    """Condition 最小验证单元"""
    condition_type: str       # NECESSARY/SUFFICIENT/SUPPORTING/CONSTRAINING/BLOCKING
    feature_ref: Optional[str]  # 对应 Feature 字段（可为空）
    operator: Optional[str]   # >/</==/contains/exists
    value: Optional[Any]      # 阈值或预期值
    evidence_ref: str         # 支撑证据
    authorization: str        # 原典授权文本
```

### Phase 3: 实现 Local Judgment
```python
def local_judgment(primitive: Primitive, features: D1FeatureResult) -> str:
    """从 Primitive + Features 推导 Local Judgment"""
    # 不返回全局 verdict
    # 只返回当前 Primitive 的局部判断
```

### Phase 4: 测试验证
- 对 9 条 C 类证据逐条验证
- 确保链路可执行、可回溯、可测试
- 输出验证报告

---

## 五、成功标准

✅ 9 条 C 类证据全部结构化  
✅ 每条验证链路完整可追溯  
✅ 测试通过  
✅ 无 AI 自补条件现象

---

## 六、风险警示

⚠️ **禁止行为**：
- 不要为了通过率而扩 Feature
- 不要生成"经典规则"
- 不要跳过原典授权环节

---

**等待 Gemini 裁决后开始执行**
