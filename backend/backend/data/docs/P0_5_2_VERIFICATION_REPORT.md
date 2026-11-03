# P0-5.2 验证报告：Threshold 来源审计 + 规则分层

**日期**: 2026-08-30  
**状态**: 🟢 完成

---

## 一、验证结果汇总

总样本: 5 条

| 特征 | 阈值 | 状态 | 层级 | 结果 |
|------|------|------|------|------|
| de_ling | True | CLASSICAL_EXPLICIT | 生产层 | ✅ 可授权 |
| de_di | 2 | ENGINEERED_THRESHOLD | 研究层 | 🔴 禁止生产 |
| de_shi | 2 | ENGINEERED_THRESHOLD | 研究层 | 🔴 禁止生产 |
| support_ratio | None | SEMANTIC_ONLY | 禁止层 | 🔴 禁止 Judgment |
| wu_ji_pressure | None | UNRESOLVED | 禁止层 | 🔴 禁止 Judgment |

---

## 二、规则分层架构

### 1. CLASSICAL_EXPLICIT（可授权）
- de_ling = True（得令者旺）
- 可进入 Classical Judgment

### 2. CLASSICAL_IMPLICIT（暂不授权）
- （暂无）

### 3. ENGINEERED_THRESHOLD（研究层）
- de_di >= 2
- de_shi >= 2
- 禁止生产，仅研究

### 4. SEMANTIC_ONLY（禁止层）
- support_ratio
- 禁止 Judgment

### 5. UNRESOLVED（禁止层）
- wu_ji_pressure
- 禁止 Judgment

---

## 三、关键发现

### ✅ 规则分层正确
- CLASSICAL_EXPLICIT → 生产层
- ENGINEERED_THRESHOLD → 研究层
- SEMANTIC_ONLY / UNRESOLVED → 禁止层

### ✅ 隔离生效
- ENGINEERED_THRESHOLD 不能进入 Classical Authorization Gate
- 只有 CLASSICAL_EXPLICIT 可以授权

### ✅ 审计结论清晰
- de_ling: CLASSICAL_EXPLICIT（有原典授权）
- de_di/de_shi: ENGINEERED_THRESHOLD（无原典授权）

---

## 四、下一步建议

### 方案 A: 继续验证更多 Primitive
- 从 P0-3.7 的 4 条 EXPLICIT 中选择
- 验证其他 Authorized Primitive

### 方案 B: 进入 P0-5.3
- 基于规则分层，重新测试 P0-5 Local Judgment
- 只使用 CLASSICAL_EXPLICIT 条件

### 方案 C: 等待 GPT 指示
- 向 GPT 汇报验证结果
- 等待裁决下一步方向

---

**请 GPT 裁决下一步方向**
