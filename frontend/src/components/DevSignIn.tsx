import { useState } from 'react'
import type { FormEvent } from 'react'

import type { DemoProfile } from '../services/devAuth'

interface DevSignInProps {
  profiles: DemoProfile[]
  currentProfile?: DemoProfile
  isSubmitting: boolean
  errorMessage: string | null
  onSignIn: (profileId: string) => Promise<void>
  onSignOut: () => Promise<void>
}

export default function DevSignIn({
  profiles,
  currentProfile,
  isSubmitting,
  errorMessage,
  onSignIn,
  onSignOut,
}: DevSignInProps) {
  const [profileId, setProfileId] = useState(profiles[0]?.profile_id ?? '')

  if (currentProfile) {
    return (
      <div className="dev-session-banner" role="status">
        <span>Demo session: {currentProfile.label}</span>
        <button disabled={isSubmitting} onClick={() => void onSignOut()} type="button">
          Sign out
        </button>
        {errorMessage && (
          <p className="transfer-error" role="alert">
            {errorMessage}
          </p>
        )}
      </div>
    )
  }

  return (
    <main className="bank-shell">
      <header className="bank-header">
        <p className="bank-name">Simple Bank</p>
        <p className="secure-label">Development/test demo sign-in</p>
      </header>
      <section className="transfer-card" aria-labelledby="demo-sign-in-title">
        <p className="eyebrow">Local testing</p>
        <h1 id="demo-sign-in-title">Sign in to test transfers</h1>
        <p className="intro">
          Select a seeded demo profile. No password or real customer credentials are used.
        </p>
        {profiles.length === 0 ? (
          <p className="transfer-error" role="alert">
            No demo profiles are available. Prepare the local demo data and try again.
          </p>
        ) : (
          <form
            className="transfer-form"
            onSubmit={(event: FormEvent<HTMLFormElement>) => {
              event.preventDefault()
              void onSignIn(profileId)
            }}
          >
            <label htmlFor="demo-profile">Demo profile</label>
            <select
              id="demo-profile"
              onChange={(event) => setProfileId(event.target.value)}
              value={profileId}
            >
              {profiles.map((profile) => (
                <option key={profile.profile_id} value={profile.profile_id}>
                  {profile.label}
                </option>
              ))}
            </select>
            <button disabled={isSubmitting || !profileId} type="submit">
              {isSubmitting ? 'Signing in...' : 'Sign in as demo user'}
            </button>
          </form>
        )}
        {errorMessage && (
          <p className="transfer-error" role="alert">
            {errorMessage}
          </p>
        )}
      </section>
    </main>
  )
}
