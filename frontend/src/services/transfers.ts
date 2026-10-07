import { ApiError, apiRequest, isRecord } from './api'

export interface TransferRequest {
  from_account: string
  to_account: string
  amount: string
}

export interface TransferResponse {
  transaction_id: string
  status: 'COMPLETED'
  from_account: string
  to_account: string
  amount: string
  created_at: string
}

const AMOUNT_PATTERN = /^(0|[1-9][0-9]*)(\.[0-9]{1,2})?$/

export function isValidTransferAmount(amount: string): boolean {
  if (!AMOUNT_PATTERN.test(amount)) {
    return false
  }

  const [wholePart = ''] = amount.split('.', 1)
  return wholePart !== '0'
}

function isTransferResponse(value: unknown): value is TransferResponse {
  if (!isRecord(value)) {
    return false
  }

  return (
    typeof value.transaction_id === 'string' &&
    value.transaction_id.length > 0 &&
    value.status === 'COMPLETED' &&
    typeof value.from_account === 'string' &&
    /^XXXX[0-9]{4}$/.test(value.from_account) &&
    typeof value.to_account === 'string' &&
    /^XXXX[0-9]{4}$/.test(value.to_account) &&
    typeof value.amount === 'string' &&
    /^[0-9]+\.[0-9]{2}$/.test(value.amount) &&
    typeof value.created_at === 'string' &&
    !Number.isNaN(Date.parse(value.created_at))
  )
}

export async function createTransfer(
  request: TransferRequest,
): Promise<TransferResponse> {
  const response = await apiRequest('/transfers', {
    method: 'POST',
    body: JSON.stringify(request),
  })

  if (!isTransferResponse(response)) {
    throw new ApiError(
      'TRANSFER_FAILED',
      'The transfer response could not be verified.',
    )
  }

  return response
}
