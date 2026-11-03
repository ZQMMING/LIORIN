# WORKER-SMTH: 《三命通会》Worker生产报告

**Worker ID**: WORKER-SMTH  
**执行时间**: 2026-08-31  
**产出数量**: 20个Primitive Candidate

---

## 目标
从《三命通会》提取Primitive Candidate，重点：论天干、论地支、论五行

---

## 产出清单

| # | Candidate ID | 语义单元 | Primitive | text_layer | canonical_mapping | 状态 |
|---|--------------|----------|-----------|------------|-------------------|------|
| 1 | CAND-SMTH-001 | 天干 | 甲木总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 2 | CAND-SMTH-002 | 天干 | 乙木总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 3 | CAND-SMTH-003 | 天干 | 丙火总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 4 | CAND-SMTH-004 | 天干 | 丁火总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 5 | CAND-SMTH-005 | 天干 | 戊土总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 6 | CAND-SMTH-006 | 天干 | 己土总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 7 | CAND-SMTH-007 | 天干 | 庚金总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 8 | CAND-SMTH-008 | 天干 | 辛金总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 9 | CAND-SMTH-009 | 天干 | 壬水总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 10 | CAND-SMTH-010 | 天干 | 癸水总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 11 | CAND-SMTH-011 | 地支 | 子水总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 12 | CAND-SMTH-012 | 地支 | 丑土总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 13 | CAND-SMTH-013 | 地支 | 寅木总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 14 | CAND-SMTH-014 | 地支 | 卯木总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 15 | CAND-SMTH-015 | 地支 | 辰土总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 16 | CAND-SMTH-016 | 地支 | 巳火总论 | ORIGINAL_TEXT | CANONICAL | PASS |
| 17 | CAND-SMTH-017 | 五行 | 木属性 | ORIGINAL_TEXT | CANONICAL | PASS |
| 18 | CAND-SMTH-018 | 五行 | 火属性 | ORIGINAL_TEXT | CANONICAL | PASS |
| 19 | CAND-SMTH-019 | 五行 | 土属性 | ORIGINAL_TEXT | CANONICAL | PASS |
| 20 | CAND-SMTH-020 | 纳音 | 六十甲子 | ORIGINAL_TEXT | PARTIAL | PASS |

---

## 统计

| 类别 | 数量 |
|------|------|
| **CANONICAL** | 19个 |
| **PARTIAL** | 1个 |
| **UNRESOLVED** | 0个 |
| **总计** | 20个 |

---

## 关键发现

### 原典特点
- 《三命通会》以"总论"形式呈现
- 定义性强，适合提取Primitive
- 多为描述性内容，少条件判断

### PARTIAL条目
- CAND-SMTH-020: 纳音概念需要补充定义

---

## V3 Schema校验结果

```
✅ 三字段一致性: 20/20 PASS
✅ text_layer与内容字段对应: 20/20 PASS
✅ source_location格式: 20/20 PASS
```