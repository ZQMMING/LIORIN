# DB SNAPSHOT · STEP 6 中期基线（只读对账）

> **日期**: 2026-08-23 · **执行**: Claude（STEP 6 收尾）
> **原则**: 全程只读，零写入。与 STEP 0 (DB_SNAPSHOT_20260823.md) 逐行对账。
> **脚本**: `_db_snapshot.py`（otcg）+ `_db_kb.py`（shuntian_kb，autocommit 防止缺表中断事务）

---

## 一、运行时库 otcg（backend 默认 DSN）

```text
DSN                = postgresql://postgres:postgres@127.0.0.1:5432/otcg
TABLE_COUNT        = 28
TOTAL_ROWS         = 293  (pg_stat_user_tables 估算值)
POPULATED          = 7 / 28  (估算值，受 autovacuum 影响)

── 精确 COUNT(*) 对账 ──
rules              = 55  (active=30, draft=15, validated=10)
evidence           = 52
mappings           = 10
books              = 6
passages           = 110
classical_concepts = 0
principles         = 0
rule_versions      = 55
mapping_versions   = 10
migration_versions = 2
schema_versions    = 1
```

### 与 STEP 0 对账

| 指标 | STEP 0 (052aebb) | STEP 6 (8f3b081) | 一致 |
|------|-------------------|-------------------|------|
| rules (exact COUNT) | 55 | 55 | YES |
| evidence (exact COUNT) | 52 | 52 | YES |
| mappings (exact COUNT) | 10 | 10 | YES |
| books | 6 | 6 | YES |
| passages | 110 | 110 | YES |
| classical_concepts | 0 | 0 | YES |
| principles | 0 | 0 | YES |
| rule_versions | 55 | 55 | YES |
| mapping_versions | 10 | 10 | YES |
| migration_versions | 2 | 2 | YES |
| schema_versions | 1 | 1 | YES |
| TABLE_COUNT | 28 | 28 | YES |
| TOTAL_ROWS (估算) | 301 | 293 | 估算波动* |
| POPULATED (估算) | 9/28 | 7/28 | 估算波动* |

> *TOTAL_ROWS / POPULATED 来自 `pg_stat_user_tables.n_live_tup`，为 autovacuum 维护的估算值，
> 非精确计数。STEP 0 → STEP 6 期间无任何写库操作（P0 修复均为代码层），
> 所有精确 COUNT(*) 结果完全一致。

---

## 二、知识库 shuntian_kb（只读巡检）

```text
DSN                = postgresql://postgres:postgres@127.0.0.1:5432/shuntian_kb
TABLE_COUNT        = 115
TOTAL_ROWS         = 1887  (pg_stat_user_tables 估算值)
POPULATED          = 51 / 115

── 精确 COUNT(*) ──
rules              = 86
evidence           = 71
passages           = 55
principles         = 36
```

### 与 STEP 0 对账

| 指标 | STEP 0 | STEP 6 | 一致 |
|------|--------|--------|------|
| TABLE_COUNT | 115 | 115 | YES |
| TOTAL_ROWS (估算) | 1887 | 1887 | YES |
| POPULATED | 51/115 | 51/115 | YES |
| rules | 86 | 86 | YES |
| evidence | 71 | 71 | YES |
| passages | 55 | 55 | YES |
| principles | 36 | 36 | YES |

---

## 三、对账结论

**otcg 核心三表 rules/evidence/mappings = 55/52/10，与 STEP 0 完全一致。**
shuntian_kb 115表/1887行，与 STEP 0 完全一致。
双库在 STEP 0 → STEP 6 期间零写入，数据状态未变。

> 注：shuntian_kb 无 `mappings` / `books` 表（与 otcg schema 不同），
> STEP 0 已记录此架构差异。本次巡检以 autocommit 模式逐表查询，避免缺表中断事务。
