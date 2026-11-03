# Five Classics Conflict Analysis - Summary for Arbitration

**Repository**: https://github.com/ZQMMING/wisdom  
**Branch**: main  
**Latest Commit**: 281462e - "P2 Entry Audit: Full Repository Reconciliation"

---

## Evidence Data

| Classic | Evidence Count | Source Directory |
|---------|---------------|------------------|
| 滴天髓 (DTS) | 44 | `data/evidence/di_tian_sui/` |
| 穷通宝鉴 (QTBJ) | 1,233 | `data/evidence/qiong_tong_bao_jian/` |
| 渊海子平 (YHZP) | 117 | `data/evidence/yuan_hai_zi_ping/` |
| 三命通会 (SMTH) | 8 | `data/evidence/san_ming_tong_hui/` |
| 子平真诠 (PZZQ) | 10 | `data/evidence/ziping_zhenquan/` |
| **Total** | **1,412** | |

---

## Quality Metrics

| Metric | Coverage | Target | Status |
|--------|----------|--------|--------|
| Theme | 100% | ≥95% | ✅ |
| Conditions | 99.9% | ≥80% | ✅ |
| Context | 98.4% | ≥90% | ✅ |
| Source | 100% | 100% | ✅ |
| **Overall Score** | **99.5/100** | ≥85 | ✅ |

---

## Conflicts for Arbitration

### 🔴 High Priority (3 conflicts)

**1. WangShuai vs TiaoHou (DTS vs QTBJ)**
- DTS: "须观日主之衰旺，察生时之浅深，究四柱之用神"
- QTBJ: "秋月之木，氣漸淒涼...初秋之時，火氣未除，尤喜水土以相滋"
- Conflict evidence: ~50条
- Suggested resolution: Hierarchical rule - WangShuai first, then TiaoHou

**2. YongShen Standard (PZZQ vs YHZP)**
- PZZQ: "八字用神，专求月令"
- YHZP: "以日为主，大要看日加临于甚度，或身旺？或身弱？"
- Conflict evidence: ~15条
- Suggested resolution: Month command determines structure, Day master determines strength

**3. Methodology: Simplification vs Refinement (DTS vs PZZQ)**
- DTS: "看奇格异局，一切神杀，荒唐取用...非关命理体咎"
- PZZQ: "相神无破，贵格已成；相神有伤，立败其格"
- Conflict evidence: ~8条
- Suggested resolution: Layered processing - DTS philosophy + PZZQ methods

### 🟡 Medium Priority (2 conflicts)

**4. Pattern Classification (PZZQ vs YHZP)**
- PZZQ: Binary - Zheng Ge (正格) vs Za Ge (杂格)
- YHZP: Ternary - Qing Ge (清格), Zhuo Ge (浊格), Hun He Ge (混合格)
- Conflict evidence: ~10条

**5. Five Elements Circulation (DTS vs SMTH)**
- DTS: "五行之气有偏全" (流通论)
- SMTH: "金有金之种，木有木之种" (种性论)
- Conflict evidence: ~3条

### 🟢 Low Priority (1 conflict)

**6. Yin-Yang Life/Death (DTS vs Folk Theory)**
- Folk: "阳生阴死，阳死阴生"
- DTS: "阴阳同生同死"
- Conflict evidence: ~2条
- Resolution: DTS view already mainstream

---

## Key Documents

| Document | Path | Size |
|----------|------|------|
| Conflict List | `docs/conflict_dispute_list.md` | 7.7KB |
| Research Compilation | `docs/conflict_dispute_research.md` | 9.3KB |
| Depth Analysis | `docs/depth_conflict_analysis.md` | 16.8KB |
| Quality Report v4 | `docs/evidence_quality_report_v4.md` | 4.1KB |
| Concept Comparison | `docs/cross_classical_concept_comparison.md` | 15KB |

---

## Evidence File Structure

```json
{
  "evidence_id": "E-DTS-101-001",
  "classic_id": "di_tian_sui",
  "classic_name": "滴天髓",
  "evidence_type": "101",
  "classical_theme": "三元本体论",
  "original_text": "...",
  "conditions": ["三元存在时", "五行流通时"],
  "trigger_conditions": ["通用情况"],
  "scope": {...},
  "provenance": {...}
}
```

---

*For arbitration reference - all evidence is in collection/preparation phase, not yet in production pipeline*
