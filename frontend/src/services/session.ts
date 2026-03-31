import api from './api'
import { SessionCreate, SessionDetail, SessionResponse } from '../types/session'

export const sessionService = {
  async create(data: SessionCreate): Promise<SessionResponse> {
    const response = await api.post('/sessions', data)
    return response.data
  },

  async get(sessionId: string): Promise<SessionDetail> {
    const response = await api.get(`/sessions/${sessionId}`)
    return response.data
  },

  async update(sessionId: string, data: Partial<SessionCreate>): Promise<SessionDetail> {
    const response = await api.put(`/sessions/${sessionId}`, data)
    return response.data
  },

  async list(skip: number = 0, limit: number = 20): Promise<SessionResponse[]> {
    const response = await api.get('/sessions', { params: { skip, limit } })
    return response.data
  }
}
