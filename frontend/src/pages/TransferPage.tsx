import { useState } from 'react'

import TransferForm from '../components/TransferForm'
import { ApiError } from '../services/api'
import { createTransfer } from '../services/transfers'
import type {
  TransferRequest,
  TransferResponse,
} from '../services/transfers'

export default function TransferPage() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [transfer, setTransfer] = useState<TransferResponse | null>(null)

  async function submitTransfer(request: TransferRequest): Promise<void> {
    setErrorMessage(null)
    setTransfer(null)
    setIsSubmitting(true)

    try {
      setTransfer(await createTransfer(request))
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : 'Transfer could not be completed. Please try again.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="bank-shell">
      <header className="bank-header">
        <p className="bank-name">Simple Bank</p>
        <p className="secure-label">Secure transfer</p>
      </header>

      <section className="transfer-card" aria-labelledby="transfer-title">
        <p className="eyebrow">Payments</p>
        <h1 id="transfer-title">Transfer funds</h1>
        <p className="intro">
          Send money from your savings account to another Simple Bank account.
        </p>

        <TransferForm
          isSubmitting={isSubmitting}
          onTransfer={submitTransfer}
        />

        {errorMessage && (
          <p className="transfer-error" role="alert">
            {errorMessage}
          </p>
        )}

        {transfer && (
          <section
            aria-label="Transfer confirmation"
            className="confirmation"
            role="region"
          >
            <h2>Transfer complete</h2>
            <p>Transaction ID: {transfer.transaction_id}</p>
            <p>From: {transfer.from_account}</p>
            <p>To: {transfer.to_account}</p>
            <p>Amount: Rs {transfer.amount}</p>
          </section>
        )}
      </section>
    </main>
  )
}
