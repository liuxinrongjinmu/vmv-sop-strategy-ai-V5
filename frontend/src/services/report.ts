import api from './api'
import { ReportCreate, ReportResponse } from '../types/report'

export const reportService = {
  async generate(data: ReportCreate): Promise<ReportResponse> {
    const response = await api.post('/report/generate', data)
    return response.data
  },

  async get(reportId: number): Promise<ReportResponse> {
    const response = await api.get(`/report/${reportId}`)
    return response.data
  },

  getExportUrl(reportId: number, format: 'md' | 'pdf' | 'docx'): string {
    return `/api/report/${reportId}/export?format=${format}`
  }
}
