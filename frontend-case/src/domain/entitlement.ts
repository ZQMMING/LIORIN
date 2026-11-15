/**
 * Entitlement Service
 * Section 45 of LIORIN spec: unified entitlement checking
 * Frontend permission is UI presentation only — backend controls real access
 */

import type { Entitlement, ProfileStatus } from '../mock/data'

export class EntitlementService {
  private entitlement: Entitlement
  private profileStatus: ProfileStatus

  constructor(entitlement: Entitlement, profileStatus: ProfileStatus) {
    this.entitlement = entitlement
    this.profileStatus = profileStatus
  }

  get isPublic(): boolean {
    return this.entitlement === 'PUBLIC'
  }

  get isAuthenticated(): boolean {
    return this.entitlement === 'AUTHENTICATED'
  }

  get isPremium(): boolean {
    return this.entitlement === 'PREMIUM'
  }

  get profileValid(): boolean {
    return this.profileStatus === 'VALID'
  }

  get hasProfile(): boolean {
    return this.profileStatus !== 'NONE'
  }

  get canViewPersonal(): boolean {
    return this.profileValid && this.entitlement !== 'PUBLIC'
  }

  get canViewPrivate(): boolean {
    return this.isPremium && this.profileValid
  }

  get canExpandHexagram(): boolean {
    return this.canViewPersonal
  }

  get canUseLLM(): boolean {
    return this.isPremium
  }

  get canViewClassics(): boolean {
    return this.isPremium || this.canViewPersonal
  }

  get needsProfile(): boolean {
    return this.entitlement !== 'PUBLIC' && this.profileStatus === 'NONE'
  }

  get needsProfileComplete(): boolean {
    return this.entitlement !== 'PUBLIC' && this.profileStatus === 'INSUFFICIENT'
  }

  get hasCalculationError(): boolean {
    return this.profileStatus === 'CALCULATION_ERROR'
  }
}

// Factory for creating from mock state
export function createEntitlement(entitlement: Entitlement, profileStatus: ProfileStatus): EntitlementService {
  return new EntitlementService(entitlement, profileStatus)
}
