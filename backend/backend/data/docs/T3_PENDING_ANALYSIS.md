# T3 归因分析报告：15 条 PENDING 分类

**日期**: 2026-08-30  
**状态**: 🟡 待 Gemini 裁决

---

## 一、分类结果

| 类别 | 数量 | 含义 | 处理方式 |
|------|------|------|----------|
| **A** | 6 | 现有 Feature 已有，映射缺失 | 补充 Mapping 规则 |
| **B** | 0 | 需要新增 Calculation Feature | 允许扩展（但本次为 0） |
| **C** | 8 | Primitive/Condition 语义 | 保持分离，由辨证层处理 |
| **D** | 1 | 需要综合辨证 | 交由辨证层处理 |

**关键发现**: B=0，不需要扩展 D1FeatureResult。

---

## 二、A 类明细（需补充 Mapping）

| Evidence ID | Domain | 建议 |
|-------------|--------|------|
| 三命通会_强弱_得令 | wangshuai | 映射 de_ling / de_ling_weight |
| 三命通会_强弱_得地 | ten_god | 映射 de_di / de_di_detail |
| 三命通会_强弱_得势 | wangshuai | 映射 de_shi / de_shi_detail |
| 三命通会_强弱_身强条件 | wangshuai | 映射 support_count vs drain_count |
| 三命通会_强弱_身弱条件 | wangshuai | 映射 drain_count > support_count |
| 三命通会_强弱_身强三要素 | wangshuai | 映射 de_ling + de_di + de_shi |

---

## 三、C 类明细（保持分离）

| Evidence ID | Domain | 建议 |
|-------------|--------|------|
| 滴天髓_生克制化_总论 | wangshuai | 辨证层处理 |
| 滴天髓_理法_气势 | wangshuai | 辨证层处理 |
| 滴天髓_理法_生扶克泄耗 | wangshuai | 辨证层处理 |
| 渊海子平_论法_论五行生克制化_2 | wangshuai | 辨证层处理 |
| 渊海子平_论法_论月令_4 | wangshuai | 辨证层处理 |
| 渊海子平_论法_论太岁吉凶_5 | pattern | 辨证层处理 |
| 渊海子平_论法_论征太岁_6 | wangshuai | 辨证层处理 |
| 渊海子平_论法_论大运_7 | wangshuai | 辨证层处理 |

---

## 四、D 类明细（交由辨证层）

| Evidence ID | Domain | 建议 |
|-------------|--------|------|
| 三命通会_强弱_旺极从势 | wangshuai | 辨证层处理（综合判断） |

---

## 五、下一步建议

### 方案 1: 补充 Mapping 规则（推荐）
- 为 A 类 6 条定义明确的 Feature → Primitive 映射
- 重新跑 30 条验证
- 目标：提升到 21/30 VERIFIED

### 方案 2: 保持现状
- 接受 15/30 验证率
- 继续推进 T3 其他任务

---

## 六、关键结论

✅ **不需要扩展 D1FeatureResult**（B=0）  
⚠️ **需要补充 Mapping 规则**（A=6）  
🔒 **C/D 类保持语义边界**（15 条中的 9 条）

---

**请 Gemini 裁决**: 是否执行方案 1 补充 Mapping？
