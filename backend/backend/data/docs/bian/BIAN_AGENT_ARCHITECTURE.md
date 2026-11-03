# 五部经典辨证代理（Bian Agents）架构设计

> 设计时间: 2026-09-01
> 目标: 为五部经典各分配专属辨证代理，全面建立"辨"层证据体系

---

## 一、核心定位

**"算 → 辨 → 解"架构中，"辨"是核心枢纽：**
- "算"层提供 Canonical Fact（日主、月令、藏干、十神等）
- "辨"层从五部经典中提取证据（Evidence），建立辨证结论
- "解"层将证据转化为断言（Assertion）和解释

**五部经典各自承担不同观察维度，不投票、不平均，互补而非比较。**

---

## 二、五代理分工

| 代理 | 经典 | 缩写 | 核心辨证目标 | 关键Observation |
|------|------|------|-------------|-----------------|
| 滴天髓辨证代理 | 滴天髓 | DTS_BI | 旺衰气势 | 得令/得地/得势/受制/泄耗/气势流通 |
| 子平真诠辨证代理 | 子平真诠 | PZZQ_BI | 格局成败 | 月令格局/用神喜忌/成败救应/十干得地 |
| 穷通宝鉴辨证代理 | 穷通宝鉴 | QTBJ_BI | 调候寒暖 | 日干×月令二维调候/寒暖燥湿/五行时令 |
| 三命通会辨证代理 | 三命通会 | SMTH_BI | 关系转化 | 刑冲合害/神煞/生克制化/组合条件 |
| 渊海子平辨证代理 | 渊海子平 | YHZP_BI | 基础语义 | 月令重要性/格局从月令出/十神基础/生克 |

---

## 三、每代理职责

### 3.1 输入
- `CanonicalState`（算层输出）
- 五部经典原文数据（`data/classics/original/`）
- 断语库（`data/classics/original/` 下的断语）

### 3.2 核心工作
1. **证据提取**：从原典中提取与当前命局相关的证据
2. **原典验证**：每条证据必须标注出处（经典名 + 篇章 + 原文上下文）
3. **授权分级**：AUTHORIZED / PARTIAL / NOT_AUTHORIZED
4. **Evidence产出**：按 schema 生成标准化 Evidence 文件

### 3.3 输出
- `data/evidence/E-{CLASSIC}-{ID}.json` — 证据文件
- `docs/bian/{CLASSIC}_evidence_taxonomy.md` — 辨证规则谱系
- `docs/bian/{CLASSIC}_verification_report.md` — 验证报告

---

## 四、Evidence Schema

每条 Evidence 必须包含：

```json
{
  "evidence_id": "E-{CLASSIC}-{SEQ}-001",
  "classic_id": "di_tian_sui",
  "evidence_type": "SEASONAL_SUPPORT",
  "direction": "SUPPORT",
  "canonical_source": {
    "classic": "滴天髓",
    "chapter": "通神论·衰旺",
    "original_text": "...",
    "source_locator": "滴天髓·通神论·衰旺第X段"
  },
  "verification_status": "AUTHORIZED",
  "authorization_level": "CONFIRMED",
  "mapping_to_canonical": {
    "day_master": "甲",
    "month_branch": "寅",
    "relation": "GROWTH_STAGE = BUILDING"
  },
  "created_at": "2026-09-01T00:00:00Z"
}
```

---

## 五、执行优先级

### Phase 1（立即执行）
- 建立五代理基础框架
- DTS_BI 旺衰证据链（得令/得地/得势/受制/泄耗）
- PZZQ_BI 格局证据链（月令格局/用神/成败）

### Phase 2（下一轮）
- QTBJ_BI 调候证据链
- SMTH_BI 关系转化证据链
- YHZP_BI 基础语义证据链

### Phase 3（后续）
- 跨经典证据对比
- Evidence Combination 规则
- 整体辨证状态形成

---

## 六、核心原则

1. **原典授权 ≠ 条件成立 ≠ 断事结论授权** — 三层永久分离
2. **推理强度 ≤ 原典授权强度** — PARTIAL 只能输出 QUALIFIED
3. **每条证据必须可溯源** — 引用必须标注经典名 + 篇章 + 原文
4. **互补不比较** — 五代理独立输出，不投票不平均
5. **不为提高通过率强行授权** — 找不到原文就标 INSUFFICIENT_SOURCE

---

*本设计文档是五部经典辨证代理架构的起点。执行中需严格遵循"算→辨→解"分层原则，不得用后层成果证明前层正确。*
