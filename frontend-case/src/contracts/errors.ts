/**
 * Contract Types — 错误响应外壳
 *
 * 后端存在两套错误响应（API_VIEW_CONTRACT.md §2），前端须同时兼容。
 */

/** 形态 A：{"error": {...}} 业务错误 */
export interface ApiErrorBody {
  error: {
    code: string // INVALID_INPUT / INSUFFICIENT_INPUT / AUTH_* 等
    message: string
    request_id?: string
    trace_id?: string
    details?: Array<{
      loc?: (string | number)[]
      msg?: string
      type?: string
      field?: string
      reason?: string
    }>
  }
}

/** 形态 B：{"detail": {...}} auth gateway 未初始化 */
export interface AuthDetailBody {
  detail: {
    code: string // AUTH_UNAVAILABLE 等
    message: string
  }
}

/** 归一化后的错误，供前端统一处理 */
export interface NormalizedApiError {
  code: string
  message: string
  requestId?: string
  traceId?: string
  details?: ApiErrorBody['error']['details']
}

/** 判断一个响应体是不是错误外壳 */
export function isApiErrorBody(body: unknown): body is ApiErrorBody {
  return (
    typeof body === 'object' &&
    body !== null &&
    'error' in (body as Record<string, unknown>)
  )
}

export function isAuthDetailBody(body: unknown): body is AuthDetailBody {
  return (
    typeof body === 'object' &&
    body !== null &&
    'detail' in (body as Record<string, unknown>)
  )
}

/** 把两套外壳归一化为统一结构，避免散写判断 */
export function normalizeApiError(body: unknown): NormalizedApiError {
  if (isApiErrorBody(body)) {
    return {
      code: body.error.code,
      message: body.error.message,
      requestId: body.error.request_id,
      traceId: body.error.trace_id,
      details: body.error.details,
    }
  }
  if (isAuthDetailBody(body)) {
    return {
      code: body.detail.code,
      message: body.detail.message,
    }
  }
  return { code: 'UNKNOWN', message: '无法识别的错误响应' }
}
