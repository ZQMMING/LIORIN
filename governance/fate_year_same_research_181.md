# PATCH-181 命运同见/岁运并临 原典语义只读（SEALED）

## 关键发现：伏吟定义跨书不统一
- 《神峰通考》：岁运与原命重复 → 伏吟
- 《三命通会·总论岁运》："岁运与日相对谓之返吟；岁运压日谓之伏吟"；"甲子流年又是甲子运谓之岁运并临"
- 三命另有：甲子生+甲子流年=真太岁；甲子日+甲子太岁=日年相并

因此 **same_branch → 伏吟=True 不是全局规则**，伏吟必须 source-specific。

## 工程分层（采纳）
```
178 原子Relation（五合/六合/六冲/三合三会/透清 + provenance）
181 Semantic Projection（结构标签, 不判吉凶）
├─ yun_year_same    → 岁运并临(流年干支==大运干支, 最干净)
├─ day_year_same    → 日年相并
├─ birth_year_same  → 真太岁
├─ yun_day_relation → 岁运压日 / 岁运与日相对
└─ 伏吟             → source-specific candidate label(非全局Boolean)
```

## 原典边界
- 《渊海子平》"岁运并临灾殃立至" vs 同书"有情者通/值生旺者未必为凶"
- 《神峰通考》此类论"大概而言""一不可拘"
- 结构 ≠ 作用 ≠ 强弱 ≠ 喜忌 ≠ 吉凶

## 代码现状核查
relation_178.py 无 same_branch/伏吟/并临代码（180纯文档）。万能伏吟规则未进工程。

## 下一刀(只读)
挖"岁运压日"结构：是流年+大运共同压日柱，还是分别"岁压日/运压日"？拆清则成原子Fact，拆不清保持semantic candidate。
