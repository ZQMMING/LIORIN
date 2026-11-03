# 五经证据整理项目 - 内部检验报告 v3

**日期**: 2026-09-02
**状态**: 收集/整理/校对阶段（未进入生产流程）
**目标**: 全部裁决通过后方可进入下一阶段

---

## 一、证据总量统计

| 经典 | 证据数 | 来源 |
|------|--------|------|
| 滴天髓 (DTS) | 44 | data/classics/original/DTS_滴天髓_段落数据_merged.json |
| 子平真诠 (PZZQ) | 10 | data/classics/original/PZZQ_子平真诠_段落数据_merged.json |
| 穷通宝鉴 (QTBJ) | 1,233 | data/classics/original/QTBJ_穷通宝鉴_段落数据_merged.json |
| 三命通会 (SMTH) | 8 | data/classics/original/SMTH_三命通会_段落数据_merged.json |
| 渊海子平 (YHZP) | 117 | data/classics/original/YHZP_渊海子平_段落数据_merged.json |
| **总计** | **1,412** | — |

---

## 二、质量指标

### 字段覆盖率

| 字段 | 数量 | 覆盖率 | 达标线 | 状态 |
|------|------|--------|--------|------|
| classical_theme | 1,412/1,412 | **100%** | ≥95% | ✅ |
| conditions | 983/1,412 | **69.6%** | ≥80% | ⚠️ |
| trigger_conditions | 1,412/1,412 | **100%** | — | ✅ |
| semantic_result | 1,412/1,412 | **100%** | — | ✅ |
| scope | 1,412/1,412 | **100%** | — | ✅ |
| exceptions | 1,412/1,412 | **100%** | — | ✅ |
| source_version | 1,412/1,1412 | **100%** | — | ✅ |
| provenance | 1,412/1,412 | **100%** | — | ✅ |
| context_before/after | 1,390/1,412 | **98.4%** | ≥90% | ✅ |

### 各经典明细

| 经典 | 总数 | Theme | Conditions | Context | 评分 |
|------|------|-------|------------|---------|------|
| DTS | 44 | 100% | 84.1% | 100% | 88.5 |
| PZZQ | 10 | 100% | 80% | 70% | 82.0 |
| QTBJ | 1,233 | 100% | 67.5% | 98.7% | 82.0 |
| SMTH | 8 | 100% | 25% | 100% | 72.5 |
| YHZP | 117 | 100% | 88.9% | 97.4% | 90.0 |

### 综合评分

| 维度 | 权重 | 得分 | 加权分 |
|------|------|------|--------|
| 主题完整性 | 10% | 100% | 10.0 |
| 条件完整性 | 50% | 69.6% | 34.8 |
| 上下文完整性 | 30% | 98.4% | 29.5 |
| 来源有效性 | 10% | 100% | 10.0 |
| **综合评分** | **100%** | | **84.3/100** |

---

## 三、改进措施

### 1. Passage合并
将短passage（<200字符）合并到相邻段落，形成有意义的上下文块：

| 经典 | 合并前 | 合并后 | 短passage减少 |
|------|--------|--------|---------------|
| DTS | 719 | 409 | 458→84 (81.7%) |
| PZZQ | 446 | 164 | 430→74 (82.9%) |
| QTBJ | 1,556 | 529 | 1,548→423 (72.7%) |
| SMTH | 1,846 | 1,841 | 6→1 (83.3%) |
| YHZP | 2,472 | 883 | 2,384→730 (69.4%) |

### 2. Context提取
从passage中定位证据原文，提取前后300字符上下文：
- DTS: 100%
- PZZQ: 70%（原文等于passage时无前后文）
- QTBJ: 98.7%
- SMTH: 100%（从相邻passage获取）
- YHZP: 97.4%

### 3. 语义字段补全
自动提取classical_theme, conditions, scope等字段。

---

## 四、已知问题

| 问题 | 数量 | 优先级 | 说明 |
|------|------|--------|------|
| 缺少conditions | 429条 | P1 | 原文条件句式不明显 |
| PZZQ context低 | 3条 | P2 | 原文等于passage |
| SMTH conditions低 | 6条 | P2 | 短文本难提取条件 |
| E-DTS-106-001 | 1条 | P0 | 溯源需人工复核 |

---

## 五、待裁决项

### 当前状态
- 证据基础数据已建立
- 溯源验证99.93%通过
- 综合质量评分84.3/100
- **未进入生产流程**

### 建议
1. 继续优化conditions提取算法，目标≥80%
2. 人工复核E-DTS-106-001溯源问题
3. SMTH证据需补充更多上下文理解

---

## 六、产出文件

```
data/evidence/                    # 1,412条证据（已补全语义字段）
data/classics/original/*_merged.json  # 合并后的原典数据
data/reports/completion_summary_v2.json
docs/evidence_quality_report_v3.md  # 本报告
scripts/complete_evidence_fields_v2.py
scripts/update_evidence_context.py
scripts/fix_evidence_quality.py
scripts/merge_passages.py
```

---

**结论**: 证据收集/整理/校对阶段基本完成，质量评分84.3分。待裁决通过后方可进入Assertion Mapping阶段。
