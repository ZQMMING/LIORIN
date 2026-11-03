# 盲派辨 Evidence Corpus 架构方案

**日期**: 2026-09-02  
**项目**: 顺天 · 东方时间智能系统  
**状态**: 待裁决

---

## 一、问题背景

Phase 3（五经证据归一化）已冻结（commit 14cf35e），下一步是建立盲派辨 Evidence Corpus。

### 核心认知

盲派不能像五经那样直接指定一本"盲派经典"作为唯一原典。原因：

1. 现代公开可系统整理的"盲派做功体系"主要载体是**段建业整理、总结的体系**
2. 而非《渊海子平》《三命通会》等子平古籍
3. 段建业体系是对郝金阳、夏仲奇等盲师断例及其所接触的盲派材料进行整理、提炼、系统化
4. 段建业相关课程资料明确说明：他形成的完整体系是对郝金阳所学内容和遗留断例进行系统总结，其中部分理论是他自己提炼出来的，**并非直接传承**
5. 《夏仲奇卜命遗例集》显示：夏仲奇使用过一种称为《十排歌》的盲师传承口诀，但该口诀本身**没有完整公开流传下来**
6. 存在"盲派究竟是独立传统还是子平体系的现代整理"的争论

### 决策原则

顺天最安全的做法是**不替历史争论裁定血统**，而是严格按 **Evidence Provenance 分层**。

---

## 二、分层架构（已确认）

```text
盲派辨 Evidence Corpus
│
├── A. 传承证据层
│     ├── 夏仲奇遗例
│     ├── 郝金阳相关遗例
│     └── 盲师口诀 / 十排歌等
│
├── B. 段氏系统化理论层
│     ├── 《盲派初级命理学》（段建业）← 第一优先
│     ├── 《段氏理象学——盲派命理研究》（段建业）← 第二优先
│     ├── 《盲派命理》修订版（段建业）← 第三优先
│     └── 相关课程/讲义
│
├── C. 命例验证层
│     ├── 夏仲奇断例
│     ├── 郝金阳断例
│     └── 段氏整理案例
│
└── D. 后世二次整理层
      ├── 网络讲义
      ├── 教程
      └── 后人总结
      （不进入 Authority Evidence）
```

**A ≠ B ≠ C ≠ D。**

尤其 D 绝对不能直接进入 Authority Evidence。

---

## 三、盲派核心 Signal 架构

### 子平体系（已冻结）

```text
月令 → 旺衰 → 格局/用神 → 判断
```

Signal: `STRENGTH`, `CLIMATE`, `PATTERN`, `TEN_GOD`, `FIVE_ELEMENTS`

### 盲派体系（待定义）

```text
宾主 → 体用 → 结构关系 → 做功 → 功神/废神 → 效率/层次 → 象/断事
```

**建议 Signal Schema**:

```json
{
  "BLIND_STRUCTURE": {
    "status": "CLASSICAL_AUTHORITY",
    "description": "盲派做功体系（宾主/体用/做功/效率/象法）",
    "sub_signals": {
      "GUEST_HOST": "宾主关系（日主/年月 vs 时柱）",
      "BODY_USE": "体用关系（体神/用神）",
      "WORK_RELATION": "做功关系（主客/动静/得失）",
      "WORK_TYPE": "做功方式（刑冲克穿合墓等）",
      "WORK_ACTOR": "功神（参与做功的神）",
      "WORK_TARGET": "功靶（做功的目标）",
      "WORK_EFFICIENCY": "做功效率（功的大小）",
      "POWER_PARTY": "势/党（气势/阵营）",
      "EMPTY_USELESS": "虚/废（无用之神）",
      "IMAGE": "象法（干支意象）",
      "YING_QI": "应期（应事时间）"
    }
  }
}
```

**关键约束**:
- 盲派 Signal **不能** 复用 `STRENGTH` / `CLIMATE` / `PATTERN`
- 必须建立独立 Signal 命名空间
- 与五经 Signal 形成互补关系（非替代）

---

## 四、核心研究对象（12项）

按优先级排序：

1. **宾主** — 日主（主） vs 年月时柱（宾）
2. **体用** — 体神（自身） vs 用神（他者）
3. **功神 / 废神** — 参与做功 vs 不参与做功
4. **做功** — 结构关系的核心操作
5. **做功方式** — 刑、冲、克、穿、合、墓等
6. **制 / 化 / 生泄 / 合 / 墓 / 复合** — 做功技法
7. **功的大小与效率** — 做功等级
8. **势 / 党** — 气势阵营
9. **虚实** — 干支虚实状态
10. **干支配置** — 天干地支的组合关系
11. **象法** — 干支意象与类象
12. **应期** — 应事时间判断

**"做功"作为盲派核心辨识轴**，不是普通的一个 Signal。

---

## 五、执行计划

### Phase A: Evidence Corpus v1（当前阶段）

**目标**: 建立盲派辨 Evidence Corpus，不做 Signal Mapping

**任务**:
1. 从B层资料提取 Evidence（第一优先：《盲派初级命理学》）
2. 建立盲派 Evidence Schema（独立于五经 Schema）
3. 存储位置：`data/evidence/blind_seg/`
4. 不修改生产代码

**产出**:
```
data/evidence/blind_seg/
├── E-BLIND-001-001.json  (宾主)
├── E-BLIND-002-001.json  (体用)
├── E-BLIND-003-001.json  (功神/废神)
├── E-BLIND-004-001.json  (做功)
├── E-BLIND-005-001.json  (做功方式)
└── ...
```

### Phase B: Signal Schema 定义（待裁决后）

**目标**: 定义盲派独立 Signal 命名空间

**任务**:
1. 创建 `data/feature_signal_mapping_blind.json`
2. 定义 BLIND_STRUCTURE 及 sub_signals
3. 不修改现有五经 Signal 映射

### Phase C: Evidence → Signal Mapping（待 Phase B 完成后）

**目标**: 将盲派 Evidence 映射到盲派 Signal

**约束**: 不修改 Phase 3 已冻结的五经 Mapping

---

## 六、待裁决问题

### Q1. 资料获取方式

盲派辨资料是否有：
- [ ] 本地文件（如PDF/Word）？请提供路径
- [ ] 在线资源（需浏览器爬取）？
- [ ] 混合（部分本地+部分在线）？

### Q2. Evidence Schema

是否需要：
- [ ] 复用五经 Schema（authority_type = "BLIND_SEGMENT"）？
- [ ] 新建盲派专用 Schema？
- [ ] 扩展字段（如增加 work_type、efficiency_level 等）？

### Q3. 提取范围

《盲派初级命理学》：
- [ ] 全量提取（所有章节）？
- [ ] 核心章节提取（只提取"做功"相关章节）？
- [ ] 主题索引提取（按12项研究对象分别提取）？

### Q4. 产出位置

盲派辨 Evidence：
- [ ] 同级目录：`data/evidence/blind_seg/`（与五经并列）？
- [ ] 独立目录：`data/evidence/blind_evidence/`？
- [ ] 新版本：创建 `blind_evidence_corpus/` 项目？

---

## 七、风险与约束

### 风险

1. **资料完整性**: 段建业体系是否完整公开？是否存在未公开内容？
2. **传承真实性**: 段建业体系与原始盲派的真实性关系如何界定？
3. **Signal 独立性**: 盲派 Signal 与五经 Signal 的边界如何保持清晰？

### 约束

1. **不进入 Production Admission**: 当前阶段仅限于 Evidence Collection
2. **不修改五经体系**: Phase 3 已冻结，不得修改
3. **不建立单一 yongshen**: 保持五经的 STRENGTH + CLIMATE + PATTERN 分层架构
4. **不比较五大体系**: 互补不比较，各自产生 Semantic Signal

---

## 八、GitHub 链接

| 资源 | Commit |
|------|--------|
| Phase 3 冻结 | https://github.com/ZQMMING/wisdom/commit/14cf35e |
| 五经证据归一化 | https://github.com/ZQMMING/wisdom/commit/87f15e2 |
| 语义归一化报告 | https://github.com/ZQMMING/wisdom/blob/main/docs/SEMANTIC_NORMALIZATION_FINAL_REPORT_V7.md |
| 本架构方案 | https://github.com/ZQMMING/wisdom/blob/main/docs/blind_segment_architecture.md |

---

*本方案已提交裁决，等待确认后执行 Phase A*
