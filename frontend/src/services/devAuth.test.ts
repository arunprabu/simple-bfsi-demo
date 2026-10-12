import { afterEach, describe, expect, it, vi } from 'vitest'

import { getDevAuthSession, signInAsDemo, signOutDemo } from './devAuth'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('development authentication API', () => {
  it('reads the demo-session status through the versioned API', async () => {
    const response = {
      fake_auth_enabled: true,
      authenticated: false,
      profiles: [{ profile_id: 'demo-user-1', label: 'Demo user 1' }],
    }
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(response), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await getDevAuthSession()

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/dev-auth/session',
      expect.objectContaining({
        method: 'GET',
        credentials: 'include',
      }),
    )
  })

  it('signs in by profile alias without sending a password', async () => {
    const response = {
      fake_auth_enabled: true,
      authenticated: true,
      profiles: [{ profile_id: 'demo-user-1', label: 'Demo user 1' }],
      current_profile: { profile_id: 'demo-user-1', label: 'Demo user 1' },
    }
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(response), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await signInAsDemo('demo-user-1')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/dev-auth/session',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify({ profile_id: 'demo-user-1' }),
      }),
    )
  })

  it('signs out through the versioned API and receives session status JSON', async () => {
    const response = {
      fake_auth_enabled: true,
      authenticated: false,
      profiles: [{ profile_id: 'demo-user-1', label: 'Demo user 1' }],
    }
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(response), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await signOutDemo()

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/dev-auth/session',
      expect.objectContaining({
        method: 'DELETE',
        credentials: 'include',
      }),
    )
  })
})
