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
  if (typeof body !== 'object' || body === null || !('error' in body)) return false
  const error = (body as Record<string, unknown>).error
  return typeof error === 'object' && error !== null &&
    typeof (error as Record<string, unknown>).code === 'string' &&
    typeof (error as Record<string, unknown>).message === 'string'
}

export function isAuthDetailBody(body: unknown): body is AuthDetailBody {
  if (typeof body !== 'object' || body === null || !('detail' in body)) return false
  const detail = (body as Record<string, unknown>).detail
  return typeof detail === 'object' && detail !== null && !Array.isArray(detail) &&
    typeof (detail as Record<string, unknown>).code === 'string' &&
    typeof (detail as Record<string, unknown>).message === 'string'
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
  if (typeof body === 'object' && body !== null && 'detail' in body) {
    const detail = (body as Record<string, unknown>).detail
    if (Array.isArray(detail)) {
      const details = detail.filter(item => typeof item === 'object' && item !== null)
      return { code: 'INVALID_INPUT', message: '提交的信息未通过校验', details }
    }
  }
  return { code: 'UNKNOWN', message: '无法识别的错误响应' }
}
