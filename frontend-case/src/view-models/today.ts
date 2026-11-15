/**
 * View Model — transforms API/mock data into UI-ready structure
 * Section 44 of LIORIN spec
 */

import type { TodayData, PublicTodayData, Entitlement, ProfileStatus } from '../mock/data'
import { EntitlementService } from '../domain/entitlement'

export interface TodayViewModel {
  entitlement: EntitlementService
  isPublic: boolean
  showPersonal: boolean
  showPremiumGate: boolean
  showProfileNone: boolean
  showProfileInsufficient: boolean
  showCalculationError: boolean
  hexagram: TodayData['hexagram']
  cycle: TodayData['cycle']
  activeYao: TodayData['active_yao']
  yaoText: TodayData['yao_text']
  guidance: TodayData['guidance']
  evidence: TodayData['evidence']
  dateLabel: TodayData['date_label']
}

export interface PublicViewModel {
  hexagram: PublicTodayData['hexagram']
  yaoText: PublicTodayData['yao_text']
  guidance: PublicTodayData['guidance']
  evidence: PublicTodayData['evidence']
  dateLabel: PublicTodayData['date_label']
}

/**
 * Build today view model from raw data + user state
 * Frontend never computes cycle_day or active_yao — consumes from backend
 */
export function buildTodayViewModel(
  data: TodayData,
  entitlement: Entitlement,
  profileStatus: ProfileStatus
): TodayViewModel {
  const service = new EntitlementService(entitlement, profileStatus)

  return {
    entitlement: service,
    isPublic: entitlement === 'PUBLIC',
    showPersonal: service.canViewPersonal && data.cycle !== null && data.active_yao !== null,
    showPremiumGate: !service.isPremium && service.isAuthenticated,
    showProfileNone: service.needsProfile,
    showProfileInsufficient: service.needsProfileComplete,
    showCalculationError: service.hasCalculationError,
    hexagram: data.hexagram,
    cycle: data.cycle,
    activeYao: data.active_yao,
    yaoText: data.yao_text,
    guidance: data.guidance,
    evidence: data.evidence,
    dateLabel: data.date_label,
  }
}

/**
 * Build public view model
 */
export function buildPublicViewModel(data: PublicTodayData): PublicViewModel {
  return {
    hexagram: data.hexagram,
    yaoText: data.yao_text,
    guidance: data.guidance,
    evidence: data.evidence,
    dateLabel: data.date_label,
  }
}
