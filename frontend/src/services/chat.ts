import api from './api'
import { MessageCreate, MessageResponse, FileUploadResponse } from '../types/message'

export const chatService = {
  async send(data: MessageCreate): Promise<MessageResponse> {
    const response = await api.post('/chat/send', data)
    return response.data
  },

  async getHistory(sessionId: string, limit: number = 50): Promise<MessageResponse[]> {
    const response = await api.get(`/chat/history/${sessionId}`, { params: { limit } })
    return response.data
  },

  async uploadFile(file: File, sessionId?: string): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (sessionId) {
      formData.append('session_id', sessionId)
    }
    
    const response = await api.post('/chat/upload', formData)
    return response.data
  }
}
