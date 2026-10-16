"""shuntian_kb 只读 KB Reader(C4,Codex 交接 Phase A)。

Codex 读库契约(05_API_DATA_CONTRACT.md)的 Python 入口:连接 `shuntian_kb`,
只读查询 rules / evidence / passages / golden_cases 四张主表。

**只读纪律(红线):** 本模块**只含 SELECT**,没有任何 UPDATE / INSERT / DELETE。
写路径一律走 backend/scripts/shuntian_* 建库/导入/登记脚本。
> 若日后有人想在本模块加写方法——先读契约 §4 的 Codex 红线,再掂量。

用法:
    from tongshu.db import kb_reader

    rules = kb_reader.query_rules(["ZPZ-101", "ZPZ-102"])
    evidence = kb_reader.query_evidence(["E-ZPZ-101-001"])
    passages = kb_reader.query_passages(["PZZQ_031_P001"])
    active_cases = kb_reader.query_golden_cases(active_only=True)   # GOLDEN-001..020
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Sequence

import psycopg2
import psycopg2.extensions
import psycopg2.extras

from tongshu.db.config import get_kb_dsn

KB_DB = "shuntian_kb"


def kb_dsn() -> str:
    """指向 shuntian_kb 的 DSN。"""
    return get_kb_dsn()


@contextmanager
def with_kb_conn() -> Iterator[psycopg2.extensions.connection]:
    """打开 shuntian_kb 连接;退出即关闭(短连接,读多写少场景足够)。

    用法:
        with with_kb_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    """
    conn = psycopg2.connect(kb_dsn())
    try:
        with conn.cursor() as _cur:
            _cur.execute("SELECT current_database()")
            _db = _cur.fetchone()[0]
            if _db != KB_DB:
                raise RuntimeError(f"Expected {KB_DB}, connected to {_db}")
        yield conn
    finally:
        conn.close()


def _fetch_rows(query: str, params: tuple = ()) -> list[dict]:
    """执行只读 SELECT,返回 list[dict](列名→值)。"""
    with with_kb_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]


def query_rules(rule_ids: Sequence[str]) -> list[dict]:
    """按 rule_id 批量取规则(空输入返回 [] 而非报错)。"""
    if not rule_ids:
        return []
    return _fetch_rows(
        "SELECT * FROM rules WHERE rule_id = ANY(%s) ORDER BY rule_id",
        (list(rule_ids),),
    )


def query_evidence(evidence_ids: Sequence[str]) -> list[dict]:
    """按 evidence_id 批量取证据。"""
    if not evidence_ids:
        return []
    return _fetch_rows(
        "SELECT * FROM evidence WHERE evidence_id = ANY(%s) ORDER BY evidence_id",
        (list(evidence_ids),),
    )


def query_passages(passage_ids: Sequence[str]) -> list[dict]:
    """按 passage_id 批量取 passage。"""
    if not passage_ids:
        return []
    return _fetch_rows(
        "SELECT * FROM passages WHERE passage_id = ANY(%s) ORDER BY passage_id",
        (list(passage_ids),),
    )


def query_golden_cases(active_only: bool = True) -> list[dict]:
    """取黄金案例。

    active_only=True(默认) → 仅 `verification_status='active'`(回归基线 GOLDEN-001..020,
    可执行基线,见契约 §2.4);False → 全部(含 GOLD_EXP_/GOLD_MAP_ draft)。
    """
    if active_only:
        return _fetch_rows(
            "SELECT * FROM golden_cases WHERE verification_status = 'active' "
            "ORDER BY case_id"
        )
    return _fetch_rows("SELECT * FROM golden_cases ORDER BY case_id")
