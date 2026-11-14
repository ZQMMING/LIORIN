import { apiRequest } from './http'

export interface EngineQaRequest {
  birth_date: string
  hour: number
  birth_minute?: number | null
  gender: 'male' | 'female'
  theme: string
  analysis_date: string
  timezone: string
  location: string
}

export interface EngineQaResponse {
  analysis_date: string
  canonical_id: string
  trace_id: string | null
  source: string
  validation_passed: boolean
  validation_status: 'not_run'
  bazi_pillars?: { year: string; month: string; day: string; hour: string } | null
  observed_evidence_by_engine: Record<string, number>
  result_available: { heluo: boolean; yijing_structure: boolean }
  ziping_claim_count: number
  heluo: { prenatal: string | null; postnatal: string | null } | null
  claims: Array<{ claim_id?: string; domain?: string; conclusion?: string; claim: string; evidence_refs: string[] }>
  claim_count: number
  warning: string
}

export class InvalidEngineQaResponse extends Error {}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function validResponse(value: unknown): value is EngineQaResponse {
  if (!record(value) || typeof value.canonical_id !== 'string' || typeof value.source !== 'string' ||
      typeof value.warning !== 'string' || !record(value.result_available) ||
      typeof value.result_available.heluo !== 'boolean' || typeof value.result_available.yijing_structure !== 'boolean' ||
      !record(value.observed_evidence_by_engine) || !Object.values(value.observed_evidence_by_engine).every(n => typeof n === 'number') ||
      typeof value.ziping_claim_count !== 'number' || !Array.isArray(value.claims)) return false
  if (!value.claims.every(c => record(c) && typeof c.claim === 'string' &&
      ['claim_id', 'domain', 'conclusion'].every(k => c[k] == null || typeof c[k] === 'string') &&
      Array.isArray(c.evidence_refs) && c.evidence_refs.every((ref: unknown) => typeof ref === 'string'))) return false
  if (value.bazi_pillars != null && (!record(value.bazi_pillars) ||
      !['year', 'month', 'day', 'hour'].every(key => typeof (value.bazi_pillars as Record<string, unknown>)[key] === 'string'))) return false
  if (value.heluo != null && (!record(value.heluo) ||
      !['prenatal', 'postnatal'].every(key => value.heluo && ((value.heluo as Record<string, unknown>)[key] == null || typeof (value.heluo as Record<string, unknown>)[key] === 'string')))) return false
  return value.trace_id == null || typeof value.trace_id === 'string'
}

export async function runEngineQa(input: EngineQaRequest): Promise<EngineQaResponse> {
  const response = await apiRequest<unknown>('/v1/qa/engine', { method: 'POST', body: input })
  if (!validResponse(response)) throw new InvalidEngineQaResponse('invalid engine QA response')
  return response
}
