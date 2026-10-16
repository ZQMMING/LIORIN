"""DB runtime 连接配置(Phase C 平台层, task #57 落地)。

V1 运行时保持内存/无 DB(冻结契约 11_DATABASE_SCHEMA.sql 声明 Phase 0 不参与运行);
本模块是平台层接入 PostgreSQL 的**可选**能力。默认 DSN 指向本地开发库 `otcg`,
可通过环境变量 `OTC_G_DATABASE_URL` 覆盖。

纪律:凭据永远不硬编码进代码/commit。本地开发默认 `postgres/postgres`(仅本机
Postgres 17 安装默认),生产/CI 一律用 `OTC_G_DATABASE_URL` 注入。
"""

from __future__ import annotations

import os

DEFAULT_DSN = "postgresql://postgres:postgres@127.0.0.1:5432/otcg"
DEFAULT_KB_DSN = "postgresql://postgres:postgres@127.0.0.1:5432/shuntian_kb"

# 库名(init 时从 postgres 维护库创建)
DB_NAME = "otcg"
KB_DB_NAME = "shuntian_kb"


def get_dsn() -> str:
    """目标库 DSN:环境变量优先,缺省本地 otcg。"""
    return os.environ.get("OTC_G_DATABASE_URL", DEFAULT_DSN)


def get_kb_dsn() -> str:
    """知识库 shuntian_kb DSN:环境变量 SHUNTIAN_KB_DATABASE_URL 优先,缺省本地构造。"""
    return os.environ.get("SHUNTIAN_KB_DATABASE_URL", DEFAULT_KB_DSN)


def get_admin_dsn() -> str:
    """维护库(postgres)DSN,用于 `init` 创建 otcg 数据库。"""
    override = os.environ.get("OTC_G_ADMIN_DATABASE_URL")
    if override:
        return override
    return get_dsn().rsplit("/", 1)[0] + "/postgres"


def db_available(dsn: str | None = None, timeout: int = 3) -> tuple[bool, str]:
    """探测目标库是否可达(短超时)。返回 (ok, err)。"""
    try:
        import psycopg2

        conn = psycopg2.connect(dsn or get_dsn(), connect_timeout=timeout)
        conn.close()
        return True, ""
    except Exception as exc:  # noqa: BLE001 — 探测要吞掉任意连接异常
        return False, str(exc)[:200]
