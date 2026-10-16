"""运行时写路径 DAO(Phase C 平台层原语)。

V1 运行时仍为内存(不读写 DB);本模块是**可选的**落库通道,供平台层接入时
逐字段落盘 calculation_runs / rule_results / expressions / audit_runs /
audit_findings / api_requests。所有函数接受显式 conn(调用方持有事务边界),
以便测试用事务回滚隔离。

不自动接线到 pipeline —— 接线是 Phase C 平台层决策,不是本轮范围。
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


def record_calculation_run(
    conn,
    *,
    birth_profile_id: str | None,
    analysis_date: date,
    theme: str,
    request_id: str,
    trace_id: str | None,
    canonical_id: str | None,
    status: str = "ok",
    source: str = "engine",
    model_id: str | None,
    prompt_version: str | None,
    versions: dict | None = None,
) -> str:
    """插入一次命盘计算记录,返回 run_id。"""
    versions = versions or {}
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO calculation_runs"
        " (birth_profile_id, analysis_date, theme, request_id, trace_id, canonical_id,"
        "  status, source, model_id, prompt_version, calculation_version,"
        "  knowledge_version, mapping_version, translation_version)"
        " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        (
            birth_profile_id,
            analysis_date,
            theme,
            request_id,
            trace_id,
            canonical_id,
            status,
            source,
            model_id,
            prompt_version,
            versions.get("calculation", "1.0.0"),
            versions.get("knowledge", "1.0.0"),
            versions.get("mapping", "0.1.0"),
            versions.get("translation", "0.1.0"),
        ),
    )
    run_id = cur.fetchone()[0]
    return str(run_id)


def record_rule_results(conn, run_id: str, rule_results: list[dict]) -> None:
    """批量写入规则匹配明细。每项: {rule_id, signal_id?, matched, payload?}。"""
    cur = conn.cursor()
    for r in rule_results:
        cur.execute(
            "INSERT INTO rule_results (run_id, rule_id, signal_id, matched, payload)"
            " VALUES (%s,%s,%s,%s,%s)",
            (
                run_id,
                r["rule_id"],
                r.get("signal_id"),
                bool(r["matched"]),
                json.dumps(r.get("payload", {}), ensure_ascii=False),
            ),
        )


def record_expression(
    conn,
    run_id: str,
    *,
    source: str,
    text: str,
    covered_claim_ids: list[str] | None = None,
    self_check: dict | None = None,
    validation_passed: bool | None = None,
) -> None:
    """写入渲染产物(模板回退或 LLM 输出)。"""
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expressions"
        " (run_id, source, text, covered_claim_ids, self_check, validation_passed)"
        " VALUES (%s,%s,%s,%s,%s,%s)",
        (
            run_id,
            source,
            text,
            json.dumps(covered_claim_ids or [], ensure_ascii=False),
            json.dumps(self_check, ensure_ascii=False) if self_check is not None else None,
            validation_passed,
        ),
    )


def record_audit(
    conn,
    run_id: str,
    *,
    request_id: str,
    trace_id: str | None,
    document_id: str | None,
    validation_passed: bool | None,
    gates: dict | None = None,
    findings: list[dict] | None = None,
) -> str:
    """写入审计主记录 + 明细。返回 audit_run_id。"""
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO audit_runs"
        " (run_id, request_id, trace_id, document_id, validation_passed, gates)"
        " VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
        (
            run_id,
            request_id,
            trace_id,
            document_id,
            validation_passed,
            json.dumps(gates or {}, ensure_ascii=False),
        ),
    )
    audit_run_id = cur.fetchone()[0]
    for f in findings or []:
        cur.execute(
            "INSERT INTO audit_findings"
            " (audit_run_id, layer, finding_code, message, payload)"
            " VALUES (%s,%s,%s,%s,%s)",
            (
                audit_run_id,
                f["layer"],
                f["finding_code"],
                f.get("message"),
                json.dumps(f.get("payload", {}), ensure_ascii=False),
            ),
        )
    return str(audit_run_id)


def record_api_request(
    conn,
    *,
    request_id: str,
    trace_id: str | None,
    method: str,
    path: str,
    status_code: int | None,
    error_code: str | None,
    latency_ms: int | None,
) -> None:
    """写入一次 API 请求审计(§30 api_requests,遥测/迁移观察)。"""
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO api_requests"
        " (request_id, trace_id, method, path, status_code, error_code, latency_ms)"
        " VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (request_id, trace_id, method, path, status_code, error_code, latency_ms),
    )


def recent_runs(conn, limit: int = 10) -> list[dict]:
    """最近命盘计算记录(desc by created_at)。"""
    cur = conn.cursor()
    cur.execute(
        "SELECT id, analysis_date, theme, request_id, source, status, model_id"
        " FROM calculation_runs ORDER BY created_at DESC LIMIT %s",
        (limit,),
    )
    cols = ["run_id", "analysis_date", "theme", "request_id", "source", "status", "model_id"]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
