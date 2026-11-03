# P0-3.4 语义归因报告

**日期**: 2026-08-30  
**状态**: 🟡 待 Gemini 裁决

---

## 一、归因结果

### 统计

A 类：6 条 — 现有 Feature 已有，映射缺失  
B 类：0 条 — 需要新增 Calculation Feature（无）  
C 类：9 条 — Primitive/Condition 语义，保持分离  
D 类：0 条 — 需要综合辨证（无）

**关键结论**: B=0，不需要扩展 D1FeatureResult

---

## 二、A 类明细（6 条）

需补充 Mapping 规则，不扩 Feature：

1. 三命通会_强弱_得令 → de_ling
2. 三命通会_强弱_得地 → de_di
3. 三命通会_强弱_得势 → de_shi
4. 三命通会_强弱_身强条件 → support_count > drain_count
5. 三命通会_强弱_身弱条件 → drain_count > support_count
6. 三命通会_强弱_身强三要素 → de_ling + de_di + de_shi

---

## 三、C 类明细（9 条）

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

## 四、风险警示

⚠️ **原典描述 ≠ Condition**

示例："甲木参天，脱胎要火"

这是原典语句/性质描述，不是自动生成一个 Condition 就算完成。

**风险**: AI 自己补条件 → 变成"经典规则" → 失去原典授权边界

---

## 五、下一步建议

### 方案 1: 补充 Mapping（推荐）
- 为 A 类 6 条定义明确 Mapping
- 不扩展 D1FeatureResult
- 重新验证提升通过率

### 方案 2: 保持现状
- 接受 70% 通过率
- C 类 9 条交由辨证层

---

## 六、数据基础

- `data/p0_3_3_structured_evidence.json` — 385 条证据
- `data/p0_3_4_attribution.json` — 15 条归因结果
- `data/t3_mapping_rules.json` — 6 条 Mapping 规则

---

**请 Gemini 裁决下一步行动**
