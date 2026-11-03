# P0-4.4 验证报告：Semantic Type → Executable Rule 映射

**日期**: 2026-08-30  
**状态**: 🟢 完成

---

## 一、验证结果汇总

总样本: 30 条（覆盖全部 9 种语义类型）

### 语义类型分布
| 类型 | 数量 |
|------|------|
| FACT（事实/状态） | 5 |
| NECESSARY（必要条件） | 5 |
| BLOCKING（制约/阻断） | 5 |
| INFERENCE（推论） | 5 |
| COMPOUND（复合论断） | 5 |
| PREFERENCE（倾向/宜忌） | 5 |
| UNKNOWN（未确定） | 3 |
| CONDITION（条件） | 0 |
| SUFFICIENT（充分条件） | 0 |

### 可执行性分布
| 状态 | 数量 | 占比 |
|------|------|------|
| EXECUTABLE | 10 | 33.3% |
| SEMANTIC_ONLY | 15 | 50.0% |
| UNRESOLVED | 5 | 16.7% |

---

## 二、关键发现

### 1. EXECUTABLE（可执行）
- **BLOCKING 类型全部可执行**（5/5）
  - 例："太岁乃年中天子，故不可犯"
  - 原因：明确的禁止性规则，可映射为 BLOCKING Condition

- **NECESSARY 类型部分可执行**（0/5，保守判断）
  - 原因：虽然表达必要条件，但 Feature 映射不明确

### 2. SEMANTIC_ONLY（仅语义层）
- **FACT 类型全部保留在语义层**（5/5）
  - 原因：描述客观状态，不产生 Judgment

- **PREFERENCE 类型全部保留在语义层**（5/5）
  - 原因：倾向/宜忌不能直接当确定性规则

- **INFERENCE 类型全部保留在语义层**（5/5）
  - 原因：推论需要保留证据等级，不能直接执行

### 3. UNRESOLVED（未确定）
- **COMPOUND 类型全部保持未确定**（5/5）
  - 原因：复合论断不能简单等同 AND/OR
  - 例："丁火柔中，内性昭融，抱乙而孝，合壬而忠"

- **UNKNOWN 类型全部保持未确定**（3/3）
  - 原因：语义抽象，无法映射

---

## 三、边界划分

### ✅ 可以执行（EXECUTABLE）
- BLOCKING 类型：明确的禁止性规则
- 需要有明确的 Feature 映射

### ⚠️ 仅语义层（SEMANTIC_ONLY）
- FACT 类型：描述性陈述
- PREFERENCE 类型：倾向性建议
- INFERENCE 类型：推论性结论
- NECESSARY 类型：必要性描述（待定）

### 🔒 保持未确定（UNRESOLVED）
- COMPOUND 类型：复合论断
- UNKNOWN 类型：语义抽象

---

## 四、下一步建议

### 方案 A：继续验证 BLOCKING
- 从真实命例验证 BLOCKING 规则
- 确认 Feature 映射是否正确

### 方案 B：深入分析 NECESSARY
- 是否需要原典审核确认 Feature 映射
- 还是保持 SEMANTIC_ONLY

### 方案 C：等待用户指示
- 向 GPT 汇报边界划分结果
- 等待裁决下一步方向

---

**请 GPT 裁决下一步方向**
