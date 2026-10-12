import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import {
  getDevAuthSession,
  signInAsDemo,
  signOutDemo,
} from './services/devAuth'
import type { DevAuthStatus } from './services/devAuth'

vi.mock('./pages/TransferPage', () => ({
  default: () => <h1>Transfer form</h1>,
}))

vi.mock('./services/devAuth', () => ({
  getDevAuthSession: vi.fn(),
  signInAsDemo: vi.fn(),
  signOutDemo: vi.fn(),
}))

const mockedGetSession = vi.mocked(getDevAuthSession)
const mockedSignIn = vi.mocked(signInAsDemo)
const mockedSignOut = vi.mocked(signOutDemo)

const signedOutStatus: DevAuthStatus = {
  fake_auth_enabled: true,
  authenticated: false,
  profiles: [{ profile_id: 'demo-user-1', label: 'Demo user 1' }],
}

const signedInStatus: DevAuthStatus = {
  ...signedOutStatus,
  authenticated: true,
  current_profile: { profile_id: 'demo-user-1', label: 'Demo user 1' },
}

describe('App development sign-in', () => {
  beforeEach(() => {
    vi.stubEnv('DEV', true)
    mockedGetSession.mockReset()
    mockedSignIn.mockReset()
    mockedSignOut.mockReset()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('offers password-free demo sign-in and opens the transfer form after login', async () => {
    mockedGetSession
      .mockResolvedValueOnce(signedOutStatus)
      .mockResolvedValueOnce(signedInStatus)
    mockedSignIn.mockResolvedValue(signedInStatus)
    const user = userEvent.setup()

    render(<App />)

    await user.selectOptions(
      await screen.findByLabelText('Demo profile'),
      'demo-user-1',
    )
    expect(screen.queryByLabelText(/password/i)).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Sign in as demo user' }))

    expect(mockedSignIn).toHaveBeenCalledWith('demo-user-1')
    expect(await screen.findByRole('heading', { name: 'Transfer form' }))
      .toBeInTheDocument()
  })

  it('keeps the existing transfer screen when fake auth is disabled', async () => {
    mockedGetSession.mockResolvedValue({
      fake_auth_enabled: false,
      authenticated: false,
      profiles: [],
    })

    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Transfer form' }))
      .toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Sign in as demo user' }))
      .not.toBeInTheDocument()
  })

  it('returns to demo sign-in after signing out', async () => {
    mockedGetSession.mockResolvedValue(signedInStatus)
    mockedSignOut.mockResolvedValue(signedOutStatus)
    const user = userEvent.setup()

    render(<App />)

    await user.click(await screen.findByRole('button', { name: 'Sign out' }))

    await waitFor(() => {
      expect(screen.getByLabelText('Demo profile')).toBeInTheDocument()
    })
    expect(mockedSignOut).toHaveBeenCalledOnce()
  })

  it('does not request demo status in a production Vite build', async () => {
    vi.stubEnv('DEV', false)
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Transfer form' }))
      .toBeInTheDocument()
    expect(mockedGetSession).not.toHaveBeenCalled()
    expect(screen.queryByRole('button', { name: 'Sign in as demo user' }))
      .not.toBeInTheDocument()
  })
})
