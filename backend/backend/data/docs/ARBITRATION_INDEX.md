# 五经证据 - 提交给GPT裁决的完整索引

**Repository**: https://github.com/ZQMMING/wisdom  
**Branch**: main  
**Latest Commit**: ea1f2bd - "Add arbitration summary for GPT review"

---

## 📊 证据总量

| 经典 | 证据数 | 占比 | 冲突相关 |
|------|--------|------|----------|
| 滴天髓 (DTS) | 44 | 3.1% | ~63条 |
| 穷通宝鉴 (QTBJ) | 1,233 | 87.3% | ~50条 |
| 渊海子平 (YHZP) | 117 | 8.3% | ~25条 |
| 三命通会 (SMTH) | 8 | 0.6% | ~3条 |
| 子平真诠 (PZZQ) | 10 | 0.7% | ~23条 |
| **总计** | **1,412** | **100%** | **~164条** |

---

## 🎯 质量指标（已全部达标）

| 指标 | 覆盖率 | 目标线 | 状态 |
|------|--------|--------|------|
| Theme | 100% | ≥95% | ✅ |
| Conditions | **99.9%** | ≥80% | ✅ |
| Context | 98.4% | ≥90% | ✅ |
| Source Tracing | 100% | 100% | ✅ |
| **综合评分** | **99.5/100** | ≥85 | ✅ |

---

## ⚔️ 六大争议点（待裁决）

### 🔴 高优先级

#### 1. 旺衰优先 vs 调候优先
**涉及**: DTS vs QTBJ (~50条证据)

| 维度 | 滴天髓立场 | 穷通宝鉴立场 |
|------|------------|--------------|
| 核心命题 | 旺衰为根本 | 调候为优先 |
| 用神取向 | 日主旺衰决定 | 季节气候决定 |
| 关键原文 | "须观日主之衰旺，察生时之浅深" | "秋月之木...尤喜水土以相滋" |

**冲突场景**: 甲日申月 → DTS用神水木 vs QTBJ用神火

**建议裁决**: 制定层级规则：先旺衰后调候

---

#### 2. 取用神标准差异
**涉及**: PZZQ vs YHZP (~15条证据)

| 维度 | 子平真诠立场 | 渊海子平立场 |
|------|--------------|--------------|
| 核心原则 | "用神专求月令" | 日主状态优先 |
| 用神来源 | 月令透干 | 综合判断 |
| 方法论 | 格局成败救应 | 身强身弱案例 |

**冲突场景**: 甲日酉月 → PZZQ看相神配合 vs YHZP看日主强弱

**建议裁决**: 月令定格局，日主定强弱

---

#### 3. 方法论分歧：简化 vs 精细
**涉及**: DTS vs PZZQ (~8条证据)

| 维度 | 滴天髓立场 | 子平真诠立场 |
|------|------------|--------------|
| 学术定位 | 批判反思派 | 精细发展派 |
| 核心主张 | 回归用神本质 | 完善格局体系 |
| 对奇格态度 | "荒唐取用，非关命理" | "成败救应，精细辨析" |

**建议裁决**: 批判性吸收 — 分层处理

---

### 🟡 中优先级

#### 4. 格局判定标准
**涉及**: PZZQ vs YHZP (~10条证据)

- PZZQ: 二分法（正格/杂格）
- YHZP: 三分法（清格/浊格/混合格）

**建议裁决**: 创建第三分类方案

---

#### 5. 五行流通观分歧
**涉及**: DTS vs SMTH (~3条证据)

- DTS: "五行之气有偏全"（流通论）
- SMTH: "金有金之种，木有木之种"（种性论）

**建议裁决**: 实证检验后裁决

---

### 🟢 低优先级

#### 6. 阴阳生死观分歧
**涉及**: DTS vs 世俗说 (~2条证据)

- 世俗: "阳生阴死，阳死阴生"
- DTS: "阴阳同生同死"（已被广泛接受）

**建议裁决**: 采用滴天髓修正说

---

## 📁 关键文件索引

### 分析报告

| 文件 | 路径 | 大小 | 用途 |
|------|------|------|------|
| 争议列表 | `docs/conflict_dispute_list.md` | 7.7KB | 6大争议点概览 |
| 资料汇编 | `docs/conflict_dispute_research.md` | 9.3KB | 原文证据+调和方案 |
| 深度分析 | `docs/depth_conflict_analysis.md` | 16.8KB | 理论/实践/条件三维分析 |
| 质量报告v4 | `docs/evidence_quality_report_v4.md` | 4.1KB | 质量指标验证 |
| 概念比对 | `docs/cross_classical_concept_comparison.md` | 15KB | 10个概念逐条对照 |
| 条件矩阵 | `docs/condition_analysis_matrix.md` | 9KB | 63个条件分布统计 |
| 裁决摘要 | `docs/ARBITRATION_SUMMARY.md` | 3.5KB | 本文件 |

### 数据文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 关系矩阵 | `data/evidence_relationship_matrix.json` | 互补/冲突关系数据 |
| 条件矩阵 | `data/condition_analysis_matrix.json` | 65KB条件分析数据 |
| 原典合并 | `data/classics/original/*_merged.json` | 五经段落合并数据 |

### 证据目录结构

```
data/evidence/
├── di_tian_sui/          # 44条
├── qiong_tong_bao_jian/  # 1,233条
├── yuan_hai_zi_ping/     # 117条
├── san_ming_tong_hui/    # 8条
└── ziping_zhenquan/      # 10条
```

---

## 🔗 直接访问链接

| 资源 | URL |
|------|-----|
| GitHub仓库 | https://github.com/ZQMMING/wisdom |
| 最新commit | https://github.com/ZQMMING/wisdom/commit/ea1f2bd |
| 争议列表 | https://github.com/ZQMMING/wisdom/blob/main/docs/conflict_dispute_list.md |
| 资料汇编 | https://github.com/ZQMMING/wisdom/blob/main/docs/conflict_dispute_research.md |
| 深度分析 | https://github.com/ZQMMING/wisdom/blob/main/docs/depth_conflict_analysis.md |
| 裁决摘要 | https://github.com/ZQMMING/wisdom/blob/main/docs/ARBITRATION_SUMMARY.md |

---

## 📋 裁决请求

**当前阶段**: 收集/整理/校对阶段（未进入生产流程）

**请求GPT裁决事项**:
1. 六大争议点的最终裁决意见
2. 建议的调和方案优先级
3. 是否需要补充更多证据
4. 是否可以进入下一阶段

**注意**: 所有证据均为收集校对阶段产出，未经过生产流程裁决，仅供研究参考。
