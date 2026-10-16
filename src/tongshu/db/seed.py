"""工程数据投影:rules / evidence / mappings JSON → DB(幂等)。

磁盘 JSON(backend/data/{rules,evidence,mappings}/*.json)是**唯一事实源**,
DB 只是可查询的投影(read path)。播种语义:
  - rules → rules(注册索引,单 layer)+ rule_versions(完整 payload 快照)。
  - evidence → books/passages(仅标题,author/dynasty 一律 NULL 不臆造)+ evidence。
  - mappings → mappings(注册索引)+ mapping_versions(payload 快照)。
全部 ON CONFLICT ... DO NOTHING / DO UPDATE,重复执行稳定。
"""

from __future__ import annotations

import glob
import hashlib
import json
from pathlib import Path

import psycopg2

from .config import get_dsn
from .migrate import MIGRATION_VERSION, SCHEMA_NAME, SCHEMA_VERSION
from tongshu.reasoning.matcher import rule_specificity

REPO = Path(__file__).resolve().parents[3]
RULE_DIR = REPO / "backend" / "data" / "rules"
EVIDENCE_DIR = REPO / "backend" / "data" / "evidence"
MAPPING_DIR = REPO / "backend" / "data" / "mappings"

# 已知典籍的稳定 book_id(P1-01 D1 与 Knowledge Base books.json 的 book_id 对齐,
# 不再对五部经典用哈希派生);其余 work 用哈希派生存 id。
BOOK_IDS = {
    "子平真诠": "ZIPING-ZHENQUAN",
    "滴天髓": "DITIANSUI",
    "穷通宝鉴": "QIONGTONG-BAOJIAN",
    "三命通会": "SANMING-TONGHUI",
    "渊海子平": "YUANHAI-ZIPING",
    "紫微斗数": "ZIWEI-DOUSHU",
}

# §30 rules.layer 白名单(与 11_DATABASE_SCHEMA.sql CHECK 一致)。
# EVENT_TOPIC: T4 断事规则层(MAR/HLT/CRR/EDU/WLT/HLT-3xx/HL),2026-08-26 激活后同步。
_LAYERS = {"BASELINE", "CYCLE_CONTEXT", "DAILY_ACTIVATION", "EVENT_TOPIC"}

# 强度轴差异(见 docs/v36/03_EVIDENCE_SYSTEM.md §3 诚实标注):本地 evidence_strength
# 用学术强度(primary|secondary|tertiary),§30 DB 契约 CHECK 只收 E0/E1/E2。
# 契约注释定义映射 E1=primary、E2=secondary/tertiary(本轴映射,非升级)。当前数据
# 40 secondary + 1 tertiary → 全部落 E2;无 primary。
_STRENGTH_TO_CONTRACT = {"primary": "E1", "secondary": "E2", "tertiary": "E2"}


def _book_id(work: str) -> str:
    if work in BOOK_IDS:
        return BOOK_IDS[work]
    return "WORK-" + hashlib.sha1(work.encode("utf-8")).hexdigest()[:8].upper()


def seed(dsn: str | None = None) -> dict:
    """执行投影,返回各表插入行数。前置:migrate 已应用。"""
    dsn = dsn or get_dsn()
    counts = {
        "rules": 0, "rule_versions": 0,
        "books": 0, "passages": 0, "evidence": 0,
        "mappings": 0, "mapping_versions": 0,
    }
    conn = psycopg2.connect(dsn)
    try:
        cur = conn.cursor()
        _ensure_tracking(cur)  # 幂等前提:版本记录存在

        # ---- rules + rule_versions ----
        for f in sorted(glob.glob(str(RULE_DIR / "*.json"))):
            with open(f, encoding="utf-8") as fh:
                rule = json.load(fh)
            rid = rule["rule_id"]
            layer = rule["applies_to_layers"][0]
            assert layer in _LAYERS, f"{rid}: 未知 layer {layer}"
            cur.execute(
                "INSERT INTO rules (rule_id, rule_type, source, layer, precedence,"
                " specificity, status, version, spec_decisions_ref)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                " ON CONFLICT (rule_id) DO UPDATE SET"
                " layer=EXCLUDED.layer, precedence=EXCLUDED.precedence,"
                " specificity=EXCLUDED.specificity, status=EXCLUDED.status,"
                " version=EXCLUDED.version, spec_decisions_ref=EXCLUDED.spec_decisions_ref,"
                " updated_at=now()",
                (
                    rid,
                    rule.get("rule_type"),
                    # source/spec_decisions_ref 是结构化字段(dict/list),入 TEXT 列需序列化
                    json.dumps(rule.get("source"), ensure_ascii=False),
                    layer,
                    rule.get("precedence", 0),
                    rule_specificity(rule),
                    rule.get("status", "active"),
                    rule.get("version", "1.0.0"),
                    json.dumps(rule.get("spec_decisions_ref"), ensure_ascii=False),
                ),
            )
            counts["rules"] += 1
            cur.execute(
                "INSERT INTO rule_versions (rule_id, version, payload, active)"
                " VALUES (%s,%s,%s,true)"
                " ON CONFLICT (rule_id, version) DO UPDATE SET payload=EXCLUDED.payload",
                (rid, rule.get("version", "1.0.0"), json.dumps(rule, ensure_ascii=False)),
            )
            counts["rule_versions"] += 1

        # ---- books + passages + evidence ----
        # passages.book_id 是 UUID FK → books(id);用业务码 book_id 查 UUID 后再引用。
        passage_by_key: dict[tuple, str] = {}  # (book_uuid, location, content) -> passage_id
        book_uuid_by_work: dict[str, object] = {}
        for f in sorted(glob.glob(str(EVIDENCE_DIR / "*.json"))):
            with open(f, encoding="utf-8") as fh:
                ev = json.load(fh)
            eid = ev["evidence_id"]
            loc = ev.get("source_locator") or {}
            work = loc.get("work")
            passage_id = None
            if work and work not in ("工程种子",):
                bid = _book_id(work)
                cur.execute(
                    "INSERT INTO books (book_id, title) VALUES (%s,%s)"
                    " ON CONFLICT (book_id) DO NOTHING",
                    (bid, work),
                )
                if work not in book_uuid_by_work:
                    cur.execute("SELECT id FROM books WHERE book_id=%s", (bid,))
                    book_uuid_by_work[work] = cur.fetchone()[0]
                book_uuid = book_uuid_by_work[work]
                location = " ".join(
                    x for x in (loc.get("chapter"), loc.get("page")) if x
                )
                content = (ev.get("citation") or {}).get("original_text", "")
                key = (book_uuid, location, content)
                if key not in passage_by_key:
                    pid = "P-" + hashlib.sha1(json.dumps(key, ensure_ascii=False).encode("utf-8")).hexdigest()[:16].upper()
                    cur.execute(
                        "INSERT INTO passages (passage_id, book_id, location, content)"
                        " VALUES (%s,%s,%s,%s) ON CONFLICT (passage_id) DO NOTHING",
                        (pid, book_uuid, location, content),
                    )
                    # evidence.passage_id 是 UUID FK → passages(id),取真实 UUID 存映射
                    cur.execute("SELECT id FROM passages WHERE passage_id=%s", (pid,))
                    passage_by_key[key] = cur.fetchone()[0]
                    counts["passages"] += 1
                passage_id = passage_by_key[key]
            cur.execute(
                "INSERT INTO evidence (evidence_id, passage_id, rule_ids,"
                " evidence_strength, modern_paraphrase)"
                " VALUES (%s,%s,%s,%s,%s)"
                " ON CONFLICT (evidence_id) DO UPDATE SET"
                " passage_id=EXCLUDED.passage_id, rule_ids=EXCLUDED.rule_ids,"
                " evidence_strength=EXCLUDED.evidence_strength",
                (
                    eid,
                    passage_id,
                    json.dumps(ev.get("rule_refs", []), ensure_ascii=False),
                    _STRENGTH_TO_CONTRACT.get(
                        ev.get("evidence_strength", "E2"), ev.get("evidence_strength", "E2")
                    ),
                    ev.get("modern_paraphrase"),
                ),
            )
            counts["evidence"] += 1
        counts["books"] = len(book_uuid_by_work)

        # ---- mappings + mapping_versions ----
        for f in sorted(glob.glob(str(MAPPING_DIR / "*.json"))):
            with open(f, encoding="utf-8") as fh:
                m = json.load(fh)
            mid = m["mapping_id"]
            cur.execute(
                "INSERT INTO mappings (mapping_id, source_concept, translation_type,"
                " modern_theme, allowed_actions, forbidden_actions, status, version)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
                " ON CONFLICT (mapping_id) DO UPDATE SET"
                " source_concept=EXCLUDED.source_concept,"
                " modern_theme=EXCLUDED.modern_theme, status=EXCLUDED.status,"
                " version=EXCLUDED.version, updated_at=now()",
                (
                    mid,
                    m.get("source_term"),
                    "semantic",
                    m.get("modern_theme"),
                    "[]",
                    "[]",
                    m.get("status", "draft"),
                    m.get("version", "0.1.0"),
                ),
            )
            counts["mappings"] += 1
            cur.execute(
                "INSERT INTO mapping_versions (mapping_id, version, payload, active)"
                " VALUES (%s,%s,%s,true)"
                " ON CONFLICT (mapping_id, version) DO UPDATE SET payload=EXCLUDED.payload",
                (mid, m.get("version", "0.1.0"), json.dumps(m, ensure_ascii=False)),
            )
            counts["mapping_versions"] += 1

        conn.commit()
        return counts
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_tracking(cur) -> None:
    """幂等前提:迁移已应用(否则播种无法落地到表)。"""
    cur.execute("SELECT 1 FROM migration_versions WHERE version=%s", (MIGRATION_VERSION,))
    if cur.fetchone() is None:
        raise RuntimeError(
            f"DB 未迁移(缺 {MIGRATION_VERSION});先运行 migrate 再 seed。"
        )
    cur.execute(
        "INSERT INTO schema_versions (schema_name, version, frozen_at) VALUES (%s,%s,now()) "
        "ON CONFLICT (schema_name) DO NOTHING",
        (SCHEMA_NAME, SCHEMA_VERSION),
    )
