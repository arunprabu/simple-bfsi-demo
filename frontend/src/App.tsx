import { useEffect, useState } from 'react'

import './App.css'
import DevSignIn from './components/DevSignIn'
import TransferPage from './pages/TransferPage'
import { ApiError } from './services/api'
import {
  getDevAuthSession,
  signInAsDemo,
  signOutDemo,
} from './services/devAuth'
import type { DevAuthStatus } from './services/devAuth'

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : 'Demo sign-in is unavailable. Check the local backend and demo data.'
}

function App() {
  const [session, setSession] = useState<DevAuthStatus | null>(null)
  const [isLoading, setIsLoading] = useState(import.meta.env.DEV)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!import.meta.env.DEV) {
      return
    }

    let isMounted = true
    void getDevAuthSession()
      .then((status) => {
        if (isMounted) {
          setSession(status)
          setErrorMessage(null)
        }
      })
      .catch((error: unknown) => {
        if (isMounted) {
          setErrorMessage(getErrorMessage(error))
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false)
        }
      })

    return () => {
      isMounted = false
    }
  }, [])

  async function handleSignIn(profileId: string): Promise<void> {
    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      setSession(await signInAsDemo(profileId))
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleSignOut(): Promise<void> {
    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      setSession(await signOutDemo())
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!import.meta.env.DEV) {
    return <TransferPage />
  }

  if (isLoading) {
    return (
      <main className="bank-shell" aria-busy="true">
        <p role="status">Checking local demo sign-in...</p>
      </main>
    )
  }

  if (errorMessage && session === null) {
    return (
      <main className="bank-shell">
        <p className="transfer-error" role="alert">
          {errorMessage}
        </p>
        <button
          onClick={() => {
            setIsLoading(true)
            setErrorMessage(null)
            void getDevAuthSession()
              .then(setSession)
              .catch((error: unknown) => setErrorMessage(getErrorMessage(error)))
              .finally(() => setIsLoading(false))
          }}
          type="button"
        >
          Retry
        </button>
      </main>
    )
  }

  if (!session?.fake_auth_enabled) {
    return <TransferPage />
  }

  if (!session.authenticated) {
    return (
      <DevSignIn
        errorMessage={errorMessage}
        isSubmitting={isSubmitting}
        onSignIn={handleSignIn}
        onSignOut={handleSignOut}
        profiles={session.profiles}
      />
    )
  }

  return (
    <>
      <DevSignIn
        currentProfile={session.current_profile}
        errorMessage={errorMessage}
        isSubmitting={isSubmitting}
        onSignIn={handleSignIn}
        onSignOut={handleSignOut}
        profiles={session.profiles}
      />
      <TransferPage />
    </>
  )
}

export default App
