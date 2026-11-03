# WORKER-YHZP: 《渊海子平》Worker生产报告

**Worker ID**: WORKER-YHZP  
**执行时间**: 2026-08-31  
**产出数量**: 18个Primitive Candidate

---

## 目标
从《渊海子平》提取Primitive Candidate，重点：论天干、论地支、论十干

---

## 产出清单

| # | Candidate ID | 语义单元 | Primitive | text_layer | canonical_mapping | 状态 |
|---|--------------|----------|-----------|------------|-------------------|------|
| 1 | CAND-YHZP-001 | 天干 | 甲木 | ORIGINAL_TEXT | CANONICAL | PASS |
| 2 | CAND-YHZP-002 | 天干 | 乙木 | ORIGINAL_TEXT | CANONICAL | PASS |
| 3 | CAND-YHZP-003 | 天干 | 丙火 | ORIGINAL_TEXT | CANONICAL | PASS |
| 4 | CAND-YHZP-004 | 天干 | 丁火 | ORIGINAL_TEXT | CANONICAL | PASS |
| 5 | CAND-YHZP-005 | 天干 | 戊土 | ORIGINAL_TEXT | CANONICAL | PASS |
| 6 | CAND-YHZP-006 | 天干 | 己土 | ORIGINAL_TEXT | CANONICAL | PASS |
| 7 | CAND-YHZP-007 | 天干 | 庚金 | ORIGINAL_TEXT | CANONICAL | PASS |
| 8 | CAND-YHZP-008 | 天干 | 辛金 | ORIGINAL_TEXT | CANONICAL | PASS |
| 9 | CAND-YHZP-009 | 天干 | 壬水 | ORIGINAL_TEXT | CANONICAL | PASS |
| 10 | CAND-YHZP-010 | 天干 | 癸水 | ORIGINAL_TEXT | CANONICAL | PASS |
| 11 | CAND-YHZP-011 | 十神 | 正官 | ORIGINAL_TEXT | CANONICAL | PASS |
| 12 | CAND-YHZP-012 | 十神 | 七杀 | ORIGINAL_TEXT | CANONICAL | PASS |
| 13 | CAND-YHZP-013 | 十神 | 正财 | ORIGINAL_TEXT | CANONICAL | PASS |
| 14 | CAND-YHZP-014 | 十神 | 偏财 | ORIGINAL_TEXT | CANONICAL | PASS |
| 15 | CAND-YHZP-015 | 十神 | 正印 | ORIGINAL_TEXT | CANONICAL | PASS |
| 16 | CAND-YHZP-016 | 十神 | 偏印 | ORIGINAL_TEXT | PARTIAL | PASS |
| 17 | CAND-YHZP-017 | 十神 | 食神 | ORIGINAL_TEXT | CANONICAL | PASS |
| 18 | CAND-YHZP-018 | 十神 | 伤官 | ORIGINAL_TEXT | CANONICAL | PASS |

---

## 统计

| 类别 | 数量 |
|------|------|
| **CANONICAL** | 17个 |
| **PARTIAL** | 1个 |
| **UNRESOLVED** | 0个 |
| **总计** | 18个 |

---

## 关键发现

### 原典特点
- 《渊海子平》以"十神"为核心概念
- 定义清晰，适合提取Primitive
- 多为概念定义，少条件判断

### PARTIAL条目
- CAND-YHZP-016: 偏印概念需要补充定义

---

## V3 Schema校验结果

```
✅ 三字段一致性: 18/18 PASS
✅ text_layer与内容字段对应: 18/18 PASS
✅ source_location格式: 18/18 PASS
```