import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../services/api'
import { createTransfer } from '../services/transfers'
import type { TransferResponse } from '../services/transfers'
import TransferPage from './TransferPage'

vi.mock('../services/transfers', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('../services/transfers')>()
  return { ...actual, createTransfer: vi.fn() }
})

const mockedCreateTransfer = vi.mocked(createTransfer)

const completedTransfer: TransferResponse = {
  transaction_id: 'transaction-123',
  status: 'COMPLETED',
  from_account: 'XXXX5678',
  to_account: 'XXXX4321',
  amount: '125.50',
  created_at: '2026-10-07T12:00:00Z',
}

async function enterTransfer(amount = '125.50') {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText('From account'), '12345678')
  await user.type(screen.getByLabelText('To account'), '87654321')
  await user.type(screen.getByLabelText('Amount (INR)'), amount)
  return user
}

describe('TransferPage', () => {
  beforeEach(() => {
    mockedCreateTransfer.mockReset()
  })

  it('submits through the transfer API and shows the saved confirmation', async () => {
    mockedCreateTransfer.mockResolvedValue(completedTransfer)
    render(<TransferPage />)

    const user = await enterTransfer()
    await user.click(screen.getByRole('button', { name: 'Transfer money' }))

    expect(mockedCreateTransfer).toHaveBeenCalledWith({
      from_account: '12345678',
      to_account: '87654321',
      amount: '125.50',
    })
    const confirmation = await screen.findByRole('region', {
      name: 'Transfer confirmation',
    })
    expect(confirmation).toHaveTextContent('transaction-123')
    expect(confirmation).toHaveTextContent('XXXX5678')
  })

  it('rejects an invalid amount before calling the API', async () => {
    render(<TransferPage />)

    const user = await enterTransfer('0.99')
    await user.click(screen.getByRole('button', { name: 'Transfer money' }))

    expect(mockedCreateTransfer).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent('at least Rs 1.00')
  })

  it('shows an API decline without presenting a success confirmation', async () => {
    mockedCreateTransfer.mockRejectedValue(
      new ApiError(
        'INSUFFICIENT_BALANCE',
        'The source account does not have enough available funds.',
      ),
    )
    render(<TransferPage />)

    const user = await enterTransfer()
    await user.click(screen.getByRole('button', { name: 'Transfer money' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The source account does not have enough available funds.',
    )
    expect(
      screen.queryByRole('region', { name: 'Transfer confirmation' }),
    ).not.toBeInTheDocument()
  })
})
