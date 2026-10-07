import { afterEach, describe, expect, it, vi } from 'vitest'

import { createTransfer, isValidTransferAmount } from './transfers'

const successfulPayload = {
  transaction_id: 'transaction-123',
  status: 'COMPLETED',
  from_account: 'XXXX5678',
  to_account: 'XXXX4321',
  amount: '125.50',
  created_at: '2026-10-07T12:00:00Z',
}

const amountCases: Array<[string, boolean]> = [
  ['1', true],
  ['1.00', true],
  ['0.99', false],
  ['1.001', false],
  ['1e2', false],
  ['0001.00', false],
]

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('transfer API boundary', () => {
  it('sends transfer data only to the versioned API endpoint', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(successfulPayload), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await createTransfer({
      from_account: '12345678',
      to_account: '87654321',
      amount: '125.50',
    })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/transfers',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify({
          from_account: '12345678',
          to_account: '87654321',
          amount: '125.50',
        }),
      }),
    )
  })

  it.each(amountCases)('validates amount %s as %s', (amount, valid) => {
    expect(isValidTransferAmount(amount)).toBe(valid)
  })
})
