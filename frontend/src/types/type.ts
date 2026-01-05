export type ThinkingStatus = 'start' | 'thinking' | 'end' | 'error'

// 後端返回的 status type
export type StatusType = 'idle' | 'working' | 'error' | 'success'

export interface IMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  thinkingStatus?: ThinkingStatus
  isStreaming?: boolean // 標記是否為流式響應中的消息（歷史消息不顯示 Thinking）
  statusContent?: string // 單獨存儲 status 的 content，用於 Thinking 組件顯示
  suggestions?: string[] // 推薦問題列表（由後端返回）
}

export interface IChatbotProps {
  title?: string
  placeholder?: string
  position?: {
    bottom?: string
    right?: string
    left?: string
  }
  apiEndpoint?: string
  apiKey?: string
  token?: string
  tokenHeaderName?: string
  width?: string
  height?: string
  primaryColor?: string | { from: string; to: string }
  avatarUrl?: string
}

export type AttachmentType = 'media' | 'code-file' | 'code-folder'

export interface IAttachmentPayload {
  type: AttachmentType
  files: File[]
}
