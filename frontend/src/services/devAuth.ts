import { ApiError, apiRequest, isRecord } from './api'

export interface DemoProfile {
  profile_id: string
  label: string
}

export interface DevAuthStatus {
  fake_auth_enabled: boolean
  authenticated: boolean
  profiles: DemoProfile[]
  current_profile?: DemoProfile
}

const PROFILE_IDS = new Set(['demo-user-1', 'demo-user-2'])

function isDemoProfile(value: unknown): value is DemoProfile {
  return (
    isRecord(value) &&
    typeof value.profile_id === 'string' &&
    PROFILE_IDS.has(value.profile_id) &&
    typeof value.label === 'string' &&
    value.label.length > 0
  )
}

function isDevAuthStatus(value: unknown): value is DevAuthStatus {
  if (
    !isRecord(value) ||
    typeof value.fake_auth_enabled !== 'boolean' ||
    typeof value.authenticated !== 'boolean' ||
    !Array.isArray(value.profiles) ||
    !value.profiles.every(isDemoProfile)
  ) {
    return false
  }

  return value.current_profile === undefined || isDemoProfile(value.current_profile)
}

async function readDevAuthStatus(path: string, options: RequestInit) {
  const response = await apiRequest(path, options)
  if (!isDevAuthStatus(response)) {
    throw new ApiError(
      'DEMO_DATA_UNAVAILABLE',
      'The demo sign-in response could not be verified.',
    )
  }
  return response
}

export function getDevAuthSession(): Promise<DevAuthStatus> {
  return readDevAuthStatus('/dev-auth/session', { method: 'GET' })
}

export function signInAsDemo(profileId: string): Promise<DevAuthStatus> {
  if (!PROFILE_IDS.has(profileId)) {
    return Promise.reject(
      new ApiError('DEMO_PROFILE_NOT_FOUND', 'Select an available demo profile.'),
    )
  }

  return readDevAuthStatus('/dev-auth/session', {
    method: 'POST',
    body: JSON.stringify({ profile_id: profileId }),
  })
}

export function signOutDemo(): Promise<DevAuthStatus> {
  return readDevAuthStatus('/dev-auth/session', { method: 'DELETE' })
}
