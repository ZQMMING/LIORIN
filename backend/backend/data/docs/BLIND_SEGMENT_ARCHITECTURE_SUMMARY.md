# 盲派辨 Evidence Corpus 架构方案 - 精简版

**日期**: 2026-09-02  
**状态**: 待裁决

---

## 核心问题

盲派不能像五经那样指定单一"经典"作为原典。

现代公开可系统整理的盲派体系主要载体是**段建业整理、总结的体系**，而非《渊海子平》《三命通会》等子平古籍。

---

## 分层架构（已确认）

```
盲派辨 Evidence Corpus
│
├── A. 传承证据层（夏仲奇遗例、郝金阳遗例、盲师口诀）
├── B. 段氏系统化理论层（《盲派初级命理学》《段氏理象学》）← 第一优先
├── C. 命例验证层（断例）
└── D. 后世二次整理层（不进入 Authority Evidence）
```

**A ≠ B ≠ C ≠ D**

---

## 盲派核心 Signal 架构（待裁决）

### 建议 Schema

```json
{
  "BLIND_STRUCTURE": {
    "status": "CLASSICAL_AUTHORITY",
    "sub_signals": {
      "GUEST_HOST": "宾主关系",
      "BODY_USE": "体用关系",
      "WORK_RELATION": "做功关系",
      "WORK_TYPE": "做功方式（刑冲克穿合墓）",
      "WORK_ACTOR": "功神",
      "WORK_TARGET": "功靶",
      "WORK_EFFICIENCY": "做功效率",
      "POWER_PARTY": "势/党",
      "EMPTY_USELESS": "虚/废",
      "IMAGE": "象法",
      "YING_QI": "应期"
    }
  }
}
```

### 关键约束

- 盲派 Signal **不能** 复用 `STRENGTH` / `CLIMATE` / `PATTERN`
- 必须建立独立 Signal 命名空间
- 与五经 Signal 形成互补关系（非替代）

---

## 核心研究对象（12项）

1. 宾主  2. 体用  3. 功神/废神  4. 做功  
5. 做功方式  6. 制/化/生泄/合/墓/复合  
7. 功的大小与效率  8. 势/党  9. 虚实  
10. 干支配置  11. 象法  12. 应期

**"做功"作为盲派核心辨识轴**

---

## 执行计划

### Phase A: Evidence Corpus v1（当前阶段）

- [x] 建立盲派辨 Evidence Corpus
- [ ] 从B层资料提取 Evidence
- [ ] 建立盲派 Evidence Schema
- [ ] 存储位置：`data/evidence/blind_seg/`
- [ ] 不修改生产代码
- [ ] 不做 Signal Mapping

### Phase B: Signal Schema 定义（待裁决后）

### Phase C: Evidence → Signal Mapping（待 Phase B 完成后）

---

## 待裁决问题

### Q1. 资料获取方式
- [ ] 本地文件（请提供路径）
- [ ] 在线资源（需爬取）
- [ ] 混合

### Q2. Evidence Schema
- [ ] 复用五经 Schema（authority_type = "BLIND_SEGMENT"）
- [ ] 新建盲派专用 Schema
- [ ] 扩展字段（work_type、efficiency_level 等）

### Q3. 提取范围
- [ ] 全量提取
- [ ] 核心章节提取
- [ ] 主题索引提取（按12项分别提取）

### Q4. 产出位置
- [ ] 同级目录：`data/evidence/blind_seg/`
- [ ] 独立目录
- [ ] 新项目组

---

## 风险与约束

### 风险
1. 资料完整性：段建业体系是否完整公开？
2. 传承真实性：段建业体系与原始盲派的真实性关系如何界定？
3. Signal 独立性：盲派 Signal 与五经 Signal 的边界如何保持清晰？

### 约束
1. 不进入 Production Admission
2. 不修改五经体系（Phase 3 已冻结）
3. 不建立单一 yongshen
4. 不比较五大体系

---

## GitHub 链接

| 资源 | Commit |
|------|--------|
| Phase 3 冻结 | https://github.com/ZQMMING/wisdom/commit/14cf35e |
| 五经证据归一化 | https://github.com/ZQMMING/wisdom/commit/87f15e2 |
| 本架构方案 | https://github.com/ZQMMING/wisdom/blob/main/docs/BLIND_SEGMENT_ARCHITECTURE.md |

---

*本方案已提交裁决，等待确认后执行 Phase A*
