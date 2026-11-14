"""OTC-G structured error contract (V3.6 §32).

Every error response uses the uniform envelope:
    {"error": {"code", "message", "request_id", "trace_id", "details"}}

Status-code mapping:
    400 INVALID_INPUT        — field present but invalid (format/enum violation)
    422 INSUFFICIENT_INPUT   — critical computation input missing/unparseable
    500 INTERNAL_ERROR       — uncaught pipeline failure
    409/423/424/425/429/502/504 — reserved for later phases (fail-closed
                                  branches per §4.4); defined here so the
                                  contract is complete but not yet wired.

Reserved codes MUST NOT be raised by V1 routes until their trigger path
exists (audit block, evidence/mapping validation, rate limit, AI provider).
"""

from __future__ import annotations
from enum import Enum

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    PROFILE_LOCATION_AMBIGUOUS = "PROFILE_LOCATION_AMBIGUOUS"
    INSUFFICIENT_INPUT = "INSUFFICIENT_INPUT"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    AUDIT_BLOCKED = "AUDIT_BLOCKED"
    EVIDENCE_INVALID = "EVIDENCE_INVALID"
    MAPPING_INVALID = "MAPPING_INVALID"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AI_PROVIDER_ERROR = "AI_PROVIDER_ERROR"
    TIMEOUT = "TIMEOUT"


HTTP_STATUS = {
    ErrorCode.INVALID_INPUT: 400,
    ErrorCode.PROFILE_LOCATION_AMBIGUOUS: 422,
    ErrorCode.INSUFFICIENT_INPUT: 422,
    ErrorCode.VERSION_CONFLICT: 409,
    ErrorCode.AUDIT_BLOCKED: 423,
    ErrorCode.EVIDENCE_INVALID: 424,
    ErrorCode.MAPPING_INVALID: 425,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.AI_PROVIDER_ERROR: 502,
    ErrorCode.TIMEOUT: 504,
}

# Critical computation inputs: their absence means the request is not
# computable at all (V3.6 INSUFFICIENT_INPUT), as opposed to merely invalid.
_CRITICAL_FIELDS = ("birth_date", "hour", "gender")


class OTCGApiError(Exception):
    """Application error carrying an ErrorCode + optional structured details."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: list | None = None,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []
        self.status_code = status_code or HTTP_STATUS[code]


def build_error_body(
    code: str,
    message: str,
    request_id: str | None,
    trace_id: str | None,
    details: list | None = None,
) -> dict:
    """Build the §32 uniform error envelope."""
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "trace_id": trace_id,
            "details": details or [],
        }
    }


def _ids_from_request(request: Request) -> tuple[str | None, str | None]:
    request_id = getattr(request.state, "request_id", None)
    trace_id = getattr(request.state, "trace_id", None)
    return request_id, trace_id


async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Pydantic validation failure → 400 INVALID_INPUT, except missing
    critical computation input → 422 INSUFFICIENT_INPUT."""
    request_id, trace_id = _ids_from_request(request)
    missing_critical = any(
        e.get("type") == "missing" and str(e.get("loc", [""])[-1]) in _CRITICAL_FIELDS
        for e in exc.errors()
    )
    if missing_critical:
        code, status = ErrorCode.INSUFFICIENT_INPUT, 422
        message = "missing or unparseable critical computation input (birth_date / hour / gender)"
    else:
        code, status = ErrorCode.INVALID_INPUT, 400
        message = "request fields present but invalid"
    details = [
        {"loc": list(e.get("loc", [])), "msg": e.get("msg"), "type": e.get("type")}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status,
        content=build_error_body(code, message, request_id, trace_id, details),
    )


async def otcg_api_error_handler(request: Request, exc: OTCGApiError) -> JSONResponse:
    request_id, trace_id = _ids_from_request(request)
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_body(
            exc.code.value, exc.message, request_id, trace_id, exc.details
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all → 500 INTERNAL_ERROR with the uniform envelope."""
    request_id, trace_id = _ids_from_request(request)
    return JSONResponse(
        status_code=500,
        content=build_error_body(
            ErrorCode.INTERNAL_ERROR.value,
            "internal error",
            request_id,
            trace_id,
            [{"type": exc.__class__.__name__, "msg": str(exc)}],
        ),
    )
