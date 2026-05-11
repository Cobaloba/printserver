import { getStatus } from './api'
import { printerStatus, OFFLINE_STATUS } from './stores'

let intervalId: ReturnType<typeof setInterval> | null = null

export function startPolling(): void {
  if (intervalId !== null) return
  // Immediate first call so UI reflects real status on mount
  getStatus().then(s => printerStatus.set(s)).catch(() => printerStatus.set(OFFLINE_STATUS))
  intervalId = setInterval(async () => {
    try {
      const status = await getStatus()
      printerStatus.set(status)
    } catch {
      printerStatus.set(OFFLINE_STATUS)
    }
  }, 5000)
}

export function stopPolling(): void {
  if (intervalId !== null) {
    clearInterval(intervalId)
    intervalId = null
  }
}
