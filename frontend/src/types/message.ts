export interface MessageCreate {
  session_id: string
  content: string
  file_url?: string
}

export interface MessageResponse {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  stage: number
  created_at: string
  metadata?: any
}

export interface FileUploadResponse {
  file_id: string
  filename: string
  content: string
  message: string
}
