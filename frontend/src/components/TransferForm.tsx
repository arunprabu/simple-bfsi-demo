import { useState } from 'react'
import type { FormEvent } from 'react'

import {
  isValidTransferAmount,
  type TransferRequest,
} from '../services/transfers'

interface TransferFormProps {
  isSubmitting: boolean
  onTransfer: (request: TransferRequest) => Promise<void>
}

export default function TransferForm({
  isSubmitting,
  onTransfer,
}: TransferFormProps) {
  const [fromAccount, setFromAccount] = useState('')
  const [toAccount, setToAccount] = useState('')
  const [amount, setAmount] = useState('')
  const [validationError, setValidationError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setValidationError(null)

    if (!fromAccount.trim() || !toAccount.trim()) {
      setValidationError('Enter both account numbers.')
      return
    }

    if (!isValidTransferAmount(amount)) {
      setValidationError(
        'Amount must be at least Rs 1.00 with no more than two decimal places.',
      )
      return
    }

    await onTransfer({
      from_account: fromAccount.trim(),
      to_account: toAccount.trim(),
      amount,
    })
  }

  return (
    <form className="transfer-form" onSubmit={handleSubmit} noValidate>
      <label htmlFor="from-account">From account</label>
      <input
        autoComplete="off"
        id="from-account"
        name="from_account"
        onChange={(event) => setFromAccount(event.target.value)}
        required
        value={fromAccount}
      />

      <label htmlFor="to-account">To account</label>
      <input
        autoComplete="off"
        id="to-account"
        name="to_account"
        onChange={(event) => setToAccount(event.target.value)}
        required
        value={toAccount}
      />

      <label htmlFor="transfer-amount">Amount (INR)</label>
      <input
        autoComplete="off"
        id="transfer-amount"
        inputMode="decimal"
        name="amount"
        onChange={(event) => setAmount(event.target.value)}
        required
        value={amount}
      />

      {validationError && (
        <p className="form-error" role="alert">
          {validationError}
        </p>
      )}

      <button disabled={isSubmitting} type="submit">
        {isSubmitting ? 'Submitting transfer...' : 'Transfer money'}
      </button>
    </form>
  )
}
