# 五经证据项目 — 完整快照

**时间**: 2026-09-01 22:40
**状态**: 等待下一步指示

---

## 核心数据

### 结构化证据 (1,412条)
| 经典 | 代码 | 证据数 | 覆盖领域 |
|------|------|--------|----------|
| 穷通宝鉴 | QTBJ | 1,233 | 调候寒暖辨证 |
| 渊海子平 | YHZP | 117 | 基础语义辨证 |
| 滴天髓 | DTS | 44 | 旺衰气势辨证 |
| 子平真诠 | PZZQ | 10 | 格局成败辨证 |
| 三命通会 | SMTH | 8 | 关系转化辨证 |

### 原典数据 (7,039段落, 1.1M字符)
```
DTS: 719段落, 269K字符 (覆盖率82.7%)
PZZQ: 446段落, 72K字符 (覆盖率91.7%)
QTBJ: 1,556段落, 105K字符 (重复率1.22%)
SMTH: 1,846段落, 461K字符 (覆盖率33.3%主题)
YHZP: 2,472段落, 202K字符 (覆盖率8.9%篇目)
```

---

## 产出文件

```
data/evidence/
├── di_tian_sui/     (44条)
├── qiong_tong_bao_jian/     (1,233条)
├── yuan_hai_zi_ping/        (117条)
├── ziping_zhenquan/         (10条)
├── san_ming_tong_hui/       (8条)
└── _unified_summary.json

docs/
├── five_classics_evidence_contract.md   # 证据合同规范
├── cross_classical_concept_comparison.md  # 15KB 同概念比对
├── condition_analysis_matrix.md          # 9KB 条件分析
├── conflict_research_supplement.md       # 6KB 矛盾研究
└── SNAPSHOT_2026-09-01.md               # 本文件

data/
└── evidence_relationship_matrix.json     # 5.5KB 关系矩阵
```

---

## 交叉验证发现

### 3组互补关系
1. 滴天髓 ↔ 穷通宝鉴 (旺衰+调候互补)
2. 子平真诠 ↔ 渊海子平 (格局+基础互补)
3. 三命通会 ↔ 其他 (关系转化补充)

### 3组冲突关系
1. 旺衰优先 vs 调候优先 (DTS vs QTBJ)
2. 取用神标准差异 (PZZQ vs YHZP)
3. 格局判定标准 (PZZQ vs YHZP)

---

## 已知问题

| 问题 | 严重程度 | 影响 |
|------|----------|------|
| YHZP覆盖率8.9% | 高 | 缺123篇原文 |
| SMTH覆盖率33.3% | 中 | 缺10个主题 |
| QTBJ重复1.22% | 低 | 19组重复需去重 |
| PZZQ缺4篇 | 低 | 喜忌支干/印取运/偏官取运/杂格取运 |

---

## 待决策选项

1. **补充原文数据** — 提高YHZP、SMTH覆盖率
2. **去重处理** — 清理QTBJ重复数据
3. **Assertion Mapping** — 进入断言生成阶段
4. **等待GPT裁决** — Production Admission第八轮pending
5. **其他方向**

---

## 当前等待

- GPT第八轮裁决 (commit `6835643`)
- 用户下一步指示

---

*快照创建: 2026-09-01 22:40*
*总证据数: 1,412条 | 格式验证: 100%通过*
