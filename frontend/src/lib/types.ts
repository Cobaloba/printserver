export interface PrinterStatus {
  printer_online: boolean
  paper_near_end: boolean
  paper_out: boolean
  estimated_remaining_pct: number
}

export interface RollState {
  bytes_printed: number
  roll_width_mm: number
  roll_diameter_mm: number
  last_reset: string
  estimated_remaining_pct: number
}

export type FontSize = 'small' | 'medium' | 'large'

export interface BotMessage {
  timestamp: string
  sender_name: string
  sender_id: number
  text: string
  status: 'printed' | 'help' | 'error' | 'not_allowed'
}
