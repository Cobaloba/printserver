import { writable } from 'svelte/store'
import type { PrinterStatus, RollState } from './types'

export const OFFLINE_STATUS: PrinterStatus = {
  printer_online: false,
  paper_near_end: false,
  paper_out: false,
  estimated_remaining_pct: 0
}

export const printerStatus = writable<PrinterStatus>(OFFLINE_STATUS)
export const rollState = writable<RollState | null>(null)
