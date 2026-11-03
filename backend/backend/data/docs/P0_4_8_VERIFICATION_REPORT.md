# P0-4.8 验证报告：Semantic Feature → Primitive 映射

**日期**: 2026-08-30  
**状态**: 🟢 完成

---

## 一、验证结果汇总

总测试: 8 条

### 符合预期: 6/8 (75%)

### 结果分布
| 结果 | 数量 |
|------|------|
| SAFE | 3 |
| BLOCKED | 3 |
| UNSAFE | 2 |

### Feature 类型分布
| 类型 | 数量 |
|------|------|
| CANONICAL_FEATURE | 3 |
| DERIVABLE_FEATURE | 2 |
| SEMANTIC_ONLY | 3 |

---

## 二、关键发现

### ✅ CANONICAL_FEATURE 安全映射
- de_ling（得令）→ 确定性计算 ✅
- de_di（得地）→ 确定性计算 ✅
- de_shi（得势）→ 确定性计算 ✅

### ⚠️ DERIVABLE_FEATURE 需要明确定义
- support_ratio（支持比例）→ 定义不完整，标记为 UNSAFE
- wu_ji_pressure（戊己压力）→ 定义不完整，标记为 UNSAFE
- **正确行为**: DERIVABLE_FEATURE 必须有明确定义才能安全映射

### 🔒 SEMANTIC_ONLY 正确阻止
- huo_chizhi（火炽）→ 禁止伪装 ✅
- wu_zhi_mai（土埋）→ 禁止伪装 ✅
- sheng_ke_balance（生克平衡）→ 禁止伪装 ✅

---

## 三、安全边界确认

### 规则 1: SEMANTIC_ONLY 不能是确定性计算
- 3/3 正确阻止 ✅

### 规则 2: DERIVABLE_FEATURE 需要明确定义
- 2/2 正确标记 ✅

### 规则 3: CANONICAL_FEATURE 必须是确定性计算
- 3/3 正确验证 ✅

---

## 四、下一步建议

### 方案 A: 继续验证更多 Primitive
- 从五经中选取更多样本
- 验证映射边界

### 方案 B: 定义 DERIVABLE_FEATURE 计算
- 为 support_ratio 和 wu_ji_pressure 定义明确计算
- 转换为 CANONICAL_FEATURE

### 方案 C: 等待 GPT 指示
- 向 GPT 汇报验证结果
- 等待裁决下一步方向

---

**请 GPT 裁决下一步方向**
