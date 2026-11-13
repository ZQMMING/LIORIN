"""个人档案独立迁移入口。不会由服务启动或旧 migrate() 自动调用。"""
from __future__ import annotations

from pathlib import Path

import psycopg2

SCHEMA_PATH = Path(__file__).with_name("profile_0001.sql")


def migrate_profile(dsn: str, *, schema_path: Path = SCHEMA_PATH) -> None:
    """显式执行个人档案迁移；调用者负责先验收目标库和备份。"""
    if not dsn:
        raise ValueError("explicit DSN required")
    sql = schema_path.read_text(encoding="utf-8")
    conn = psycopg2.connect(dsn)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    finally:
        conn.close()
