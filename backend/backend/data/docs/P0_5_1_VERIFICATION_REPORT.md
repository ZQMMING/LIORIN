# P0-5.1 验证报告：Threshold Provenance Audit（阈值溯源审计）

**日期**: 2026-08-30  
**状态**: 🟡 完成（发现阈值无原典授权）

---

## 一、审计结果汇总

总样本: 2 条

| 特征 | 阈值 | 判定 | 建议 |
|------|------|------|------|
| de_di | >= 2 | 🔴 ENGINEERED_THRESHOLD | 标注为工程定义 |
| de_shi | >= 2 | 🔴 ENGINEERED_THRESHOLD | 标注为工程定义 |

---

## 二、详细审计

### 1. de_di >= 2（得地）

**审计结果**: 没有原典明确授权

**分析**:
- 《滴天髓》"得地者强"没有给出具体数值阈值
- >= 2 是工程定义，不是经典授权
- 需要改为 ENGINEERED_THRESHOLD 标签

**证据等级**:
- Feature: CANONICAL（de_di 计算定义明确）
- Condition: ENGINEERED_THRESHOLD（>= 2 是工程定义）

### 2. de_shi >= 2（得势）

**审计结果**: 没有原典明确授权

**分析**:
- 《滴天髓》"得势者强"没有给出具体数值阈值
- >= 2 是工程定义，不是经典授权
- 需要改为 ENGINEERED_THRESHOLD 标签

**证据等级**:
- Feature: CANONICAL（de_shi 计算定义明确）
- Condition: ENGINEERED_THRESHOLD（>= 2 是工程定义）

---

## 三、核心发现

### ✅ Feature 是 Canonical
- de_di（得地计数）：确定性计算
- de_shi（得势计数）：确定性计算

### ❌ Condition 不是 CLASSICAL_EXPLICIT
- de_di >= 2：阈值没有原典授权
- de_shi >= 2：阈值没有原典授权

### ⚠️ 必须区分
```
Feature: CANONICAL（计算定义明确）
Condition: ENGINEERED_THRESHOLD（阈值是工程定义）
```

---

## 四、正确做法

1. **不要**把 >= 2 标成 CLASSICAL_EXPLICIT
2. **要**把 >= 2 标成 ENGINEERED_THRESHOLD
3. **要**在证据链中明确标注阈值来源

---

## 五、下一步建议

### 方案 A: 继续验证更多 Primitive
- 从 P0-3.7 的 4 条 EXPLICIT 中选择
- 验证其他 Authorized Primitive

### 方案 B: 等待 GPT 指示
- 向 GPT 汇报审计结果
- 等待裁决下一步方向

---

**请 GPT 裁决下一步方向**

