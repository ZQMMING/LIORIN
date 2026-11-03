# Candidate Pool Schema V2.0

**时间**: 2026-08-31  
**依据**: GPT裁决 8bb2150  
**状态**: 🟢 修正完成

---

## 字段修正

### 🔴 问题（V1.0）
```json
{
  "source_version": "任铁樵注本",
  "text_layer": "ORIGINAL_COMMENTARY",
  "original_text": "三元者，天干也。",
  ...
}
```
**问题**：把任注内容放进`original_text`，字段名误导。

### ✅ 修正（V2.0）
```json
{
  "text_layer": "ORIGINAL_COMMENTARY",
  "original_text": "",
  "commentary_text": "三元者，天干也。",
  "later_commentary_text": "",
  ...
}
```
**修正**：
- `original_text`只放《滴天髓》正文
- `commentary_text`放任铁樵注释
- `later_commentary_text`放后世解释
- 三者只能有一个有值

---

## 三层文本分离

| 字段 | 内容 | 示例 |
|------|------|------|
| **original_text** | 《滴天髓》正文 | "五阳从气不从势" |
| **commentary_text** | 任铁樵注释 | "任氏曰：五阳从气..." |
| **later_commentary_text** | 后世解释 | 民国/现代学者解释 |

---

## 完整Schema

```json
{
  "candidate_id": "CAND-{BOOK}-{SEQ}",
  "source_book": "滴天髓|子平真诠|穷通宝鉴|三命通会|渊海子平",
  "text_layer": "ORIGINAL_TEXT|ORIGINAL_COMMENTARY|LATER_COMMENTARY",
  
  "original_text": "",
  "commentary_text": "",
  "later_commentary_text": "",
  
  "source_location": "章节位置",
  "semantic_unit": "提取的语义单元",
  "primitive_candidate": "候选Primitive名称",
  "canonical_mapping": "CANONICAL|PARTIAL|UNRESOLVED",
  "confidence": "HIGH|MEDIUM|LOW",
  "unresolved_questions": [],
  "agent_id": "WORKER-{BOOK}",
  "creation_time": "ISO8601",
  "red_team_flags": [],
  "audit_status": "PENDING|APPROVED|DENIED"
}
```

---

## 验证规则

### Rule 1: text_layer与字段对应
- `ORIGINAL_TEXT` → `original_text`必须有值
- `ORIGINAL_COMMENTARY` → `commentary_text`必须有值
- `LATER_COMMENTARY` → `later_commentary_text`必须有值

### Rule 2: 三段互斥
- 只能有一个字段有值
- 不能同时有多个字段有值

### Rule 3: source_version已删除
- 改由`text_layer`明确区分
- 避免"注本"与"通行本"混淆

---

## Pilot Batch V2统计

| Candidate ID | text_layer | 内容字段 | 状态 |
|--------------|------------|----------|------|
| CAND-DTS-001 | ORIGINAL_COMMENTARY | commentary_text | ✅ PASS |
| CAND-DTS-002 | ORIGINAL_COMMENTARY | commentary_text | ✅ PASS |
| CAND-DTS-003 | ORIGINAL_COMMENTARY | commentary_text | ⚠️ PARTIAL |
| CAND-DTS-004 | ORIGINAL_TEXT | original_text | ✅ PASS |
| CAND-DTS-005 | ORIGINAL_TEXT | original_text | 🔴 FAIL |
| CAND-DTS-006 | ORIGINAL_TEXT | original_text | ✅ PASS |
| CAND-DTS-007 | ORIGINAL_TEXT | original_text | ✅ PASS |
| CAND-DTS-008 | ORIGINAL_COMMENTARY | commentary_text | ✅ PASS |