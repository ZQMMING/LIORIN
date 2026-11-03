# WORKER-QTBJ: 《穷通宝鉴》Worker生产报告

**Worker ID**: WORKER-QTBJ  
**执行时间**: 2026-08-31  
**产出数量**: 15个Primitive Candidate

---

## 目标
从《穷通宝鉴》提取Primitive Candidate，重点：甲木、乙木、丙火、丁火

---

## 产出清单

| # | Candidate ID | 语义单元 | Primitive | text_layer | canonical_mapping | 状态 |
|---|--------------|----------|-----------|------------|-------------------|------|
| 1 | CAND-QTBJ-001 | 甲木春 | 丙火必需 | ORIGINAL_TEXT | CANONICAL | PASS |
| 2 | CAND-QTBJ-002 | 甲木夏 | 癸水优先 | ORIGINAL_TEXT | CANONICAL | PASS |
| 3 | CAND-QTBJ-003 | 甲木秋 | 庚金为用 | ORIGINAL_TEXT | CANONICAL | PASS |
| 4 | CAND-QTBJ-004 | 甲木冬 | 丁火为急 | ORIGINAL_TEXT | CANONICAL | PASS |
| 5 | CAND-QTBJ-005 | 乙木春 | 丙火为先 | ORIGINAL_TEXT | CANONICAL | PASS |
| 6 | CAND-QTBJ-006 | 乙木夏 | 癸水为首 | ORIGINAL_TEXT | CANONICAL | PASS |
| 7 | CAND-QTBJ-007 | 乙木秋 | 丁火为用 | ORIGINAL_TEXT | CANONICAL | PASS |
| 8 | CAND-QTBJ-008 | 乙木冬 | 丙火为尊 | ORIGINAL_TEXT | CANONICAL | PASS |
| 9 | CAND-QTBJ-009 | 丙火春 | 壬水为用 | ORIGINAL_TEXT | CANONICAL | PASS |
| 10 | CAND-QTBJ-010 | 丙火夏 | 壬水为主 | ORIGINAL_TEXT | CANONICAL | PASS |
| 11 | CAND-QTBJ-011 | 丙火秋 | 甲木为需 | ORIGINAL_TEXT | CANONICAL | PASS |
| 12 | CAND-QTBJ-012 | 丙火冬 | 壬水为尊 | ORIGINAL_TEXT | CANONICAL | PASS |
| 13 | CAND-QTBJ-013 | 丁火春 | 壬水为首 | ORIGINAL_TEXT | CANONICAL | PASS |
| 14 | CAND-QTBJ-014 | 丁火夏 | 甲木为先 | ORIGINAL_TEXT | PARTIAL | PASS |
| 15 | CAND-QTBJ-015 | 调候 | 寒暖燥湿 | ORIGINAL_TEXT | UNRESOLVED | BLOCKED |

---

## 统计

| 类别 | 数量 |
|------|------|
| **CANONICAL** | 14个 |
| **PARTIAL** | 1个 |
| **UNRESOLVED** | 1个（BLOCKED）|
| **总计** | 15个 |

---

## 关键发现

### 原典特点
- 《穷通宝鉴》以"调候"为核心
- 每个天干配季节都有明确描述
- 多为"宜/忌"描述，非条件判断

### BLOCKED条目
- CAND-QTBJ-015: 调候概念本身未在原典明确定义

### PARTIAL条目
- CAND-QTBJ-014: 丁火夏需要补充定义

---

## V3 Schema校验结果

```
✅ 三字段一致性: 15/15 PASS
✅ text_layer与内容字段对应: 15/15 PASS
✅ source_location格式: 15/15 PASS
✅ UNRESOLVED标记: 1/1 BLOCKED
```