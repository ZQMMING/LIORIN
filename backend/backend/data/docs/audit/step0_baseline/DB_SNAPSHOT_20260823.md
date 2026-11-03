# DB SNAPSHOT · STEP 0.2 数据库事实基线

> **日期**: 2026-08-23 · **执行**: Hermes（STEP 0 修正版作业）
> **原则**: 只记录事实与 provenance，不证明谁"正确"。全程只读，零写入。

---

## 一、重大发现：服务器上存在 **两个数据库**，矛盾初步解开

`127.0.0.1:5432` 上并存（与 `01_ERD_SCHEMA.md` 第15行记载一致："shuntian_kb 与运行时 otcg 并存，互不干扰"）：

| 数据库 | 角色 | 表数 | 总行数 | 已填充 |
|---|---|---|---|---|
| **otcg** | 运行时库（backend 默认 DSN 指向） | 28 | 301 | 9/28 |
| **shuntian_kb** | 知识库（2026-08-20 建库） | **115** | **1887** | 51/115 |

**结论性事实**：所谓「71表/577行」既不是 otcg 现状，也不完全等于 shuntian_kb 现状
——它是 **2026-08-20 建库时点的历史快照数字**。此后 shuntian_kb 继续演进至 115 表/1887 行。
三套数字对应三个不同对象/时点，**不构成同一事物的矛盾**。

---

## 二、DB FACT SHEET

### 2.1 运行时库 otcg（backend 实际连接）

```text
DSN              = postgresql://postgres:postgres@127.0.0.1:5432/otcg (config.py 默认)
TABLE_COUNT      = 28
TOTAL_ROWS       = 301
POPULATED        = 9 / 28
RULES_TOTAL      = 55   (active=30, draft=15, validated=10) ← BUG-06A 恢复后基线 ✅
EVIDENCE_COUNT   = 52   ← BUG-06A 基线 ✅
MAPPING_COUNT    = 10   ← BUG-06A 基线 ✅
BOOKS            = 6
PASSAGES         = 110
CLASSICAL_CONCEPTS = 0
PRINCIPLES         = 0
SCHEMA_VERSION   = 'otcg_db_schema' v2.0.0 (2026-08-18)
MIGRATION_HEAD   = 20260818_phase0_v40_28tables ("OTC-G V4.0 §29 28-table contract")
                   （migration_versions 共2条：v36_contract → v40_28tables）
GIT_COMMIT       = 052aebb981a18e668ab90fdc1ca65ae6ed88abce
DB_FILE_HASH     = N/A (PostgreSQL 服务端库，非文件型；如需哈希须 pg_dump 后对 dump 计 hash —— 本步未做，避免任何写放大)
```

行数分布（非零表）：passages 110 / rule_versions 55 / rules 55 / evidence 52 /
mapping_versions 10 / mappings 10 / books 6 / migration_versions 2 / schema_versions 1。

### 2.2 知识库 shuntian_kb（只读巡检）

```text
TABLE_COUNT      = 115
TOTAL_ROWS       = 1887
POPULATED        = 51 / 115
rules=86, evidence=71, passages=55, principles=36（其余为各域知识表）
访问方式         = 只读会话 (readonly=True)，本次零写入
```

---

## 三、「71 表 / 577 行」PROVENANCE 追溯

| 证据 | 内容 | 位置 |
|---|---|---|
| AUDIT_REPORT_V1.0.md:23 | "71 表已建, 577 行数据, H1/H2/H3 audit 待裁定" | docs/audit/AUDIT_REPORT_V1.0.md |
| AUDIT_REPORT_V1.0.md:120 | "**shuntian_kb (Postgres 17, 71 表, 577 行)** ← 知识库" | 同上 |
| 01_ERD_SCHEMA.md:4,17 | shuntian_kb 建库完成 2026-08-20；迁移版本 `20260820_shuntian_v1_twelvedomains_71tables_sc_nullable`（5 版已应用） | docs/shuntian/01_ERD_SCHEMA.md |
| 02_MIGRATION.md:33-36 | 5 版迁移明细（含 `..._71tables`、`..._sc_nullable`），时间戳 2026-08-20 20:27~20:32 | docs/shuntian/02_MIGRATION.md |
| 09_DATA_DICTIONARY.md:6 | "审计对象：71 张现有表，不新增、不删除、不重命名" | docs/shuntian/09_DATA_DICTIONARY.md |

### PROVENANCE STATUS 裁定

```text
CURRENT_DB (otcg 28表/301行)          = VERIFIED   （实测 + migration_versions 自证）
BUG-06A 基线 (55 rules/52 evi/10 map) = VERIFIED   （实测与 BUG06A_FINAL.md 完全吻合）
历史声明 "71表/577行"                  = PARTIALLY_VERIFIED
  ├─ 来源已定位：2026-08-20 shuntian_kb 建库时点快照（文档链一致）
  └─ 未决事项：该时点的 dump/备份 artifact 未找到；且 shuntian_kb 当前已是 115表/1887行，
     "577行" 数字已不代表任何现存状态 → 仅作历史记录，不得称为 current baseline
shuntian_kb 当前态 (115表/1887行)      = VERIFIED   （只读实测）
```

---

## 四、STEP 0.2 禁令遵守确认

✅ 未迁移 28→71　✅ 未恢复/删除任何表　✅ 未修改 migration
✅ 未补数据　✅ 未运行写 DB 的 migration　✅ 未为对齐基线改 schema
✅ shuntian_kb 以 readonly 会话巡检　✅ 零写入

---

## 五、留给 STEP 1 的裁决输入（不在本步裁定）

1. otcg(28) 与 shuntian_kb(115) 双库并存的架构定位是否维持（ERD 文档称"互不干扰"，但 A12 需审计 Agent 是否曾混用两库连接）
2. shuntian_kb 中 rules=86/evidence=71 与 otcg 的 55/52 数量差异的来源（知识库先行 vs 越界数据残留）
3. classical_concepts/principles 在 otcg 为空、在 kb 有值——P1 缺口清单需按双库口径重写
4. "71表/577行"正式降级为 HISTORICAL_SNAPSHOT_20260820

**GATE 进度: 2/8** — Git captured ✅ / Dirty accounted ✅ / DB actual snapshot ✅ / 71·577 provenance ✅
