import api from './api'
import { ReportCreate, ReportResponse } from '../types/report'

export const reportService = {
  async generate(data: ReportCreate): Promise<ReportResponse> {
    const startResponse = await api.post('/report/generate', data)
    const taskId = startResponse.data.task_id
    
    if (!taskId) {
      throw new Error('未获取到任务ID')
    }
    
    const maxAttempts = 120
    const interval = 3000
    
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise(resolve => setTimeout(resolve, interval))
      
      try {
        const statusResponse = await api.get(`/report/task/${taskId}`)
        const status = statusResponse.data
        
        if (status.status === 'completed' && status.report) {
          return {
            id: status.report.id,
            title: status.report.title,
            content: status.report.content,
            sources: status.report.sources,
            created_at: status.report.created_at
          }
        }
        
        if (status.status === 'failed') {
          throw new Error(status.message || '报告生成失败')
        }
      } catch (error: any) {
        if (error.message && error.message !== '报告生成失败') {
          continue
        }
        throw error
      }
    }
    
    throw new Error('报告生成超时，请稍后重试')
  },

  async get(reportId: number): Promise<ReportResponse> {
    const response = await api.get(`/report/${reportId}`)
    return response.data
  },

  getExportUrl(reportId: number, format: 'md' | 'pdf' | 'docx'): string {
    const baseURL = import.meta.env.VITE_API_URL 
      ? `${import.meta.env.VITE_API_URL}/api`
      : '/api'
    return `${baseURL}/report/${reportId}/export?format=${format}`
  }
}
