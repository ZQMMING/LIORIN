"""FastAPI application for OTC-G (personal reading + today card).

V3.6 endpoint layout (§25-26):
  - POST /v1/calculate    — deterministic computation SIR only (no render)
  - POST /v1/daily-guide  — full pipeline (compute + render + validate)
  - GET  /v1/today        — today card (guest: public tier; authed: +personal)
  - POST /api/reading     — DEPRECATED alias of /v1/daily-guide (Sunset 2027-08-18)
  - GET  /api/today       — DEPRECATED alias of /v1/today (Sunset 2027-08-18)

The reading endpoint drives the real TONGSHUPipeline (engines -> reasoning ->
canonical -> render -> validation) and returns the rendered text plus a summary
of the reasoning output. The renderer is env-gated (see render.clients): with
TONGSHU_LLM_API_KEY set it uses the real OpenAI-compatible client; otherwise
the deterministic Stub. A hard renderer failure degrades to Template Fallback
and NEVER surfaces as a 5xx (§24).

Observability (§36): TraceMiddleware injects X-Trace-ID / X-Process-Time-Ms and
records deprecated-path telemetry; renderer-only latency is exposed as
X-Render-Time-Ms (absent for /v1/calculate). Errors use the §32 envelope
{error:{code,message,request_id,trace_id,details}}.

B-09 STAGE-B (TASK_BATCH3_B09 §STAGE-B + B09_AUTH_PROPOSAL §7):
  - ``api/deps.py`` adds ``get_current_user_or_device`` (3-tier acceptor),
    ``get_current_user`` / ``get_current_device`` (required tier) and
    ``RateLimited(bucket, max, window, key)``.
  - ``TONGSHU_AUTH_ENFORCED`` (default false) controls enforcement; flag=false
    parses + tags ``X-Auth-Would-Deny`` but never rejects (per §Q9).
  - ``/v1/today`` and ``/api/today`` accept the optional 3-tier dep; the
    guest path returns the **public** layer only, an authenticated request
    gets an additional ``personal`` block (user_id / tier / device_id).
  - NFC routes stay 501 (per B-05 freeze, M2 rule) without auth.

Today-card calendar fields are computed deterministically (ganZhi, weekday, day,
plus the real 黄历 via huangli_engine / lunar_python — V4.0.1 §7.4 "Calendar 去
Mock"); the remaining editorial fields (greeting/theme/catalyst/dimensions/
time_window/hexagram/reasoning/cross_validation) are bridged from
web/data/today.json mock until a profile gate + content module exist. Provenance
is declared per field so the bridge is never silently mistaken for engine output.
"""

from __future__ import annotations
import dataclasses
import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..engines.bazi_engine import STEM_ELEMENT
from ..engines.time_resolver import TimeResolver
from ..pipeline import TONGSHUPipeline
from .deps import (
    IdentityContext,
    RATE_LIMIT_COMPUTE_USER,
    RATE_LIMIT_LIVENESS_GLOBAL,
    RATE_LIMIT_READ_PUBLIC,
    RATE_LIMIT_READ_USER,
    RATE_LIMIT_WRITE_USER,
    get_current_user,
    get_current_user_or_device,
    reset_rate_limit_buckets,
)
from .errors import (
    OTCGApiError,
    ErrorCode,
    otcg_api_error_handler,
    request_validation_error_handler,
    unhandled_exception_handler,
)
from .profile import ProfileState, ProfileStatus, require_personal_profile, resolve_profile
from .tracing import TraceMiddleware, deprecated_counts
from ..audit.gates import gate_block_counts

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]  # repo root = D:/shuntian
API_VERSION = "0.2.0"

# ---------------------------------------------------------------------- #
# Display maps for the today card (frontend contract, not engine semantics)
# ---------------------------------------------------------------------- #

STEM_CN = {
    "JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁", "WU": "戊",
    "JI": "己", "GENG": "庚", "XIN": "辛", "REN": "壬", "GUI": "癸",
}
BRANCH_CN = {
    "ZI": "子", "CHOU": "丑", "YIN": "寅", "MAO": "卯", "CHEN": "辰",
    "SI": "巳", "WU": "午", "WEI": "未", "SHEN": "申", "YOU": "酉",
    "XU": "戌", "HAI": "亥",
}
ELEMENT_COLOR = {
    "WOOD": "var(--c-mu)",
    "FIRE": "var(--c-huo)",
    "EARTH": "var(--c-tu)",
    "METAL": "var(--c-jin)",
    "WATER": "var(--c-shui)",
}
WEEKDAY_CN = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


class ReadingRequest(BaseModel):
    birth_date: str = Field(..., description="YYYY-MM-DD")
    hour: int = Field(..., ge=0, le=23, description="solar hour 0-23")
    gender: str = Field(..., pattern="^(male|female)$", description="Required per Profile Contract §1.2 (forbidden_default=true).")
    theme: str = Field("WORK", min_length=1)
    analysis_date: Optional[str] = Field(None, description="YYYY-MM-DD; default today")
    # P0-2 Profile Gate (§3.3): time-policy inputs. All optional for backward
    # compatibility; the gate requires timezone+location together for personal
    # computation (422 INSUFFICIENT_INPUT otherwise — never guess §6 L1).
    birth_minute: Optional[int] = Field(None, ge=0, le=59, description="birth minute 0-59; None = 时辰中点")
    timezone: Optional[str] = Field(None, description="IANA timezone, e.g. Asia/Shanghai; resolvable from location")
    calendar_system: Optional[str] = Field("solar", description="solar | lunar (lunar unsupported in V1)")
    location: Optional[str] = Field(None, description="location id / name from backend/data/locations.json")


class BirthTime(BaseModel):
    """Birth clock time: hour + optional minute (None = 时辰中点)."""
    hour: int = Field(..., ge=0, le=23, description="solar hour 0-23")
    minute: Optional[int] = Field(None, ge=0, le=59, description="birth minute 0-59; None = 时辰中点")


class ProfileRequest(BaseModel):
    """POST /v1/profile — §32 profile validation + time-policy receipt (stateless)."""
    birth_date: str = Field(..., description="YYYY-MM-DD")
    birth_time: BirthTime = Field(...)
    gender: str = Field(..., pattern="^(male|female)$", description="Required per Profile Contract §1.2 (forbidden_default=true).")
    timezone: Optional[str] = Field(None, description="IANA timezone; resolvable from location")
    calendar_system: Optional[str] = Field("solar", description="solar | lunar (lunar unsupported in V1)")
    location: Optional[str] = Field(None, description="location id / name from backend/data/locations.json — 出生地(Natal Calculation Context, 用于真太阳时→派生时区→排盘)")
    # ---- Spatial Layer Model (SPATIAL_LAYER_MODEL.md §3.2, 2026-08-25) ----
    # V1 Profile 冻结 5 项必填(用户口径 2026-08-25): 出生日期/出生时间/出生地/性别/当前生活城市。
    # current_location = 当前环境 Context:前端必填收集,后端仅记录,零计算影响。
    # 绝不进入 Profile Gate / CalculationContext / 排盘路径(Deterministic Core 冻结)。
    # 注:迁居历史/居住时长/过去城市/目标城市 明确不进 V1(SPATIAL_LAYER_MODEL.md §6)。
    current_location: Optional[str] = Field(None, description="[环境层·仅记录] 当前生活城市 id/name from locations.json; V1 必填收集但不参与排盘")
    analysis_date: Optional[str] = Field(None, description="YYYY-MM-DD; default today")


def _parse_dates(birth_date: str, analysis_date: Optional[str]) -> tuple[date, date]:
    """Parse request dates → (birth, analysis). Raises §32 INSUFFICIENT_INPUT."""
    try:
        y, m, d = (int(x) for x in birth_date.split("-"))
        birth = date(y, m, d)
    except ValueError as e:
        raise OTCGApiError(
            ErrorCode.INSUFFICIENT_INPUT,
            f"birth_date not a valid YYYY-MM-DD date: {birth_date!r}",
            details=[{"field": "birth_date", "reason": str(e)}],
        ) from e
    if analysis_date:
        try:
            y2, m2, d2 = (int(x) for x in analysis_date.split("-"))
            analysis = date(y2, m2, d2)
        except ValueError as e:
            raise OTCGApiError(
                ErrorCode.INSUFFICIENT_INPUT,
                f"analysis_date not a valid YYYY-MM-DD date: {analysis_date!r}",
                details=[{"field": "analysis_date", "reason": str(e)}],
            ) from e
    else:
        analysis = date.today()
    return birth, analysis


def _personal_block(identity: IdentityContext) -> dict[str, Any]:
    """Build the ``personal`` payload for an authenticated today-card.

    Returns a small, stable structure (user_id / tier / device_id / has_birth_info)
    so the frontend can switch on tier without re-decoding the access token.
    Always returns a NEW dict so the route can mutate safely.
    """
    block: dict[str, Any] = {"tier": "personal"}
    user_id = identity.effective_user_id
    if user_id is not None:
        block["user_id"] = user_id
    if identity.user is not None:
        block["token_version"] = identity.user.token_version
        block["has_birth_info"] = identity.user.has_birth_info
        block["is_new_user"] = identity.user.is_new_user
        # Bearer-only path: UserContext carries the device_id the access
        # token was issued for (itsdangerous payload). Surface it so the
        # frontend can tell user-personal vs anonymous-personal apart even
        # when X-Device-Token is not presented. device_type is omitted here
        # because it requires a DB lookup only available with DeviceContext.
        if identity.user.device_id and "device_id" not in block:
            block["device_id"] = identity.user.device_id
    if identity.device is not None:
        block["device_id"] = identity.device.device_id
        block["device_type"] = identity.device.device_type
    return block


# ---------------------------------------------------------------------- #
# App factory
# ---------------------------------------------------------------------- #


def create_app(repo_root: Path | None = None, db_ops: Any | None = None,
               profile_store: Any | None = None, local_qa: bool = False) -> FastAPI:
    """FastAPI app factory.

    B-09 R2 rework (ARBITRATION_BATCH3 R2): the very first call inside this
    factory is ``ensure_auth_ready()`` so every startup path (uvicorn --factory,
    TestClient(create_app()), direct import) takes the fail-fast gate. Tests
    that explicitly pop TONGSHU_AUTH_SECRET to assert the gate must run the
    assertion against ``create_app()`` itself rather than against module import.

    ``db_ops`` is the optional production db_ops adapter (PostgresAuthDB). When
    None (tests, dev mode without DB) the auth gateway stays uninitialised and
    the /v1/auth/* routes return 503 AUTH_UNAVAILABLE. When supplied, the gateway
    is wired exactly once via ``get_gateway_v2(db_ops)``.
    """
    # B-09 R2 rework (ARBITRATION_BATCH3 R2): fail-fast gate at the top of the
    # factory so no startup path can serve traffic without the secret set.
    from ..services.identity_gateway import ensure_auth_ready as _ensure_ready
    _ensure_ready()
    root = Path(repo_root) if repo_root else REPO_ROOT
    pipeline = TONGSHUPipeline.for_demo(root)
    # P0-2 Profile Gate:出生地点 registry + 真太阳时解析(确定性,零 AI)。
    time_resolver = TimeResolver()

    def _gate_personal(req: ReadingRequest) -> ProfileState:
        """§3.3 Profile Activation Gate for personal-computation endpoints.

        个人端点永远不允许降级公共链或猜测缺失出生输入:缺 timezone/location →
        422 INSUFFICIENT_INPUT(missing_fields);非法值(未知 location/坏时区/
        lunar)→ 400 INVALID_INPUT。
        """
        state = resolve_profile(
            timezone=req.timezone,
            calendar_system=req.calendar_system,
            location=req.location,
            time_resolver=time_resolver,
            gender=req.gender,
        )
        require_personal_profile(state)
        return state

    app = FastAPI(title="OTC-G API", version=API_VERSION, docs_url="/docs")

    origins = [o.strip() for o in os.environ.get("TONGSHU_CORS_ORIGINS", "*").split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TraceMiddleware)

    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(OTCGApiError, otcg_api_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.get("/health", dependencies=[Depends(RATE_LIMIT_LIVENESS_GLOBAL)])
    def health() -> dict:
        counts = deprecated_counts()
        gblocks = gate_block_counts()
        # B-09 STAGE-B: report flag visibility so operators can audit
        # enforcement from the liveness probe alone.
        from .deps import is_auth_enforced as as_flag

        return {
            "status": "ok",
            "renderer": "stub" if pipeline.renderer.is_stub else "llm",
            "model_id": pipeline.renderer.model_id,
            "version": API_VERSION,
            "deprecated_calls": sum(counts.values()),
            "deprecated_calls_by_path": counts,
            # V3.6 §63 G*_block_rate telemetry
            "gates_blocked": sum(gblocks.values()),
            "gates_blocked_by_gate": gblocks,
            "auth_enforced": as_flag(),
        }

    def _yi_block(result) -> dict | None:
        """B-01: 构造 yi 响应块；全 None 时返回 None（省略键而非输出 null）。"""
        block: dict[str, Any] = {}
        if result.heluo_result is not None:
            block["heluo"] = dataclasses.asdict(result.heluo_result)
        if result.yi_structure is not None:
            block["yi_structure"] = result.yi_structure.to_dict()
        if result.yi_interpretation is not None:
            block["yi_interpretation"] = result.yi_interpretation.to_dict()
        return block or None

    def _reading_response(result, analysis: date) -> dict:
        canon = result.canonical
        signals = canon.signals or {}
        _ca = canon.cross_analysis
        if hasattr(_ca, 'to_dict'):
            _ca = _ca.to_dict()
        elif not isinstance(_ca, dict):
            _ca = {}
        # M2 架构下 cross_analysis 无 status 字段；派生 cross_status 从 coverage 形态推断。
        # 规则：所有 ZI 引擎都有 evidence → ALIGNED；部分 → PARTIAL；空 → INSUFFICIENT。
        cross_status = _ca.get("status") if isinstance(_ca, dict) else None
        if cross_status is None and isinstance(_ca, dict):
            by_engine = _ca.get("by_engine", {}) or {}
            engines_with_ev = sum(
                1 for eng_set in by_engine.values()
                if (eng_set.get("evidence_ids") if isinstance(eng_set, dict) else [])
            )
            total = len(by_engine)
            total_assertions = 0
            cov = _ca.get("coverage", {}) or {}
            coverage = cov.get("coverage", {}) if isinstance(cov, dict) else {}
            for dom_idx in coverage.values():
                if isinstance(dom_idx, dict):
                    for ds_idx in dom_idx.values():
                        if isinstance(ds_idx, dict):
                            for eng_set in ds_idx.get("by_engine", {}).values():
                                if isinstance(eng_set, dict):
                                    total_assertions += len(eng_set.get("assertion_ids", []) or [])
            if engines_with_ev == 0 or total_assertions == 0:
                cross_status = "INSUFFICIENT"
            elif engines_with_ev < total:
                cross_status = "PARTIAL"
            else:
                cross_status = "ALIGNED"
        resp = {
            "request_id": result.audit_entry_id,
            "canonical_id": canon.canonical_id,
            "theme": canon.theme,
            "analysis_date": analysis.isoformat(),
            "cross_status": cross_status,
            "source": result.source,
            "engine_status": {"blind": getattr(result, "blind_status", "unknown")},
            "engine_rule_status": {"blind": "pending_review"},
            "validation_passed": result.validation_passed,
            "rendered_text": result.rendered_text,
            "signal_counts": {
                "BASELINE": len(signals.get("BASELINE", [])),
                "CYCLE_CONTEXT": len(signals.get("CYCLE_CONTEXT", [])),
                "DAILY_ACTIVATION": len(signals.get("DAILY_ACTIVATION", [])),
            },
            "atomic_claims": canon.atomic_claims or [],
            "audit_entry_id": result.audit_entry_id,
        }
        yi = _yi_block(result)
        if yi is not None:
            resp["yi"] = yi
        return resp

    # ------------------------------------------------------------------ #
    # V3.6 public endpoints
    # ------------------------------------------------------------------ #

    @app.post(
        "/v1/daily-guide",
        dependencies=[Depends(get_current_user), Depends(RATE_LIMIT_COMPUTE_USER)],
    )
    def daily_guide(
        req: ReadingRequest,
        response: Response,
        request: Request,
        identity: IdentityContext = Depends(get_current_user_or_device),
    ) -> dict:
        birth, analysis = _parse_dates(req.birth_date, req.analysis_date)
        profile = _gate_personal(req)
        result = pipeline.run(
            analysis_date=analysis,
            birth_date=(birth.year, birth.month, birth.day, req.hour),
            gender=req.gender,
            theme=req.theme,
            trace_id=getattr(request.state, "trace_id", None),
            timezone=profile.timezone,
            location=profile.location,
            birth_minute=req.birth_minute,
        )
        if result.render_elapsed_ms is not None:
            response.headers["X-Render-Time-Ms"] = f"{result.render_elapsed_ms:.0f}"
        return _reading_response(result, analysis)

    @app.post(
        "/v1/calculate",
        dependencies=[Depends(get_current_user), Depends(RATE_LIMIT_COMPUTE_USER)],
    )
    def calculate(
        req: ReadingRequest,
        response: Response,
        request: Request,
        identity: IdentityContext = Depends(get_current_user_or_device),
    ) -> dict:
        birth, analysis = _parse_dates(req.birth_date, req.analysis_date)
        profile = _gate_personal(req)
        result = pipeline.run(
            analysis_date=analysis,
            birth_date=(birth.year, birth.month, birth.day, req.hour),
            gender=req.gender,
            theme=req.theme,
            compute_only=True,
            trace_id=getattr(request.state, "trace_id", None),
            timezone=profile.timezone,
            location=profile.location,
            birth_minute=req.birth_minute,
        )
        canon = result.canonical.to_dict()
        # M2 兼容：cross_analysis 无 status 字段，注入派生 status
        ca = canon.get("cross_analysis") or {}
        if isinstance(ca, dict) and "status" not in ca:
            by_engine = ca.get("by_engine", {}) or {}
            engines_with_ev = sum(
                1 for eng_set in by_engine.values()
                if (eng_set.get("evidence_ids") if isinstance(eng_set, dict) else [])
            )
            total = len(by_engine)
            total_assertions = 0
            cov = ca.get("coverage", {}) or {}
            coverage = cov.get("coverage", {}) if isinstance(cov, dict) else {}
            for dom_idx in coverage.values():
                if isinstance(dom_idx, dict):
                    for ds_idx in dom_idx.values():
                        if isinstance(ds_idx, dict):
                            for eng_set in ds_idx.get("by_engine", {}).values():
                                if isinstance(eng_set, dict):
                                    total_assertions += len(eng_set.get("assertion_ids", []) or [])
            if engines_with_ev == 0 or total_assertions == 0:
                ca["status"] = "INSUFFICIENT"
            elif engines_with_ev < total:
                ca["status"] = "PARTIAL"
            else:
                ca["status"] = "ALIGNED"
        resp = {
            "canonical_id": canon["canonical_id"],
            "theme": canon["theme"],
            "analysis_date": analysis.isoformat(),
            "cross_analysis": ca,
            "signals": canon["signals"],
            "atomic_claims": canon["atomic_claims"],
            "exclusions": canon["exclusions"],
            "meta": canon.get("meta"),  # V3.6 §6 版本族 + 可观测性三件套
            "source": result.source,
            "engine_status": {"blind": getattr(result, "blind_status", "unknown")},
            "engine_rule_status": {"blind": "pending_review"},
        }
        yi = _yi_block(result)
        if yi is not None:
            resp["yi"] = yi
        return resp

    # ------------------------------------------------------------------ #
    # Local diagnostic route is deliberately unavailable unless explicitly enabled.
    if local_qa:
        @app.post("/v1/qa/engine")
        def qa_engine(req: ReadingRequest, request: Request) -> dict:
            host = request.client.host if request.client else None
            if host not in ("127.0.0.1", "::1", "testclient"):
                raise HTTPException(status_code=403, detail={"code": "LOCAL_ONLY", "message": "QA endpoint requires loopback"})
            birth, analysis = _parse_dates(req.birth_date, req.analysis_date)
            profile = _gate_personal(req)
            result = pipeline.run(
                analysis_date=analysis,
                birth_date=(birth.year, birth.month, birth.day, req.hour),
                gender=req.gender, theme=req.theme, compute_only=True,
                trace_id=getattr(request.state, "trace_id", None),
                timezone=profile.timezone, location=profile.location,
                birth_minute=req.birth_minute,
            )
            from .engine_qa import summarize_result
            return summarize_result(result, analysis)

    # Today card
    # ------------------------------------------------------------------ #

    mock_path = root / "web" / "data" / "today.json"
    try:
        with open(mock_path, "r", encoding="utf-8") as f:
            TODAY_MOCK: dict[str, Any] = json.load(f)
    except OSError:
        TODAY_MOCK = {}

    def _computed_ganzhi(ad: date) -> list[dict]:
        chart = pipeline.bazi_engine.compute((ad.year, ad.month, ad.day, 12), gender="male")
        out = []
        for label, pillar in (
            ("年柱", chart.year_pillar),
            ("月柱", chart.month_pillar),
            ("日柱", chart.day_pillar),
        ):
            el = STEM_ELEMENT.get(pillar.heavenly_stem, "WATER")
            name = f"{STEM_CN.get(pillar.heavenly_stem, '?')}{BRANCH_CN.get(pillar.earthly_branch, '?')}"
            out.append({"name": name, "label": label, "color": ELEMENT_COLOR.get(el, "var(--c-shui)")})
        return out

    def _today_card(
        ad: date,
        region: str,
        response: Response,
        trace_id: str | None,
        identity: IdentityContext,
    ) -> dict:
        card = TODAY_MOCK.get(f"{ad.isoformat()}|{region}") or TODAY_MOCK.get("default", {})
        card = dict(card)
        # G-F5 (guest-tier leak): mock data carries hexagram.personal — a
        # per-user reading that must never reach the public tier. Strip the
        # nested key here; _personal_block() re-adds the top-level "personal"
        # block only for authenticated identities below.
        if "hexagram" in card and isinstance(card["hexagram"], dict):
            card["hexagram"] = {k: v for k, v in card["hexagram"].items() if k != "personal"}

        # Deterministic fields computed live; editorial fields bridged from mock.
        card["ganZhi"] = _computed_ganzhi(ad)
        card["weekday"] = WEEKDAY_CN[ad.weekday()]
        card["day"] = ad.day
        # V4.0.1 §7.4 Calendar 去 Mock:黄历字段由 huangli_engine 实时计算
        # (lunar_python 1.4.8 + 日柱锚定),来源登记见 backend/data/calendar_sources.json。
        hl = pipeline.huangli_engine.get_day(ad)
        hl_dict = hl.to_dict()
        card["lunarMonth"] = hl_dict["lunar_month_label"]
        card["yi"] = hl_dict["yi"]
        card["ji"] = hl_dict["ji"]
        card["calendar"] = hl_dict
        card["provenance"] = {
            "ganZhi": "computed",
            "weekday": "computed",
            "day": "computed",
            "lunarMonth/yi/ji/calendar": "computed (calendar source registry: lunar_python 1.4.8 + day_stem_branch_anchor)",
            "greeting/monthLabel/theme/catalyst/dimensions/time_window/hexagram/reasoning/cross_validation": "mock_until_profile_gate_or_content_module",
        }
        card["trace_id"] = trace_id
        # B-09 STAGE-B (M1): public tier by default; personal block only when
        # the optional 3-tier dep resolves an authenticated identity. The
        # negative-assertion test relies on this key being ABSENT for guests.
        if identity.is_authenticated:
            card["personal"] = _personal_block(identity)
        return card

    @app.get(
        "/v1/today",
        dependencies=[Depends(RATE_LIMIT_READ_PUBLIC), Depends(RATE_LIMIT_READ_USER)],
    )
    def today(
        date_str: Optional[str] = Query(None, alias="date"),
        region: str = Query("Beijing"),
        response: Response = None,
        request: Request = None,
        identity: IdentityContext = Depends(get_current_user_or_device),
    ) -> dict:
        ad = date.fromisoformat(date_str) if date_str else date.today()
        trace_id = getattr(request.state, "trace_id", None)
        return _today_card(ad, region, response, trace_id, identity)

    # ------------------------------------------------------------------ #
    # P0-2 Profile Gate — §32 POST /v1/profile (validation + normalization
    # receipt; stateless — DB persistence deferred to SIR Runtime P0-5)
    # ------------------------------------------------------------------ #

    @app.post(
        "/v1/profile",
        dependencies=[Depends(get_current_user), Depends(RATE_LIMIT_WRITE_USER)],
    )
    def profile(
        req: ProfileRequest,
        request: Request,
        identity: IdentityContext = Depends(get_current_user_or_device),
    ) -> dict:
        birth, _ = _parse_dates(req.birth_date, req.analysis_date)
        # Phase 1 / Gender 重构:gender 显式传入 resolve_profile（Profile Contract §1.2）
        state = resolve_profile(
            timezone=req.timezone,
            calendar_system=req.calendar_system,
            location=req.location,
            time_resolver=time_resolver,
            gender=req.gender,
        )
        require_personal_profile(state)  # 422 INSUFFICIENT_INPUT + missing_fields
        resolved = time_resolver.resolve(
            birth_date=birth,
            hour=req.birth_time.hour,
            minute=req.birth_time.minute,
            timezone=state.timezone,
            location=state.location,
            apparent_solar=True,
            gender=state.gender,  # SubjectContext.gender 接线
        )
        return {
            "profile_status": ProfileStatus.VALID.value,
            "birth_date": birth.isoformat(),
            "birth_time": {
                "hour": req.birth_time.hour,
                "minute": req.birth_time.minute,
            },
            "timezone": state.timezone,
            "location": resolved.location_id,
            "calendar_system": state.calendar_system,
            "resolved_time_policy": {
                "timezone": resolved.timezone,
                "longitude": resolved.longitude,
                "latitude": resolved.latitude,
                "apparent_solar": resolved.apparent_solar,
                "calendar_system": resolved.calendar_system,
                "day_boundary": resolved.day_boundary,
                "birth_effective": resolved.birth_effective(),
                "correction_minutes": resolved.corrections.get("total_correction_min"),
                "corrections": resolved.corrections,
                "warnings": resolved.warnings,
            },
            "trace_id": getattr(request.state, "trace_id", None),
        }

    # 独立档案存储契约：旧 /v1/profile 仍保持无状态校验回执。
    # 只有明确装配 profile_store 且用户持有效 bearer 时才提供持久化。
    def _require_profile_user(identity: IdentityContext) -> str:
        if identity.user is None or not identity.user.user_id or identity.user.user_id == "anonymous":
            raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "user bearer token required"})
        return identity.user.user_id

    @app.put("/v1/profile/stored")
    def save_stored_profile(
        req: ProfileRequest,
        request: Request,
        identity: IdentityContext = Depends(get_current_user_or_device),
    ) -> dict:
        user_id = _require_profile_user(identity)
        if profile_store is None:
            raise HTTPException(status_code=503, detail={"code": "PROFILE_STORE_UNAVAILABLE", "message": "profile storage not configured"})
        birth, _ = _parse_dates(req.birth_date, req.analysis_date)
        state = resolve_profile(timezone=req.timezone, calendar_system=req.calendar_system,
                                location=req.location, time_resolver=time_resolver, gender=req.gender)
        require_personal_profile(state)
        # 在任何 DB 写入之前执行时间解析；不接受无效出生信息。
        time_resolver.resolve(birth_date=birth, hour=req.birth_time.hour,
                              minute=req.birth_time.minute, timezone=state.timezone,
                              location=state.location, apparent_solar=True, gender=state.gender)
        profile_store.save(user_id, {
            "birth_date": birth.isoformat(),
            "birth_time": {"hour": req.birth_time.hour, "minute": req.birth_time.minute},
            "gender": state.gender, "timezone": state.timezone,
            "location": state.location, "current_location": req.current_location,
            "calendar_system": state.calendar_system,
        })
        return {"profile_status": "VALID", "stored": True,
                "trace_id": getattr(request.state, "trace_id", None)}

    @app.get("/v1/profile/stored")
    def read_stored_profile(
        identity: IdentityContext = Depends(get_current_user_or_device),
    ) -> dict:
        user_id = _require_profile_user(identity)
        if profile_store is None:
            raise HTTPException(status_code=503, detail={"code": "PROFILE_STORE_UNAVAILABLE", "message": "profile storage not configured"})
        profile = profile_store.get(user_id)
        if profile is None:
            raise HTTPException(status_code=404, detail={"code": "PROFILE_NOT_FOUND", "message": "profile not found"})
        return profile

    # ------------------------------------------------------------------ #
    # DEPRECATED V2 paths (Sunset 2027-08-18; Deprecation headers added by
    # TraceMiddleware. status code stays 200 on success.)
    # ------------------------------------------------------------------ #

    @app.post(
        "/api/reading",
        deprecated=True,
        dependencies=[Depends(get_current_user), Depends(RATE_LIMIT_COMPUTE_USER)],
    )
    def reading_legacy(
        req: ReadingRequest,
        response: Response,
        request: Request,
        identity: IdentityContext = Depends(get_current_user_or_device),
    ) -> dict:
        birth, analysis = _parse_dates(req.birth_date, req.analysis_date)
        profile = _gate_personal(req)
        result = pipeline.run(
            analysis_date=analysis,
            birth_date=(birth.year, birth.month, birth.day, req.hour),
            gender=req.gender,
            theme=req.theme,
            trace_id=getattr(request.state, "trace_id", None),
            timezone=profile.timezone,
            location=profile.location,
            birth_minute=req.birth_minute,
        )
        if result.render_elapsed_ms is not None:
            response.headers["X-Render-Time-Ms"] = f"{result.render_elapsed_ms:.0f}"
        return _reading_response(result, analysis)

    @app.get(
        "/api/today",
        deprecated=True,
        dependencies=[Depends(RATE_LIMIT_READ_PUBLIC), Depends(RATE_LIMIT_READ_USER)],
    )
    def today_legacy(
        date_str: Optional[str] = Query(None, alias="date"),
        region: str = Query("Beijing"),
        response: Response = None,
        request: Request = None,
        identity: IdentityContext = Depends(get_current_user_or_device),
    ) -> dict:
        ad = date.fromisoformat(date_str) if date_str else date.today()
        trace_id = getattr(request.state, "trace_id", None)
        return _today_card(ad, region, response, trace_id, identity)

    # B-09 STAGE-B: B-05 freeze preserved — NFC stays 501 with no auth.
    # Register the NFC router inside create_app so test clients built with
    # create_app() (as opposed to the module-level app singleton) see the
    # /nfc/* routes. B-05 freeze: still 501, still no auth (M2).
    from .nfc import router as _nfc_router
    app.include_router(_nfc_router)  # _nfc_router already declares prefix="/nfc"

    # B-09 R2 rework (ARBITRATION_BATCH3 R1): mount the /v1/auth router
    # inside create_app so test clients (TestClient(create_app())) see the
    # five auth endpoints. Previously the router was defined but never
    # included, so POST /v1/auth/register returned 404 at HTTP layer.
    from .auth import router as _auth_router
    app.include_router(_auth_router)  # _auth_router already declares prefix="/v1/auth"

    # P0-LEGACY-PURGE: /admin 断言观测台（V13 Assertion Observatory）已移除。
    # 该路由承载旧 Assertion/Resolver/Guidance 生产链，会独立产生 rendered_guidance
    # 命理结论且绕过 Authority Ledger（与 Canonical 管线零代码共享）。
    # 按 P0 Legacy Runtime Complete Purge 裁决：彻底删除，不再挂载。
    # 需要 Debug/Research 观测面时应基于新架构（assertion_v2/judgment_architecture）重建。

    # B-09 R2 rework (ARBITRATION_BATCH3 R1): wire the production db_ops
    # singleton when Postgres is reachable. The gateway stays None in tests
    # (FakeDB is wired by the test fixtures via the module attribute); the
    # /v1/auth/* routes return 503 AUTH_UNAVAILABLE when gateway is None.
    if db_ops is not None:
        from ..services.identity_gateway import get_gateway_v2 as _wiring
        _wiring(db_ops)

    # B-09 STAGE-B test isolation: clear any rate-limit state when
    # create_app is called multiple times in the same process (conftest
    # re-creates the app between scenarios).
    reset_rate_limit_buckets()

    return app


# B-09 R2 rework (ARBITRATION_BATCH3 R2): removed unconditional module-level
# `app = create_app()` so importing tongshu.api.app does NOT trigger
# ensure_auth_ready(). Production uses `uvicorn tongshu.api.app:create_app
# --factory` (or imports create_app directly), so the fail-fast gate
# still runs on every legitimate startup path. The lazy import test
# (test_c_import_never_raises_without_secret) relies on this contract.


# Optional module-level app: only built when TONGSHU_TONG_EAGER=1.
# The default is the factory pattern (uvicorn --factory); this block
# preserves the legacy `uvicorn tongshu.api.app:app` entry for ops who
# still prefer it, AND it lets test runners force a real app build
# without exporting the secret first.
if os.environ.get("TONGSHU_TONG_EAGER") == "1":
    app = create_app()  # noqa: F841
