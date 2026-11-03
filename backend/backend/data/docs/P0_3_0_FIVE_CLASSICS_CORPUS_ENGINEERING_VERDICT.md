# P0-3.0 五经 Corpus 辨证工程化 — 工程执行完成报告

> **本文件不是裁决文件。** 工程已完成并推送到 GitHub（commit `2584e6a`），
> **裁决由 AI 审计者（GPT）在 GitHub 上审阅 commit 后作出**。
> 本报告只陈述事实：做了什么、验证结果、需要审计者裁决的问题清单。

**执行日期**: 2026-08-30
**执行目标**: 利用 FOR-BAZI 五经 Corpus 做候选检索，以现有原书资料/Evidence 做交叉验证，最终把五经辨证工程化
**执行原则**: 先做 Corpus Adapter + Corpus Audit + Evidence Candidate Retrieval，不继续堆旺衰规则

---

## 一、执行背景（事实）

### 1.1 执行前状态

- ✅ CanonicalState 数据结构（facts/relations/classical_states/qualifiers/unresolved_reasons/provenance）
- ✅ CanonicalStateProducer（从 BaziChart 生产 CanonicalState）
- ✅ DTS 旺衰 10 个 Primitive（DTS-WS-001~010，基于《滴天髓阐微·十七、衰旺》原典）
- ✅ DTS 旺衰 6 条关系规则（REL-001~006）
- ✅ Signal 适配器（基础层 Signal → CanonicalSignal）
- ✅ 旧评分路径调用图审计 + 迁移计划

### 1.2 待解决的工程缺口

1. **证据来源单一**：此前主要依赖《滴天髓阐微·十七、衰旺》单一章节
2. **五经未系统利用**：FOR-BAZI 五经 Corpus（滴天髓/子平真诠/穷通宝鉴/三命通会/渊海子平）已结构化，但未接入辨证工程
3. **候选检索能力缺失**：没有工具能根据辨证概念（如"得时""有根""调候"）从五经中自动检索候选证据
4. **交叉验证能力缺失**：没有机制能将 FOR-BAZI Corpus 的候选证据与现有原书资料（完整原典补充/五部经典完整数据）做交叉验证

### 1.3 执行方向

**不是**继续"凭经验写身强身弱算法"。

**而是**：
1. 建立 Corpus Adapter — 统一读取五经 JSON，提供标准化访问接口
2. 建立 Corpus Audit — 审计五经数据的完整性、质量、覆盖度
3. 建立 Evidence Candidate Retrieval — 根据辨证概念从五经中自动检索候选证据
4. 建立 Cross-Validation — 将候选证据与现有原书资料做交叉验证（**本轮未执行，待下轮**）
5. 最终将五经辨证工程化 — 每一条辨证规则都有五经候选证据 + 交叉验证结果（**远期，未执行**）

---

## 二、本轮已完成的工程（commit `2584e6a`）

### 阶段1：Corpus Adapter — ✅ 已完成并验证

**新增文件**: `src/tongshu/corpus/adapter.py`

- `FiveClassicsCorpusAdapter`：统一读取 FOR-BAZI 五经 JSON，提供标准化访问接口
- 数据结构：`ClassicEntry`（classic_id/classic_name/entry_id/category/key/original_text/interpretation/likes_dislikes/source/tags）
- 查询接口：按经典/分类/标签/关键词检索
- **验证结果**：5部经典 / 376条条目 / 16个分类 / 96个标签；"得时"检索5条、"有根"检索4条、"调候"检索123条

### 阶段2：Corpus Audit — ✅ 已完成

**新增文件**: `docs/P0_3_0_CORPUS_AUDIT_REPORT.md`

审计发现（事实）：
- 数据格式结构化程度高（统一 JSON）
- 原文保留完整（每条都有原文）
- 标签系统完善（96个标签）
- **各经典条目数不均衡**：渊海子平187条 vs 滴天髓19条
- **辨证概念覆盖度中等**：调候/十神/格局高，得时/有根/气势中等
- **原文准确性未系统验证**（需与原始原典交叉验证）
- **辨证组合规则缺失**（Corpus 主要是概念性条目）

### 阶段3：Evidence Candidate Retrieval — ✅ 已完成并验证

**新增文件**: `src/tongshu/corpus/retrieval.py`

- `EvidenceCandidateRetriever`：根据辨证概念从五经中自动检索候选证据
- 18个核心辨证概念→关键词映射表（得时/有根/有气/气势/生扶/制泄/调候/用神/格局/成败救应/十神/刑冲合害/旺衰/月令/通根/干多不如根重/得时不旺/失时不弱）
- 多维度匹配权重：标签精确(0.4) > 原文(0.3) > 关键词(0.15) > 分类(0.1) > 解析(0.05)
- 候选证据标准化输出，含匹配度/匹配原因/授权提示
- **验证结果**：得时最高匹配度0.833，有根最高0.900，跨经典检索正常

### 本轮未执行（待下轮）

- ⏳ 阶段4：Cross-Validation（将 FOR-BAZI 原文与原始原典做交叉验证）
- 🔴 阶段5：五经辨证规则工程化（远期，必须基于前四阶段）

---

## 三、验证结果汇总（事实，非裁决）

| 验证项 | 结果 |
|---|---|
| Corpus Adapter 加载 | 5经典/376条/16分类/96标签 |
| "得时" 概念检索 | 5条候选，最高匹配0.833（滴天髓·月令提纲论） |
| "有根" 概念检索 | 5条候选，最高匹配0.900（三命通会·强弱_得地） |
| "调候" 概念检索 | 123条候选（穷通宝鉴120条为主） |
| "调候" 限定经典检索 | 跨经典过滤正常 |
| 批量概念检索 | 18个概念均可检索 |

---

## 四、待 AI 审计者（GPT）裁决的问题清单

以下问题请审计者基于 GitHub 上的 commit（`2584e6a`）及实际代码审阅后裁决：

1. **Corpus Adapter 的数据结构设计**是否合理？`ClassicEntry` 的字段划分是否满足后续辨证工程需求？
2. **检索匹配权重**（标签0.4/原文0.3/关键词0.15/分类0.1/解析0.05）是否合理？是否存在过度依赖现代"解析"字段的风险？
3. **候选证据的授权提示**（HIGH_MATCH/MEDIUM_MATCH/LOW_MATCH/WEAK_MATCH）是否足够保守？是否会误导后续把候选证据直接当原典授权？
4. **18个辨证概念→关键词映射表**是否有遗漏的核心概念？关键词设计是否合理？
5. **Corpus Audit 发现的覆盖度缺口**（渊海子平187条 vs 滴天髓19条；原文准确性未验证）是否需要在进入阶段4前先行补足？
6. **下一步是否应执行阶段4（Cross-Validation）**？如果是，优先级和抽样策略如何？
7. 本轮工程是否违反任何项目治理原则（如"候选证据≠原典授权"、"合理≠原典证明"）？

---

## 五、项目治理原则（持续生效，供审计者核对）

1. **算准→辨准→解准** — 算层是地基，算错则全错
2. **FROZEN≠PROVEN CORRECT** — 代码冻结不等于计算正确
3. **P6-CALC 仍是最高优先级** — 计算完整性审计不能停
4. **禁止五行计分→强弱** — 禁止 strength_score / root_score
5. **原典授权≠条件成立≠断事结论授权** — 三层必须分离
6. **整体旺衰保持 UNRESOLVED** — 除非有明确原典授权的综合规则
7. **合理≠原典证明** — FOR-BAZI 的解析是现代解释，不能作为原典授权
8. **候选证据≠原典授权** — 候选证据必须经过交叉验证才能升级授权等级

---

## 六、本文件状态

- **本文件是**: 工程执行完成报告 + 待裁决请求
- **本文件不是**: 裁决文件
- **裁决人**: AI 审计者（GPT），基于 GitHub commit `2584e6a`
- **裁决入口**: 请审计者直接审阅 commit `2584e6a` 及其涉及的文件：
  - `src/tongshu/corpus/adapter.py`
  - `src/tongshu/corpus/retrieval.py`
  - `docs/P0_3_0_CORPUS_AUDIT_REPORT.md`
  - `scripts/_verify_corpus_adapter.py`
  - `scripts/_verify_retriever.py`
