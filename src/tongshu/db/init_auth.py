# -*- coding: utf-8 -*-
"""B-09 R2 rework (ARBITRATION_BATCH3 R3 + R5):
This function is part of the migration chain. It is called by:
  - ``tongshu.db.migrate.migrate()`` after the frozen contract lands
    (production wiring; the auth version ``20260823_B09_auth_v1`` is
    recorded in the same conn.commit() as the V4.0 28-table DDL).
  - ``scripts.db_setup migrate`` and ``scripts.db_setup all``
    (Phase C tooling; the chain runs ``migrate()`` which calls us).
The previous STAGE-A docstring falsely claimed ``called by
db.init_schema()`` -- that function does not exist in ``tongshu.db``.
R3 of BATCH3 closes the gap so the version record no longer lives in a
dead-script limbo.
"""
from __future__ import annotations

from pathlib import Path
import psycopg2

from ..db.config import get_dsn

AUTH_MIGRATION_VERSION = "20260823_B09_auth_v1"
AUTH_MIGRATION_PATH = Path(__file__).resolve().parents[3] / "scripts" / "migrations" / "0002_auth.sql"  # B-09 R2: parents[3] reaches backend/, not parents[2] (src/)


def _table_exists(cur, table: str) -> bool:
    """Check if a table exists in the public schema."""
    cur.execute(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name=%s",
        (table,),
    )
    return cur.fetchone() is not None


def init_auth_schema(dsn: str | None = None) -> dict:
    """Apply 0002_auth.sql migration. Returns {applied, version, reason}.

    B-09 C12 rework (ARBITRATION_BATCH3_R2 C2): 0002_auth.sql ships with a
    UTF-8 BOM. ``utf-8-sig`` strips it so psycopg2 can parse the first
    statement. Without this, ``migrate()`` -> ``init_auth_schema()`` would
    SyntaxError at execute time.
    """
    dsn = dsn or get_dsn()
    auth_sql = AUTH_MIGRATION_PATH.read_text(encoding="utf-8-sig")  # B-09 C12: strip UTF-8 BOM if present
    
    conn = psycopg2.connect(dsn)
    try:
        cur = conn.cursor()
        
        # Check if migration_versions table exists
        if not _table_exists(cur, "migration_versions"):
            return {
                "applied": False,
                "version": AUTH_MIGRATION_VERSION,
                "reason": "migration_versions table not found, run 0001_schema first",
            }
        
        # Check if already applied
        cur.execute(
            "SELECT 1 FROM migration_versions WHERE version=%s",
            (AUTH_MIGRATION_VERSION,),
        )
        if cur.fetchone():
            return {
                "applied": False,
                "version": AUTH_MIGRATION_VERSION,
                "reason": "already applied",
            }
        
        # Execute the auth migration
        cur.execute(auth_sql)
        conn.commit()
        
        return {
            "applied": True,
            "version": AUTH_MIGRATION_VERSION,
            "reason": "applied",
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
