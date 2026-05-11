import type { PrinterStatus, RollState, FontSize } from './types'

async function request(url: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(url, { signal: AbortSignal.timeout(8000), ...init })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail ?? 'Request failed')
  }
  return res
}

export async function getStatus(): Promise<PrinterStatus> {
  const res = await request('/api/v1/status')
  return res.json()
}

export async function getAdminRoll(): Promise<RollState> {
  const res = await request('/api/v1/admin/roll')
  return res.json()
}

export async function postAdminRoll(width_mm: number, diameter_mm: number): Promise<void> {
  await request('/api/v1/admin/roll', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ width_mm, diameter_mm })
  })
}

export async function printTodo(title: string, items: string[]): Promise<void> {
  await request('/api/v1/print/todo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, items })
  })
}

export interface ReceiptParams {
  store: string
  items: Array<{ name: string; price: number }>
  address: string | null
  phone: string | null
  tax_pct: number
}

export async function printReceipt(params: ReceiptParams): Promise<void> {
  await request('/api/v1/print/receipt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  })
}

export async function printFreeText(text: string, font_size: FontSize): Promise<void> {
  await request('/api/v1/print/free-text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, font_size })
  })
}

export async function printQr(url: string): Promise<void> {
  await request('/api/v1/print/qr', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  })
}

export async function printGoatse(): Promise<void> {
  await request('/api/v1/print/goatse', { method: 'POST' })
}
