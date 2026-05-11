import { getStatus } from './api'
import { printerStatus } from './stores'
import type { PrinterStatus } from './types'

const OFFLINE: PrinterStatus = {
  printer_online: false,
  paper_near_end: false,
  paper_out: false,
  estimated_remaining_pct: 0
}

let intervalId: ReturnType<typeof setInterval> | null = null

export function startPolling(): void {
  if (intervalId !== null) return
  intervalId = setInterval(async () => {
    try {
      const status = await getStatus()
      printerStatus.set(status)
    } catch {
      printerStatus.set(OFFLINE)
    }
  }, 5000)
}

export function stopPolling(): void {
  if (intervalId !== null) {
    clearInterval(intervalId)
    intervalId = null
  }
}
