# WORKER-ZPZQ: 《子平真诠》Worker生产报告

**Worker ID**: WORKER-ZPZQ  
**执行时间**: 2026-08-31  
**产出数量**: 20个Primitive Candidate

---

## 目标
从《子平真诠》提取Primitive Candidate，重点：论格局、论用神

---

## 产出清单

| # | Candidate ID | 语义单元 | Primitive | text_layer | canonical_mapping | 状态 |
|---|--------------|----------|-----------|------------|-------------------|------|
| 1 | CAND-ZPZQ-001 | 格局 | 月令格 | ORIGINAL_TEXT | CANONICAL | PASS |
| 2 | CAND-ZPZQ-002 | 用神 | 月令透干 | ORIGINAL_TEXT | CANONICAL | PASS |
| 3 | CAND-ZPZQ-003 | 相神 | 辅佐用神 | ORIGINAL_TEXT | CANONICAL | PASS |
| 4 | CAND-ZPZQ-004 | 杂格 | 外格 | ORIGINAL_TEXT | PARTIAL | PASS |
| 5 | CAND-ZPZQ-005 | 格局成败 | 成格条件 | ORIGINAL_TEXT | UNRESOLVED | BLOCKED |
| 6 | CAND-ZPZQ-006 | 格局成败 | 破格条件 | ORIGINAL_TEXT | UNRESOLVED | BLOCKED |
| 7 | CAND-ZPZQ-007 | 用神 | 财官印食 | ORIGINAL_TEXT | CANONICAL | PASS |
| 8 | CAND-ZPZQ-008 | 相神 | 护用之神 | ORIGINAL_COMMENTARY | CANONICAL | PASS |
| 9 | CAND-ZPZQ-009 | 格局 | 八格 | ORIGINAL_TEXT | CANONICAL | PASS |
| 10 | CAND-ZPZQ-010 | 格局 | 十干配局 | ORIGINAL_COMMENTARY | CANONICAL | PASS |
| 11 | CAND-ZPZQ-011 | 用神 | 月令取用 | ORIGINAL_TEXT | CANONICAL | PASS |
| 12 | CAND-ZPZQ-012 | 相神 | 相神得力 | ORIGINAL_TEXT | CANONICAL | PASS |
| 13 | CAND-ZPZQ-013 | 格局 | 成格条件 | ORIGINAL_TEXT | UNRESOLVED | BLOCKED |
| 14 | CAND-ZPZQ-014 | 格局 | 败格条件 | ORIGINAL_TEXT | UNRESOLVED | BLOCKED |
| 15 | CAND-ZPZQ-015 | 用神 | 用神有情 | ORIGINAL_COMMENTARY | CANONICAL | PASS |
| 16 | CAND-ZPZQ-016 | 相神 | 相神无破 | ORIGINAL_TEXT | CANONICAL | PASS |
| 17 | CAND-ZPZQ-017 | 格局 | 清浊之分 | ORIGINAL_TEXT | CANONICAL | PASS |
| 18 | CAND-ZPZQ-018 | 用神 | 用神深浅 | ORIGINAL_COMMENTARY | PARTIAL | PASS |
| 19 | CAND-ZPZQ-019 | 格局 | 格之成败 | ORIGINAL_TEXT | UNRESOLVED | BLOCKED |
| 20 | CAND-ZPZQ-020 | 杂格 | 从化诸格 | ORIGINAL_TEXT | UNRESOLVED | BLOCKED |

---

## 统计

| 类别 | 数量 |
|------|------|
| **CANONICAL** | 12个 |
| **PARTIAL** | 2个 |
| **UNRESOLVED** | 6个（BLOCKED）|
| **总计** | 20个 |

---

## 关键发现

### BLOCKED条目（6个）
- CAND-ZPZQ-005: 成格条件 - 原典未明确定义"成格"
- CAND-ZPZQ-006: 破格条件 - 涉及L4风险
- CAND-ZPZQ-013: 成格条件（重复）
- CAND-ZPZQ-014: 败格条件 - 原典未明确
- CAND-ZPZQ-019: 格之成败 - 原典描述而非条件判断
- CAND-ZPZQ-020: 从化诸格 - 涉及从格，原典未明确定义

### 正确标记
- UNRESOLVED → BLOCKED，明确禁止进入Production
- PARTIAL → 标注需要补充定义
- CANONICAL → 原典明确定义的最小语义单元

---

## V3 Schema校验结果

```
✅ 三字段一致性: 20/20 PASS
✅ text_layer与内容字段对应: 20/20 PASS
✅ source_location格式: 20/20 PASS
✅ UNRESOLVED标记: 6/6 BLOCKED
```