import { describe, it, expect, vi, afterEach } from 'vitest'
import { printTodo, printFreeText, printQr, printGoatse, getStatus, getAdminRoll, postAdminRoll, printReceipt } from './api'

afterEach(() => {
  vi.restoreAllMocks()
})

function mockFetch(ok: boolean, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok,
      json: async () => body
    })
  )
}

describe('api error handling', () => {
  it('throws Error with detail message on 503', async () => {
    mockFetch(false, { detail: 'Printer offline' })
    await expect(printTodo('Test', ['item'])).rejects.toThrow('Printer offline')
  })

  it('resolves without throwing on 200 success', async () => {
    mockFetch(true, { success: true })
    await expect(printTodo('Test', ['item'])).resolves.toBeUndefined()
  })

  it('throws fallback message when detail field is absent', async () => {
    mockFetch(false, {})
    await expect(printTodo('Test', ['item'])).rejects.toThrow('Request failed')
  })

  it('throws with detail for printFreeText on error', async () => {
    mockFetch(false, { detail: 'Printer error' })
    await expect(printFreeText('hello', 'medium')).rejects.toThrow('Printer error')
  })

  it('throws with detail for printQr on error', async () => {
    mockFetch(false, { detail: 'Printer error' })
    await expect(printQr('https://example.com')).rejects.toThrow('Printer error')
  })

  it('throws with detail for printGoatse on error', async () => {
    mockFetch(false, { detail: 'Printer error' })
    await expect(printGoatse()).rejects.toThrow('Printer error')
  })

  it('throws with detail for printReceipt on error', async () => {
    mockFetch(false, { detail: 'Printer error' })
    await expect(
      printReceipt({ store: 'Shop', items: [{ name: 'Item', price: 1.0 }], address: null, phone: null, tax_pct: 0 })
    ).rejects.toThrow('Printer error')
  })
})

describe('getStatus', () => {
  it('returns parsed PrinterStatus on 200', async () => {
    const payload = { printer_online: true, paper_near_end: false, paper_out: false, estimated_remaining_pct: 75 }
    mockFetch(true, payload)
    const status = await getStatus()
    expect(status.printer_online).toBe(true)
    expect(status.estimated_remaining_pct).toBe(75)
  })

  it('throws on non-2xx', async () => {
    mockFetch(false, { detail: 'Server error' })
    await expect(getStatus()).rejects.toThrow('Server error')
  })
})

describe('getAdminRoll', () => {
  it('returns parsed RollState on 200', async () => {
    const payload = {
      bytes_printed: 1000,
      roll_width_mm: 57,
      roll_diameter_mm: 40,
      last_reset: '2026-05-01T00:00:00Z',
      estimated_remaining_pct: 90
    }
    mockFetch(true, payload)
    const roll = await getAdminRoll()
    expect(roll.bytes_printed).toBe(1000)
    expect(roll.roll_width_mm).toBe(57)
  })
})

describe('postAdminRoll', () => {
  it('resolves on success', async () => {
    mockFetch(true, { success: true })
    await expect(postAdminRoll(57, 40)).resolves.toBeUndefined()
  })

  it('throws on error', async () => {
    mockFetch(false, { detail: 'Validation error' })
    await expect(postAdminRoll(0, 0)).rejects.toThrow('Validation error')
  })
})
