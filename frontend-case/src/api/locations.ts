import { apiRequest } from './http'

export interface BirthLocation { id: string; name: string; country: string; timezone?: string; aliases?: string[] }

export async function fetchBirthLocations(): Promise<BirthLocation[]> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 10000)
  let response: { locations: BirthLocation[] }
  try {
    response = await apiRequest<{ locations: BirthLocation[] }>('/v1/locations', { signal: controller.signal })
  } finally {
    clearTimeout(timer)
  }
  if (!Array.isArray(response.locations) || !response.locations.every(location =>
    typeof location.id === 'string' && typeof location.name === 'string' && typeof location.country === 'string' &&
    (location.timezone === undefined || typeof location.timezone === 'string') &&
    (location.aliases === undefined || (Array.isArray(location.aliases) && location.aliases.every(alias => typeof alias === 'string'))))) {
    throw new Error('invalid location catalogue')
  }
  return response.locations
}
