"""冻结契约 DDL 幂等落地(migrate)。

把 docs/v36/11_DATABASE_SCHEMA.sql(V4.0 契约,28 表)应用到目标库。
以 migration_versions 表做版本跟踪:
  - 首次:单事务内整文件执行 → 记录版本;失败回滚 → 干净重试。
  - 重跑:已记录 → 跳过(幂等)。
  - 版本缺但库已有旧契约表(users 存在)→ 幂等重放新 DDL 增量升级:
    文件内全部 CREATE TABLE IF NOT EXISTS + ALTER IF EXISTS 归一,
    既建表跳过、新表落地、约束/列升级,再记录新版本(替代 V3.6 的
    「收养即跳过」——那会让 7 张新表永不落地)。
  - 其余异常表 → 重放(会报 CREATE TABLE 已存在,由操作者处理)。
"""

from __future__ import annotations

from pathlib import Path

import psycopg2

from .config import get_dsn
from .init_auth import init_auth_schema  # B-09 R2: chain auth schema after frozen DDL

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "docs" / "v36" / "11_DATABASE_SCHEMA.sql"
MIGRATION_VERSION = "20260818_phase0_v40_28tables"
SCHEMA_NAME = "otcg_db_schema"
SCHEMA_VERSION = "2.0.0"


def _record(cur, description: str) -> None:
    """记录迁移版本 + 回写 schema_versions(幂等)。"""
    cur.execute(
        "INSERT INTO migration_versions (version, description) VALUES (%s, %s)",
        (MIGRATION_VERSION, description),
    )
    cur.execute(
        "INSERT INTO schema_versions (schema_name, version, frozen_at) "
        "VALUES (%s, %s, now()) "
        "ON CONFLICT (schema_name) DO UPDATE SET version=EXCLUDED.version",
        (SCHEMA_NAME, SCHEMA_VERSION),
    )


def _statements(sql: str) -> list[str]:
    """把 DDL 按分号切成独立语句(本文件无跨行字符串字面量,纯 DDL,安全)。"""
    buf: list[str] = []
    stmts: list[str] = []
    for raw in sql.splitlines():
        line = raw.strip()
        if line.startswith("--") or not line:
            continue
        buf.append(raw)
        if buf and "".join(buf).strip().endswith(";"):
            stmts.append("\n".join(buf))
            buf = []
    if buf:
        stmts.append("\n".join(buf))
    return [s for s in stmts if s.strip()]


def _table_exists(cur, table: str) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name=%s",
        (table,),
    )
    return cur.fetchone() is not None


def migrate(dsn: str | None = None, schema_path: Path | None = None) -> dict:
    """应用冻结 DDL + auth 链(B-09 R2)。

冻结契约落地后,自动链式调用 init_auth_schema() 让
0002_auth.sql 的 5 张表 + 版本号 20260823_B09_auth_v1 一起被
记录到 migration_versions,避免 version 号躺在永远不会被执行的
脚本里(ARBITRATION_BATCH3 E2/R3 的裁决)。

返回 {applied: bool, version, reason, auth_chain: dict}。
"""
    dsn = dsn or get_dsn()
    sql = (schema_path or SCHEMA_PATH).read_text(encoding="utf-8")
    conn = psycopg2.connect(dsn)
    try:
        cur = conn.cursor()
        if _table_exists(cur, "migration_versions"):
            cur.execute(
                "SELECT 1 FROM migration_versions WHERE version=%s",
                (MIGRATION_VERSION,),
            )
            if cur.fetchone():
                return {
                    "applied": False,
                    "version": MIGRATION_VERSION,
                    "reason": "already applied",
                }
            # 版本表存在但无本版本,且库已有旧契约表 → 幂等重放新 DDL 增量升级
            # 到 28 表(IF NOT EXISTS 跳过既建表、ALTER 归一新约束/列),再记录版本。
            if _table_exists(cur, "users"):
                cur.execute(sql)
                _record(cur, "OTC-G V4.0 §29 28-table contract (upgraded from V3.6 21-table)")
                conn.commit()
                return {
                    "applied": True,
                    "version": MIGRATION_VERSION,
                    "reason": "upgraded (28-table contract replayed idempotently)",
                    "auth_chain": init_auth_schema(dsn),
                }
        # 首次:单事务整文件执行(任一句失败 → 整体回滚 → 无部分状态)
        cur.execute(sql)
        if not _table_exists(cur, "migration_versions"):
            # 防 DDL 变更导致跟踪表缺失(契约文件理应创建,此处为兜底)
            cur.execute(
                "CREATE TABLE migration_versions ("
                " id UUID PRIMARY KEY DEFAULT gen_random_uuid(),"
                " version TEXT NOT NULL UNIQUE,"
                " description TEXT NOT NULL,"
                " applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
        _record(cur, "OTC-G V4.0 §29 28-table contract DDL")
        conn.commit()
        auth_chain = init_auth_schema(dsn)
        return {
            "applied": True, "version": MIGRATION_VERSION,
            "reason": "applied",
            "auth_chain": auth_chain,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
