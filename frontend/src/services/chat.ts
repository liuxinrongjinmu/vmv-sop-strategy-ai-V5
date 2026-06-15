import api from './api'
import { API_KEY_STORAGE } from './api'
import { MessageCreate, MessageResponse, FileUploadResponse } from '../types/message'

export interface StreamEvent {
  type: 'text' | 'report' | 'stage' | 'meta' | 'error'
  content?: string
  stage?: number
  sources?: string[]
}

export const chatService = {
  async send(data: MessageCreate): Promise<MessageResponse> {
    const response = await api.post('/chat/send', data)
    return response.data
  },

  /**
   * SSE流式发送消息
   * @param data 消息数据
   * @param onEvent 收到事件时的回调
   * @param onDone 流完成时的回调
   * @param onError 出错时的回调
   */
  async sendStream(
    data: MessageCreate,
    onEvent: (event: StreamEvent) => void,
    onDone: () => void,
    onError: (error: string) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const baseURL = api.defaults.baseURL || '/api'
    const apiKey = localStorage.getItem(API_KEY_STORAGE) || import.meta.env.VITE_API_KEY || ''

    try {
      const response = await fetch(`${baseURL}/chat/send/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey ? { 'X-API-Key': apiKey } : {}),
        },
        body: JSON.stringify({
          session_id: data.session_id,
          content: data.content
        }),
        signal,
      })

      if (!response.ok) {
        onError(`服务器错误: ${response.status}`)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        onError('无法读取服务器响应')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''  // 保留最后不完整的行
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6)
            if (jsonStr === '[DONE]') {
              onDone()
              return
            }
            try {
              const event = JSON.parse(jsonStr) as StreamEvent
              onEvent(event)
            } catch {
              // 跳过无法解析的行
            }
          }
        }
      }
      onDone()
    } catch (error) {
      onError('网络连接失败，请检查网络后重试')
    }
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
